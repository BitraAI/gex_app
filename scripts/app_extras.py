"""Unusual-trades scanner + Live News tab extracted verbatim from app.py, then
upgraded: last-price side inference, parallel cached scanning, auto-refresh
with since-last-scan tracking, earnings/roll flags, live ATM print/sweep feed
from the option stream, and an optional Telegram digest for new flags."""
import asyncio
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime

import pandas as pd
import streamlit as st

from scripts import telegram_notifier
from scripts.calculations import parse_option_chain, build_greeks_lookup
from scripts.client import fetch_option_chain, get_next_earnings_date
from scripts.flow import _ensure_async_loop, run_async, is_market_open, ensure_atm_streaming
from scripts._constants import STREAM_SYMBOL_MAP
from scripts.option_streaming_service import _normalize_display_symbol
from scripts.app_data import init_client
from scripts.app_tables import _render_styled_dataframe
from scripts._utils import format_expiration

# Scan tuning: chain snapshot cache TTL (re-scans inside the TTL reuse the
# cached chains — no new REST traffic), fragment auto-refresh cadence, the
# stagger between concurrent chain fetches, and the fetch-parallelism cap.
_UW_CHAIN_CACHE_TTL = 90.0
_UW_REFRESH_SECONDS = 90
_UW_FETCH_STAGGER = 0.2          # seconds between submitting chain fetches
_UW_FETCH_WORKERS = 4            # concurrent chain fetches (Schwab budget)
_UW_LIVE_WINDOW = 300.0          # live print feed window (5 min, matching
                                 # _SWEEP_WINDOW in option_streaming_service)


@st.fragment(run_every=60)
def render_news_frag():
    """Render the Live News tab — headlines from Yahoo Finance RSS for
    all tracked tickers.  The fragment auto-refreshes every 60 s to pick
    up newly polled articles."""
    s = st.session_state
    news_svc = s.get("news_service")
    if news_svc is None or not news_svc.is_running:
        st.info("News service not initialized.")
        return

    tickers = s.get("ticker_history", [])
    if not tickers:
        st.info("No tickers tracked yet.")
        return

    # Force a poll on first render so there is something to show
    if s.get("_news_first_poll", True):
        s["_news_first_poll"] = False
        loop = _ensure_async_loop()
        asyncio.run_coroutine_threadsafe(news_svc.poll(tickers), loop)

    news = news_svc.get_all_news()

    if not news:
        st.caption("No news headlines yet — next poll in ~5 min.")
        return

    st.markdown(
        f"<div style='margin-bottom:8px;color:gray;font-size:0.85rem'>"
        f"{len(news)} recent headlines"
        f"</div>",
        unsafe_allow_html=True,
    )

    for item in news:
        title = item.get("title", "")
        link = item.get("link", "")
        published = item.get("published", "")
        st.markdown(
            f"[{title}]({link})  "
            f"<span style='color:gray;font-size:0.8rem'>{published}</span>",
            unsafe_allow_html=True,
        )


def _infer_uw_side(bid: float, ask: float, traded: float) -> str:
    """Infer the aggressor side (ASK/BID/MID) from the *last trade price*
    position within the bid-ask spread.

    Trading at/near the ask means a buyer lifted the offer (demand);
    at/near the bid means a seller hit the bid (supply); a print at the
    midpoint (or a missing/out-of-range price) is uninformative -> MID.
    The caller passes the chain's ``last`` price when the session has one
    (what actually traded) and falls back to ``mark`` otherwise — the mark
    is a mid-of-spread theoretical value, so chains without a last price
    de-grade to MID-heavy inference, which is honest rather than noisy.
    """
    if bid <= 0 or ask <= 0 or ask <= bid or traded <= 0:
        return "MID"
    if traded >= ask:
        return "ASK"
    if traded <= bid:
        return "BID"
    mid = (bid + ask) / 2
    half = (ask - bid) / 2
    frac = (traded - mid) / half if half > 0 else 0.0
    if frac >= 0.3:
        return "ASK"
    if frac <= -0.3:
        return "BID"
    return "MID"


