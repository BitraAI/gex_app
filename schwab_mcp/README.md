# schwab_mcp — MCP Server for gex_app

Read-only [Model Context Protocol](https://modelcontextprotocol.io) server that
exposes the repo's market-data and Schwab-account capabilities as tools for AI
agents (registered globally with OpenCode as **`gex_app`**).

All data comes directly from the **Schwab Trader API** via the official
`schwab-py` SDK; all analytics are computed locally with the exact same
pipeline the Streamlit app uses (`client.py` → `calculations.py` →
`analytics.py`). The MCP layer is purely an exposure/adapter layer.
All data tools are **READ-ONLY**. The only trading tools are the equity
order tools (`place_buy_order`, `place_sell_order`, `cancel_order`,
`replace_order`), and places/replaces are **code-gated three-step**:
preview (`confirm=false`) returns the exact spec plus a `confirmation_code`
and submits nothing → the agent presents both to the user and waits for an
explicit approval (OpenCode also prompts on catalog-path calls) → only a
`confirm=true` call that echoes the unchanged code executes at Schwab.
`cancel_order` previews live state and executes without the code gate.

---

## Tools

| Tool | Arguments | Returns | Underlying code |
|---|---|---|---|
| `get_spot` | `symbols: ["SPY","QQQ"]` | Last, mark, bid/ask, net change (+ %), volume, quote time, regular/extended last | `client.fetch_quotes` |
| `get_option_chain` | `symbol`, `strike_count=50`, `max_dte=60`, `expiration="YYYY-MM-DD"` (optional) | Per-contract rows: strike, CALL/PUT, mark, bid/ask, last, volume, OI, DTE, raw greeks from the API response | `client.fetch_option_chain` |
| `get_gex_analytics` | `symbol="SPY"` | Total/net GEX, call wall, put wall, gamma flip, ATM strike, dealer position, max ±GEX strikes, largest OI/gamma strikes, expected pin, IV skew (25Δ), ATM IV, SSVI surface, per-strike band ±$5 of ATM | `fetch_option_chain` → `parse_option_chain` → `compute_analytics` (identical to the app; index symbols auto-fall back to their ETF proxy) |
| `get_candles` | `symbol="SPY"`, `timeframe="1m"`, `bars=30` | OHLCV bars (`time_utc`, o/h/l/c, volume) with parquet cache; timeframes: `1m 2m 5m 15m 30m 1h 4h 1d 1w 233t` | `client.fetch_candles_smart` |
| `get_positions` | — | Per-position symbol/description/side/qty/avg price/market value/day change + account balances (cash, market values, equity, buying power) | Direct `get_account_numbers` / `get_account(POSITIONS)` |
| `place_buy_order` | `symbol`, `quantity` (1..10000), `order_type="LIMIT"`, `limit_price`, `duration="DAY"` or `"GTC"`, `account_last4`, `confirm=false`, `confirmation_code` | **Trading.** Preview (`confirm=false`) → exact order spec, implied notional, and a `confirmation_code`; execute requires `confirm=true` **plus that code** (rejected otherwise); returns order id + live status | `equity_buy_{market,limit}` → `place_order` (code-gated) |
| `place_sell_order` | Same as `place_buy_order` | **Trading.** Sells long shares (short-selling rejected); same preview + code gate | `equity_sell_{market,limit}` → `place_order` (code-gated) |
| `cancel_order` | `order_id`, `account_last4`, `confirm=false` | **Trading.** Preview shows current order status (flags already-filled/canceled); execute sends the cancel and returns status after. Not code-gated (flattening is de-risking) | `get_order` + `cancel_order` |
| `replace_order` | `order_id`, optional `quantity`/`limit_price`/`order_type`/`duration`, `account_last4`, `confirm=false`, `confirmation_code` | **Trading.** Modifies an open order — only passed params change, rest kept from the live order; replacement issues a NEW order id; single-leg equity only; preview + code gate like the place tools | `get_order` + spec rebuild → `replace_order` (code-gated) |
| `get_market_hours` | `market="EQUITY"`, `date="YYYY-MM-DD"` (optional; today default) | Session windows (pre/regular/post, ET) per product for one market; `isOpen:false` on holidays. Markets: EQUITY, OPTION, BOND, FOREX (no INDEX in the SDK) | Direct `get_market_hours` |
| `get_movers` | `index="$SPX"` | Top movers from Schwab's screen: symbol, name, last, net change, **% change (normalized from the API's fraction)**, volume, market volume share, trades. Only populates during regular hours; screen weights market share, not raw % move. Aliases accepted (`SPX` → `$SPX`) | Direct `get_movers` |
| `get_transactions` | `days=30` (1..60, API hard limit), `account_last4` (optional) | Per-transaction date, type, description, net amount (+ = credit), status, settlement, instrument legs; plus window and net cash change summary | Direct `get_transactions` |

Conventions:

- Responses are JSON strings; errors return `{"error": "..."}` rather than
  raising, so agents get actionable text back.
- Account numbers are truncated to the last 4 digits (`****5716`).
- GEX values are in dollars of gamma exposure as computed by
  `analytics.compute_analytics` (see the app documentation for formulas).
