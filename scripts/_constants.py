STREAM_SYMBOL_MAP = {"SPX": "SPY", "SPXW": "SPY", "RUT": "IWM", "RUTW": "IWM", "NDX": "QQQ", "NDXP": "QQQ"}

INDEX_SYMBOLS = {"SPX", "SPXW", "RUT", "RUTW", "NDX", "NDXP", "VIX", "VIXW"}

# Schwab OAuth quote symbols for the index-level spots.  The plain "$SPX"
# form is what both the quote and option-chain endpoints accept; the
# "$SPX:X" suffix is NOT a valid OAuth symbol and is rejected as
# errors.invalidSymbols.
INDEX_QUOTE_MAP = {"SPX": "$SPX", "SPXW": "$SPX",
                    "RUT": "$RUT", "RUTW": "$RUT",
                    "NDX": "$NDX", "NDXP": "$NDX",
                    "VIX": "$VIX", "VIXW": "$VIX"}

# Max number of 1-second OHLCV bars retained in the streaming DataFrames.
MAX_BAR_ROWS = 200

# --- Flow / Order-Flow constants ---
TICKER_RETRY_COUNT = 3
FLOW_RATIO_GREEN_THRESHOLD = 0.2
FLOW_RATIO_RED_THRESHOLD = 0.8
ATM_SUBSCRIBE_BACKOFF_BASE = 0.5
ATM_SUBSCRIBE_BACKOFF_RANGE = 1.0
FLOW_WATCHDOG_STALE_SECONDS = 60

# --- Streaming constants ---
STREAM_RECONNECT_DELAY = 2
STREAM_RETRY_DELAY = 3
STREAM_RETRY_BACKOFF = 2

# --- Polling constants ---
INDEX_SPOT_MAX_RETRIES = 3
INDEX_SPOT_RETRY_BACKOFF = 1.0
INDEX_SPOT_UNEXPECTED_BACKOFF_MULTIPLIER = 5

# --- Chart constants ---
# (PANE_H_DEFAULT, GAP, AXIS_W, NUM_TICKS, VPVR_* mirror these in chart JS)