def _uw_fetch_chain(symbol: str, client) -> dict | None:
    """Lean chain fetch for the Unusual Trades scan.

    Unlike the main pipeline (``_fetch_option_chain_core``) this skips the
    risk-free-rate / dividend-yield quote calls — the scan's premium and
    Vol/OI math does not use them — which roughly halves REST calls per
    ticker and keeps the parallel scan well inside Schwab's request budget.
    Mirrors the index-symbol ETF-proxy fallback so $SPX/$SPXW/$RUT/$NDX
    still scan (against the proxy chain, exactly like the main pipeline).

    Runs inside a worker thread: it touches no streamlit session state —
    ``client`` is pre-resolved by the caller.  Returns None when the chain
    could not be fetched for any reason.
    """
    sym = _normalize_display_symbol(symbol)
    stream_sym = STREAM_SYMBOL_MAP.get(sym)
    raw = None
    try:
        raw = run_async(fetch_option_chain(client, symbol, strike_count=75,
                                           include_quotes=True))
    except Exception:
        raw = None

    data, spot = [], 0.0
    if isinstance(raw, dict) and raw.get("errors"):
        raw = None
    if raw is not None:
        try:
            data, spot = parse_option_chain(raw)
        except Exception:
            data, spot = [], 0.0

    if (not data or spot <= 0) and stream_sym:
        # Index (or failed) fetches fall back to the ETF proxy chain; the
        # proxy's own volume/OI backfills missing per-contract fields.
        try:
            fb_raw = run_async(fetch_option_chain(client, stream_sym,
                                                  strike_count=75,
                                                  include_quotes=True))
            data, spot = parse_option_chain(fb_raw,
                                            fallback_greeks=build_greeks_lookup(fb_raw))
        except Exception:
            pass

    if not data or spot <= 0:
        return None
    return {"sym": sym, "data": data, "spot": spot}


def _uw_earnings_flags(syms: set[str]) -> dict[str, str | None]:
    """Next earnings date per symbol, fetched once per symbol per day
    (session-cached).  Values are ``YYYY-MM-DD`` strings or None."""
    s = st.session_state
    cache = s.setdefault("_uw_earnings", {})
    today_iso = date.today().isoformat()
    client = st.session_state.client
    for sym in syms:
        ent = cache.get(sym)
        if ent and ent[0] == today_iso:
            continue
        try:
            val = run_async(get_next_earnings_date(client, sym))
        except Exception:
            val = None
        cache[sym] = (today_iso, val)
    return {sym: cache[sym][1] for sym in syms}


