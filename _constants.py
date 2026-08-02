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