- **Movers schema quirks are normalized inside `get_movers`**: the raw
  response's `screeners` list *is* the mover list, and `netPercentChange`
  arrives as a fraction — rows are returned with percent values.
- **Order tools are deliberately constrained**: equity only, MARKET/LIMIT
  only, DAY/GTC only, NORMAL session only, max quantity 10,000, and the
  three-step code gate described above. The `confirmation_code` is the first
  8 hex chars of SHA-256 of the canonical (sort-keys) JSON of the order spec
  — deterministic, so a preview and its confirm can be validated in separate
  sessions/processes, and drift between them always invalidates the code.
  Agents must present the preview AND its code to the user and wait for an
  explicit affirmative reply before the confirm call. OpenCode's global
  `permissions` additionally set `effect: "ask"` on place/sell/replace, so a
  HUMAN approves at the client layer on catalog-path calls.
- **`get_order` returns the order object itself at the top level** (not
  wrapped in `securitiesAccount` like `get_account`) — order-summary code
  handles both shapes; pre-activation states (`PENDING_ACTIVATION`,
  `QUEUED`, …) are cancelable and count as open.

---

## Example agent questions

Questions an agent can answer with the server, and the tool that serves each.
The order lifecycle was verified live end-to-end (place → replace → cancel)
with the code-gated confirm flow — a real user approval at every step.

| Question | Tool | Notes |
|---|---|---|
| "Get real-time quotes for AAPL, GOOGL, and MSFT" | `get_spot` | Multi-symbol batch: last/bid/ask/±change/volume |
| "Show me my Schwab account balances and positions" | `get_positions` | Account type, `****`-truncated number, balances, flat/long/short positions |
| "What are the GEX walls and dealer positioning on SPY going into expiry?" | `get_gex_analytics` | Call/put walls, gamma flip, expected pin, ATM strike, dealer position, IV skew in one call; same pipeline as the app |
| "Show me the last 15 one-minute candles for NVDA" | `get_candles` | Recent OHLCV tape from the parquet-backed price history |
| "Where is the largest open interest on TSLA between $340 and $370?" | `get_option_chain` | Filter returned rows by strike/volume/OI directly in the agent, or pass `expiration` to narrow to one expiry |
| "Check if the markets are open" | `get_market_hours` | Session windows (pre/regular/post, ET) for EQUITY/OPTION/BOND/FOREX; also answers "when does Monday open?" for any date |
| "What are today's market movers in the $SPX" | `get_movers` | Normalized ≤10 rows (symbol, name, last, % change, volume share); aliases like `SPX` work; only populates during regular hours |
| "Get my transactions from the last 30 days" | `get_transactions` | Sorted rows + net-cash-change summary; window capped at 60 days by the API |
| "Buy 1 share XLE at $35" | `place_buy_order` | Code-gated: preview shows exact spec + notional + `confirmation_code`, agent asks the user, execute only with `confirm=true` + that code; returns order id + live status |
| "Sell my 3 shares of AAPL at $50" | `place_sell_order` | Sells LONG shares only (short-selling rejected); same code-gated preview → user approval → confirm flow; MARKET or LIMIT |
| "Replace my XLE order at $30 instead" | `replace_order` | Same code gate; changes only the passed params (new order id issued); rejects orders in terminal states and multi-leg orders |
| "Cancel my XLE order" | `cancel_order` | Preview flags already-filled/canceled orders before `confirm=true` sends the cancel (no code gate — flattening is de-risking) |

Typical compound workflows that already work:

- *"What's the setup on SPY right now?"* → `get_gex_analytics` (walls, gamma
  flip, dealer position) + `get_spot` (context) + `get_candles` (tape)
- *"Work my order end-to-end"* → `place_buy_order` (preview + code → user
  approval → confirm) → `replace_order` (same gate) → `cancel_order`
  (flatten) — verified live cycles: placed 201 → replaced (new order id)
  → canceled 200

---

## Folder structure

```
schwab_mcp/
├── __init__.py      # package docstring
├── main.py          # ENTRYPOINT → imports tools, runs server (stdio)
├── core.py          # shared plumbing (see below)
└── tools/
    ├── __init__.py  # imports all tool modules (registration side effects)
    ├── spot.py          # get_spot
    ├── option_chain.py  # get_option_chain
    ├── gex_analytics.py # get_gex_analytics
    ├── candles.py       # get_candles
    ├── positions.py     # get_positions
    ├── orders.py        # place_buy_order / place_sell_order / cancel_order / replace_order
    ├── market_hours.py  # get_market_hours
    ├── movers.py        # get_movers
    └── transactions.py  # get_transactions
```

`core.py` contains everything the tools share:

| Member | Purpose |
|---|---|
| `server` | The `MCPServer` instance (mcp SDK 2.x; falls back to `FastMCP` on 1.x). All tools decorate with `@server.tool()`. |
| `_get_client()` | Thread-safe lazy singleton for the shared Schwab `AsyncClient` (double-checked lock; token auto-refresh handled by schwab-py). |
| `_schwab_sem` | `asyncio.Semaphore(4)` around every REST call — prevents bursts from tripping Schwab's throttling. |
| `_jsonable` / `_ok` / `_err` | JSON-safe conversion (numpy/pandas/Decimal → plain values) and response envelopes. |
| `_r_and_q(sym)` | Risk-free rate + dividend yield used by the analytics pipeline. |

