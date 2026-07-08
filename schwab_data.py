import os
import sys

from schwab import auth
from schwab.auth import client_from_token_file
import json 

# Replace with your credentials from the Schwab Developer Portal
api_key = 'REDACTED_SECRET'
app_secret = 'REDACTED_SECRET'
callback_url = 'https://127.0.0.1:8182/'
token_path = '~/.local/share/gex_app/schwab_token.json' 

# Initialize the client and start the authentication flow
client = client_from_token_file(token_path, api_key, app_secret)

# Example: Fetch price history
response = client.get_price_history_every_day('AAPL')
response.raise_for_status()
print(json.dumps(response.json(), indent=4))
