"""get_candles — OHLCV bars from the Schwab price-history API (parquet cache)."""

from schwab_mcp.core import _err, _get_client, _ok, _schwab_sem, server


@server.tool()
async def get_candles(symbol: str = "SPY", timeframe: str = "1m", bars: int = 30) -> str:
    """OHLCV bars from Schwab price history (with parquet cache).

    symbol: e.g. SPY, NVDA. timeframe: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w.
    bars: most recent N bars to return.
    """
    try:
        from client import fetch_candles_smart
        allowed = {"1m", "2m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "233t"}
        if timeframe not in allowed:
            return _err(f"timeframe must be one of {sorted(allowed)}")
        async with _schwab_sem:
            df = await fetch_candles_smart(await _get_client(), symbol, timeframe)
        if df is None or df.empty:
            return _err("no candle data")
        tail = df.tail(max(1, min(int(bars), 500)))
        out = []
        for _, row in tail.iterrows():
            dt = row.get("datetime")
            ts = int(dt) if dt is not None else None
            out.append({
                "time_utc": __import__("datetime").datetime.utcfromtimestamp(ts / 1000 if ts > 1e12 else ts).isoformat() + "Z",
                "open": float(row["open"]), "high": float(row["high"]),
                "low": float(row["low"]), "close": float(row["close"]),
                "volume": int(row["volume"]) if row.get("volume") is not None else None,
            })
        return _ok({"symbol": symbol, "timeframe": timeframe, "bars": out})
    except Exception as e:
        return _err(f"get_candles failed: {type(e).__name__}: {e}")