It also bootstraps `sys.path` with the repo root so the gex_app data modules
(`client`, `analytics`, `calculations`, `_constants`) import cleanly no matter
which cwd the server starts in.

### Adding a new tool

1. Create `schwab_mcp/tools/<name>.py`:

   ```python
   """get_<name> — one-line purpose."""

   from schwab_mcp.core import _err, _get_client, _ok, _schwab_sem, server

   @server.tool()
   async def get_<name>(...) -> str:
       """Docstring shown to the agent."""
       try:
           from client import <fetcher>
           async with _schwab_sem:
               data = await <fetcher>(await _get_client(), ...)
           ...
           return _ok(result)
       except Exception as e:
           return _err(f"get_<name> failed: {type(e).__name__}: {e}")
   ```

2. Add the module to the import list in `schwab_mcp/tools/__init__.py`.
3. Restart the OpenCode session (or `opencode mcp list` to confirm reconnect).

Rules of thumb: wrap existing repo fetchers rather than calling the Schwab API
inline; always take the semaphore per API call; catch everything and return
`_err(...)`; keep tool logic independent of `st.session_state`.

---

## MCP configuration

**OpenCode registration** (global config,
`~/.config/opencode/opencode.json`):

```json
{
  "mcp": {
    "servers": {
      "gex-app": {
        "type": "local",
        "command": ["/path/to/venv/bin/python",
                    "/path/to/home/gex_app/schwab_mcp/main.py"]
      }
    }
  },
  "permissions": [
    { "action": "gex_app_place_buy_order", "resource": "*", "effect": "ask" },
    { "action": "gex_app_place_sell_order", "resource": "*", "effect": "ask" },
    { "action": "gex_app_replace_order", "resource": "*", "effect": "ask" }
  ]
}
```

- **Python**: `/path/to/venv/bin/python` (has `mcp`, `schwab-py`,
  pandas, numpy, pyarrow).
- **Transport**: stdio.
- **Auth/token**: `~/.local/share/gex_app/schwab_token.json` (same file the
  Streamlit app uses; refresh tokens don't rotate, so both can run safely
  side-by-side and tokens refresh automatically).
- **Reconnect check**: `opencode mcp list` should show
  `✓ gex-app  connected`. New tools appear in an agent's catalog on the next
  session.
- **Order confirmation is enforced at the OpenCode layer**: the global config
  carries `permissions` rules with `effect: "ask"` for the three execution
  tools — `gex_app_place_buy_order`, `gex_app_place_sell_order`,
  `gex_app_replace_order` (server name `gex-app` → action prefix `gex_app_`,
  hyphens become underscores per the permissions guide). Any agent call to
  these tools raises an approval prompt (Allow once / Allow always / Reject)
  before the call reaches the server. `cancel_order` is deliberately NOT
  gated — flattening a position/bracket is a de-risking move.
- Defense in depth on the trading path (three code-gated layers): the
  OpenCode permission prompt outside the server (catalog-path calls), the
  `confirmation_code` gate inside the tools, and the terminal-state checks
  that preview steps run against live orders. An order can only reach Schwab
  when all layers agree. Note: a raw subprocess call to `main.py` bypasses
  the OpenCode prompt by construction — the in-server code gate is what
  still holds there (it was proven live, including a refused no-code and a
  refused wrong-code confirm).

---

## Known behaviors & gotchas

- **Schwab throttling**: sustained bursts beyond ~120 req/min don't return
  429s — they return valid 200-OK responses with long delays, which look like
  hangs. The semaphore keeps MCP usage well below that; avoid adding
  scan/burst-style tools that fan out per-symbol requests without pacing.
- **schwab-py 2.x response schemas moved**:
  - Quotes: nested blocks — top level plus `quote` / `regular` / `extended` /
    `reference`. `get_spot` unwraps the `quote` block when present.
  - Option chains: the raw response often contains **no `greeks` block**;
    `get_option_chain` therefore exposes raw greeks as `null`, while
    `get_gex_analytics` gets full app-grade greeks because it runs the repo's
    `parse_option_chain` fallback-greeks pipeline.
  - Intraday extended-hours quotes only carry the last extended trade — they
    are not usable as per-session classifiers.
- **Index symbols**: SPX/RUT/NDX/VIX need `$SYMBOL` in chain requests, and
  some index chains are unavailable — `get_gex_analytics` mirrors the app's
  ETF-proxy fallback (SPY for SPX, etc.) via `_constants.STREAM_SYMBOL_MAP`.
- **Market hours windows (ET)**: equity pre-market 07:00–09:30, regular
  09:30–16:00, post-market 16:00–20:00; option post-market closes 16:15.
  Movers-style lists only populate during regular hours.
- **History limits**: transaction history goes back 60 days max
  (`get_transactions`); candle history depends on timeframe.
