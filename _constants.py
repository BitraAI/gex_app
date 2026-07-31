STREAM_SYMBOL_MAP = {"SPX": "SPY", "SPXW": "SPY", "RUT": "IWM", "RUTW": "IWM", "NDX": "QQQ", "NDXP": "QQQ"}

INDEX_SYMBOLS = {"SPX", "SPXW", "RUT", "RUTW", "NDX", "NDXP", "VIX", "VIXW"}

INDEX_QUOTE_MAP = {"SPX": "$SPX:X", "SPXW": "$SPX:X",
                    "RUT": "$RUT:X", "RUTW": "$RUT:X",
                    "NDX": "$NDX:X", "NDXP": "$NDX:X",
                    "VIX": "$VIX:X", "VIXW": "$VIX:X"}

# Max number of 1-second OHLCV bars retained in the streaming DataFrames.
MAX_BAR_ROWS = 200