def _run_uw_scan(
    tickers: list[str],
    *,
    min_vol: int,
    min_ratio: float,
    min_premium: float,
    max_dte: int,
    otm_only: bool,
) -> tuple[pd.DataFrame, list[dict], bool]:
    """Scan every *tickers* chain for unusual blocks and return
    ``(results_df, digest_rows, first_scan)``.

    - Chains are fetched concurrently (capped) and cached per symbol for
      ``_UW_CHAIN_CACHE_TTL`` seconds, so tweaking filters inside the TTL
      costs zero REST calls.
    - ``NEW`` highlights contracts flagged now that were not flagged in the
      previous scan of the same trading day, and ``Vol Δ`` is today's
      session volume growth per contract since the first time it was seen
      by a scan.
    - ``Roll?`` marks the same strike/type flagged across 2+ expirations
      (fresh positioning trades like a roll rather than an outright bet).
    - ``Earnings`` marks rows whose expiration window includes the
      symbol's next earnings date.
    - ``first_scan`` is True when this scan established the session
      baseline (no NEW flags, no digest).
    """
    s = st.session_state
    if not init_client():
        return pd.DataFrame(), [], False
    client = s.client

    # Daily reset: session volume and flagged-set baselines are per day.
    today_iso = date.today().isoformat()
    if s.get("_uw_scan_date") != today_iso:
        s["_uw_scan_date"] = today_iso
        s["_uw_vol_seen"] = {}
        s["_uw_prev_flagged"] = None
    vol_seen = s.setdefault("_uw_vol_seen", {})
    prev_flagged = s.get("_uw_prev_flagged")
    first_scan = prev_flagged is None

    # --- fetch (or reuse cached) chains --------------------------------
    cache = s.setdefault("_uw_chain_cache", {})
    now = time.time()
    chains: dict[str, dict] = {}
    to_fetch = []
    for t in tickers:
        ent = cache.get(t)
        if ent and now - ent[0] <= _UW_CHAIN_CACHE_TTL:
            chains[t] = ent[1]
        else:
            to_fetch.append(t)
    if to_fetch:
        with ThreadPoolExecutor(max_workers=min(_UW_FETCH_WORKERS, len(to_fetch))) as pool:
            futs: dict[object, str] = {}
            for i, t in enumerate(to_fetch):
                if i:
                    time.sleep(_UW_FETCH_STAGGER)
                futs[pool.submit(_uw_fetch_chain, t, client)] = t
            for fut in as_completed(futs):
                t = futs[fut]
                try:
                    chain = fut.result()
                except Exception:
                    chain = None
                if chain:
                    cache[t] = (time.time(), chain)
                    chains[t] = chain

    # --- pass 1: collect eligible rows ----------------------------------
    elig: list[dict] = []
    for t in tickers:
        chain = chains.get(t)
        if not chain:
            continue
        data, spot = chain["data"], chain["spot"]
        for opt in data:
            volume = int(opt.get("volume", 0) or 0)
            if volume < min_vol:
                continue
            dte = int(opt.get("days_to_exp", 0) or 0)
            if dte <= 0 or dte > max_dte:
                continue
            oi = int(opt.get("open_interest", 0) or 0)
            ratio = volume / oi if oi > 0 else float("inf")
            if oi > 0 and ratio < min_ratio:
                continue
            last = float(opt.get("last", 0) or 0)
            mark = float(opt.get("mark", 0) or 0)
            traded = last if last > 0 else mark
            premium = traded * volume * 100
            if premium < min_premium:
                continue
            if otm_only:
                if opt["type"] == "CALL" and opt["strike"] <= spot:
                    continue
                if opt["type"] == "PUT" and opt["strike"] >= spot:
                    continue

            row = {
                "key": f"{chain['sym']}|{opt['type']}|{opt['strike']:g}|{opt['expiration']}",
                "Ticker": chain["sym"],
                "Type": opt["type"],
                "Side": _infer_uw_side(
                    float(opt.get("bid", 0) or 0),
                    float(opt.get("ask", 0) or 0),
                    traded,
                ),
                "Strike": opt["strike"],
                "Expiration": opt["expiration"],
                "DTE": dte,
                "Volume": volume,
                "OI": oi,
                "Vol/OI": ratio if oi > 0 else None,
                "Last": traded,
                "Mark": mark,
                "Premium": premium,
                "IV": opt.get("iv", 0) or 0,
                "Delta": opt.get("delta", 0) or 0,
                "Spot": spot,
            }
            elig.append(row)

    # --- enrichments: volume delta, roll detection, earnings ------------
    counts = Counter((e["Ticker"], e["Type"], e["Strike"]) for e in elig)
    earnings = {}
    if elig:
        earnings = _uw_earnings_flags({e["Ticker"] for e in elig})

    rows = []
    new_rows = []
    for row in elig:
        key = row["key"]
        flags = []

        prev_vol = vol_seen.get(key)
        if prev_vol is not None and row["Volume"] >= prev_vol:
            row["Vol Δ"] = row["Volume"] - prev_vol
        else:
            row["Vol Δ"] = None

        if not first_scan and key not in prev_flagged:
            flags.append("NEW")
            new_rows.append(row)
        if counts[(row["Ticker"], row["Type"], row["Strike"])] > 1:
            flags.append("ROLL?")
        ed = earnings.get(row["Ticker"])
        if ed:
            try:
                if date.today() <= date.fromisoformat(ed) <= date.fromisoformat(row["Expiration"]):
                    flags.append("EARN")
            except ValueError:
                pass
        row["Flags"] = " · ".join(flags)
        rows.append(row)
        vol_seen[key] = row["Volume"]

    s["_uw_prev_flagged"] = {row["key"] for row in elig}

    if rows:
        df = pd.DataFrame(rows).sort_values("Premium", ascending=False).reset_index(drop=True)
    else:
        df = pd.DataFrame()
    return df, new_rows, first_scan


