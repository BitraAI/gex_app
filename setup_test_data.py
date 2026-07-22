#!/usr/bin/env python3
# Test script to simulate the bullish/bearish flow data issue
# This simulates what should happen in the actual app

import json
import os
import time

# Create the necessary directories and files
os.makedirs('~/.local/share/gex_app', exist_ok=True)

# Write ticker_history.json if it doesn't exist
ticker_history_path = os.path.expanduser('~/.local/share/gex_app/ticker_history.json')
if not os.path.exists(ticker_history_path):
    with open(ticker_history_path, 'w') as f:
        json.dump(["SPY", "AAPL", "TSLA"], f)
    print(f"Created {ticker_history_path} with test tickers")

# Write an existing Schwab token file
import json
schwab_token_path = os.path.expanduser('~/.local/share/gex_app/schwab_token.json')
if not os.path.exists(schwab_token_path):
    with open(schwab_token_path, 'w') as f:
        json.dump({
            "token": "test_token_for_simulation",
            "refresh_token": "test_refresh_token",
            "expires_at": str(int(time.time()) + 3600)
        }, f)
    print(f"Created {schwab_token_path} with test token")

print("\n=== Directory Structure ===")
os.system('find ~/.local/share/gex_app -type f -name "*"')

print("\n=== Ticker History ===")
with open(ticker_history_path, 'r') as f:
    tickers = json.load(f)
    print(f"Tickers: {tickers}")
    
print("\n=== Schwab Token ===")
with open(schwab_token_path, 'r') as f:
    token = json.load(f)
    print(f"Token exists: {'token' in token}")

print("\n=== Summary ===")
print("The directory structure is now set up for testing.")
print("")
print("To reproduce the bullish/bearish flow data issue:")
print("1. Run the actual app with: streamlit run app.py")
print("2. Enter a ticker (e.g., SPY)")
print("3. Click Refresh")
print("4. Observe if bullish/bearish flow data appears in the table")
print("5. If no data appears, check the app logs for:")
print("   - ATM option service initialization")
print("   - Options subscription")
print("   - Service registration")