def _uw_digest_text(new_rows: list[dict], digest_min: float) -> str | None:
    """Build the Telegram digest for genuinely NEW flagged contracts whose
    premium clears *digest_min*.  Returns None when nothing qualifies."""
    rows = [r for r in new_rows if r["Premium"] >= digest_min]
    if not rows:
        return None
    rows.sort(key=lambda r: -r["Premium"])
    lines = [f"<b>Unusual trade flags — {len(rows)} new</b>"]
    for r in rows[:10]:
        cp = "C" if r["Type"] == "CALL" else "P"
        emoji = "🟢" if cp == "C" else "🔴"
        oi_part = f"{r['Vol/OI']:.1f}x OI" if r["Vol/OI"] is not None else "no OI"
        premium = r["Premium"]
        ptxt = f"${premium / 1e6:.2f}M" if premium >= 1e6 else f"${premium / 1e3:.0f}k"
        vold = r.get("Vol Δ")
        vold_txt = f" · +{vold:,} since first seen" if isinstance(vold, int) and vold > 0 else ""
        lines.append(
            f"{emoji} <b>{r['Ticker']}</b> {r['Expiration'][5:]} {r['Strike']:g}{cp}"
            f" · {r['Volume']:,} vol · {oi_part} · {ptxt} @ {r['Side']}"
            f" · Δ{r['Delta']:.2f}{vold_txt}"
        )
    if len(rows) > 10:
        lines.append(f"…and {len(rows) - 10} more")
    return "\n".join(lines)


def render_unusual_trades():
    """Unusual Trades scanner tab.

    Scans every tracked ticker (or just the current one) for "unusual"
    options blocks: outsized volume relative to open interest (fresh
    positioning rather than churn) or extreme traded premium.  Chains are
    fetched in parallel and cached for ~90 s; the fragment auto-refreshes
    during market hours so NEW flags, a live ATM print/sweep feed and an
    optional Telegram digest stay current hands-free.
    """
    s = st.session_state

    st.subheader("Unusual Trades Scanner")

    with st.expander("How to read this scanner", expanded=False):
        st.markdown(
            "Each row is a single option contract flagged by the scanner. "
            "**Vol/OI** is today's volume divided by open interest &mdash; a "
            "ratio above 1.0 means more contracts traded today than are open, "
            "a classic sign of fresh position building (unusual flow) rather "
            "than churn of existing contracts. **Premium** is "
            "`last x volume x 100` (the theoretical mark when no last trade "
            "exists) &mdash; the estimated money traded. "
            "**Side** infers the aggressor from the last price sitting at the "
            "bid or ask; chains with no last trade read MID. "
            "**Flags**: <b>NEW</b> = flagged now, wasn't in the previous scan "
            "&middot; <b>VOL Δ</b> = volume added since this contract first "
            "appeared in a scan &middot; <b>ROLL?</b> = same strike/type "
            "flagged across 2+ expirations (looks like a roll, not an "
            "outright bet) &middot; <b>EARN</b> = the expiration window "
            "covers the symbol's next earnings date. Below the snapshot "
            "scan, **Live ATM prints** surfaces recent large prints and "
            "sweep proxies straight from the option tick stream."
        )

    scope = st.radio(
        "Scope",
        ["All tracked tickers", "Current ticker only"],
        horizontal=True,
        key="uw_scope",
    )
    if scope == "All tracked tickers":
        tickers = list(s.get("ticker_history", []))
    else:
        tickers = [s.get("symbol", "")] if s.get("symbol") else []
    if not tickers:
        st.info("No tickers to scan — add tickers on the main page first.")
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        min_vol = st.number_input("Min Volume", min_value=1, value=1000, step=100, key="uw_min_vol")
    with c2:
        min_ratio = st.number_input("Min Vol/OI", min_value=0.1, value=1.0, step=0.1, key="uw_min_ratio")
    with c3:
        min_premium = st.number_input("Min Premium ($)", min_value=0, value=100000, step=10000, key="uw_min_premium")
    with c4:
        max_dte = st.number_input("Max DTE", min_value=1, value=3, step=1, key="uw_max_dte")

    otm_only = st.checkbox(
        "Show OTM only (strikes beyond spot)",
        value=True,
        key="uw_otm_only",
    )

    # Telegram digest for genuinely NEW bars.  Every available call to the
    # notifier suppresses itself outside market hours, like the other
    # alert paths documented in TELEGRAM.md.
    with st.expander("Telegram digest", expanded=False):
        tg_on = st.toggle(
            "Push NEW flags to Telegram",
            value=True,
            key="uw_tg_on",
            help="Only genuinely NEW flags whose premium clears the "
                 "digest threshold are pushed, once per scan. Suppressed "
                 "outside market hours.",
        )
        digest_min = st.number_input(
            "Min digest premium ($)", min_value=0, value=250000, step=50000,
            key="uw_digest_min",
        )
        st.caption(
            "Digests piggyback on an open dashboard (auto-scan below), like "
            "the other Telegram alert paths."
        )

    auto = st.toggle(
        f"Auto-scan every {_UW_REFRESH_SECONDS:.0f} s (market hours only)",
        value=True,
        key="uw_auto",
    )
    run = st.button("Run scan now", type="primary", key="run_uw_scan")

    last_t = s.get("_uw_last_scan_time", 0)
    stale = (time.time() - last_t) > (_UW_CHAIN_CACHE_TTL - 2)
    should_scan = run or (
        auto and is_market_open() and stale
    )

    if should_scan:
        s["_uw_last_scan_time"] = time.time()
        with st.spinner(f"Scanning {len(tickers)} ticker(s)..."):
            df, new_rows, first_scan = _run_uw_scan(
                tickers,
                min_vol=int(min_vol),
                min_ratio=float(min_ratio),
                min_premium=float(min_premium),
                max_dte=int(max_dte),
                otm_only=otm_only,
            )
            s["uw_results"] = df
            s["_uw_last_scan_error"] = None
        if tg_on and not first_scan and is_market_open():
            text = _uw_digest_text(new_rows, float(digest_min))
            if text:
                ok = telegram_notifier.send_telegram(text)
                s["_uw_last_digest"] = (
                    "sent" if ok else "send failed (check config.toml [telegram])"
                )
            else:
                s["_uw_last_digest"] = None

    results_df = s.get("uw_results")
    if results_df is None or results_df.empty:
        st.info("Set your filters and click **Run scan** to surface unusual options activity.")
    else:
        _total_premium = float(results_df["Premium"].sum())
        _calls = int((results_df["Type"] == "CALL").sum())
        _puts = int((results_df["Type"] == "PUT").sum())
        _new = 0
        if "Flags" in results_df.columns:
            _new = int(results_df["Flags"].str.contains("NEW", na=False).sum())

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Flagged contracts", len(results_df))
        m2.metric("Total premium", f"${_total_premium:,.0f}")
        m3.metric("Tickers", results_df["Ticker"].nunique())
        m4.metric("Calls / Puts", f"{_calls} / {_puts}")
        m5.metric("New since last scan", _new)

        _scan_time = s.get("_uw_last_scan_time", 0)
        status_bits = [f"Last scan {datetime.fromtimestamp(_scan_time).strftime('%H:%M:%S')}"
                       if _scan_time else "No scan yet"]
        if s.get("_uw_last_digest"):
            status_bits.append(f"Telegram: {s['_uw_last_digest']}")
        if not is_market_open():
            status_bits.append("Market closed — auto-scan paused")
        st.caption(" · ".join(status_bits))

        df = results_df.head(3000).copy()
        df["Expiration"] = df["Expiration"].map(format_expiration)

        def _row_style(row):
            is_call = row["Type"] == "CALL"
            bg = "#e6f7f1" if is_call else "#fdecec"
            side = row["Side"]
            if side == "ASK":
                side_style = "color: #00cc96; font-weight: 600;"
            elif side == "BID":
                side_style = "color: #ef5350; font-weight: 600;"
            else:
                side_style = "color: #ff9800;"
            flags = row.get("Flags")
            if flags and "NEW" in flags:
                flag_style = "color: #ff9800; font-weight: 600;"
            else:
                flag_style = ""
            return [
                (side_style if col == "Side"
                 else flag_style if col == "Flags"
                 else f"background-color: {bg};")
                for col in row.index
            ]

        _fmatters = {
            "Strike": "${:,.2f}",
            "Volume": "{:,.0f}",
            "Vol Δ": lambda v: "—" if pd.isna(v) else f"{v:+,.0f}",
            "OI": "{:,.0f}",
            "Vol/OI": lambda v: "—" if pd.isna(v) else f"{v:.2f}x",
            "Last": lambda v: "—" if pd.isna(v) or v == 0 else "${:,.2f}".format(v),
            "Mark": "${:,.2f}",
            "Premium": "${:,.0f}",
            "IV": lambda v: "—" if pd.isna(v) or v == 0 else f"{(v / 100 if v > 3 else v):.0%}",
            "Delta": "{:.2f}",
            "Spot": "${:,.2f}",
            "Flags": lambda v: v if (isinstance(v, str) and v) else "",
        }
        styled = (
            df.style
            .apply(_row_style, axis=1)
            .format({k: v for k, v in _fmatters.items() if k in df.columns})
            .set_properties(**{"text-align": "right"})
        )

        _render_styled_dataframe(
            styled,
            height=460,
            column_config={
                "Type": st.column_config.TextColumn("Type", width="small"),
                "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                "Side": st.column_config.TextColumn("Side", width="small"),
                "Last": st.column_config.TextColumn("Last", width="small"),
                "Vol Δ": st.column_config.TextColumn("Vol Δ", width="small"),
                "Flags": st.column_config.TextColumn("Flags", width="small"),
            },
        )

    # ------------------------------------------------------------------
    # Live ATM prints & sweep proxy straight from the option tick stream.
    # The stream only subscribes the ATM front/second-expiration contracts
    # per tracked ticker, so this complements (never duplicates) the
    # full-chain snapshot scan above.
    # ------------------------------------------------------------------
    st.divider()
    st.markdown("#### Live ATM prints & sweep proxy (last 5 min)")
    if s.get("symbol"):
        ensure_atm_streaming(s.get("symbol"))
    live_svc = st.session_state.get("atm_option_service")
    if live_svc is None or not live_svc.is_running:
        st.caption("Live prints need the option stream — it starts automatically while this tab is open.")
        return

    live_min = st.number_input(
        "Min print premium ($)", min_value=0, value=100000, step=25000,
        key="uw_live_min_prem",
    )
    live = live_svc.get_unusual_prints(
        None, window=_UW_LIVE_WINDOW, min_premium=float(live_min),
    )

    sweeps = live.get("sweeps", [])
    if sweeps:
        sw = pd.DataFrame([{
            "Time": datetime.fromtimestamp(w["ts"]).strftime("%H:%M:%S"),
            "Ticker": w["ticker"],
            "Type": w["opt_type"],
            "Side": "BUY" if w["direction"] == "buy" else "SELL",
            "Prints": w["prints"],
            "Strikes": w["strikes"],
            "Strike list": ", ".join(f"${k:g}" for k in w["strike_list"]),
            "Total size": w["total_size"],
            "Total premium": w["total_premium"],
        } for w in sweeps])
        _render_styled_dataframe(
            sw.style.format({"Total size": "{:,.0f}", "Total premium": "${:,.0f}"}),
            height=200,
        )
        st.caption("A sweep = 3+ consecutive same-side prints on one type "
                   "within ~10 s gaps across 2+ strikes (streams cover the "
                   "ATM front/second expiry per ticker).")
    else:
        st.caption("No sweep-proxy clusters detected in the window.")

    print_rows = live.get("prints", [])
    if print_rows:
        pr = pd.DataFrame([{
            "Time": datetime.fromtimestamp(p["ts"]).strftime("%H:%M:%S"),
            "Ticker": p["ticker"],
            "Type": p["opt_type"],
            "Strike": p["strike"],
            "Exp": str(p["exp"]),
            "Size": p["size"],
            "Price": p["price"],
            "Side": ("ASK" if p["direction"] == "buy"
                     else "BID" if p["direction"] == "sell" else "MID"),
            "Premium": p["premium"],
        } for p in print_rows])
        _render_styled_dataframe(
            pr.style.format({
                "Strike": "${:,.2f}",
                "Size": "{:,.0f}",
                "Price": "${:,.2f}",
                "Premium": "${:,.0f}",
            }),
            height=250,
        )
    else:
        st.caption("No qualifying prints in the window.")
