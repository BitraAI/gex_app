import asyncio
import threading
import time
from datetime import datetime, timezone

import pandas as pd

# Mocking the necessary components for testing
class MockAsyncClient:
    pass

class MockStreamClient:
    def __init__(self, client, enforce_enums=False):
        self.client = client
        self._handlers = []
    
    async def login(self):
        pass
    
    async def level_one_equity_subs(self, symbols):
        pass
    
    def add_level_one_equity_handler(self, handler):
        self._handlers.append(handler)
    
    async def handle_message(self):
        await asyncio.sleep(0.1)  # Simulate some delay

class MockStreamingService:
    def __init__(self, async_client, loop):
        self._client = async_client
        self._loop = loop
        self._symbol = None
        self._running = False
        self._connected = False
        self._ticks_received = 0
        self._df = pd.DataFrame()
        self._current_bar = None
        self._lock = threading.Lock()
    
    @property
    def symbol(self):
        return self._symbol
    
    def start(self, symbol):
        self._symbol = symbol
        self._running = True
        # Simulate receiving some tick data
        self._simulate_ticks()
    
    def _simulate_ticks(self):
        # Simulate some ticks at different times
        import random
        import time
        
        def generate_ticks():
            base_time = int(time.time() * 1000)
            for i in range(20):
                tick_time = base_time + i * 1000
                price = 500.0 + random.random() * 10
                size = random.randint(100, 1000)
                self._handle_tick(tick_time, price, size)
                time.sleep(0.1)
        
        self._thread = threading.Thread(target=generate_ticks)
        self._thread.daemon = True
        self._thread.start()
    
    def _handle_tick(self, tick_time_ms, price, size):
        bucket = (tick_time_ms // 1000) * 1000
        if self._current_bar is None:
            self._current_bar = {
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": size,
                "datetime": bucket / 1000  # Convert to seconds
            }
        else:
            self._current_bar["high"] = max(self._current_bar["high"], price)
            self._current_bar["low"] = min(self._current_bar["low"], price)
            self._current_bar["close"] = price
            self._current_bar["volume"] += size
    
    def get_candles(self):
        return self._df
    
    async def _stream(self):
        pass

# Test the actual streaming service
print("=" * 60)
print("TESTING: Streaming service can properly aggregate ticks")
print("=" * 60)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

client = MockAsyncClient()
from streaming_service import StreamingService

streaming_service = StreamingService(client, loop)

# Start streaming
print("\n1. Starting stream for SPY")
streaming_service.start("SPY")

# Wait for initial data collection
print("2. Waiting for initial data (10 seconds)...")
time.sleep(10)

# Test the get_candles method
print("3. Checking current status:")
candles = streaming_service.get_candles()
print(f"   - ticks_received: {streaming_service._ticks_received}")
print(f"   - DataFrame rows: {len(candles)}")
print(f"   - Has current_bar: {streaming_service._current_bar is not None}")

if not candles.empty:
    print(f"   - Sample candle: {candles.iloc[0].to_dict()}")

print("\n4. Final streaming stats:")
stats = streaming_service.get_stats()
for key, value in stats.items():
    print(f"   {key}: {value}")

# Test connecting to live streaming
print("\n" + "=" * 60)
print("TESTING: Chart rendering and updates")
print("=" * 60)

# Simulate what happens in render_candlesticks_frag
print("\n5. Simulating render_candlesticks_frag (Streamlit fragment)")

# Mock what the fragment does
symbol = "SPY"
streaming_service.start(symbol)

print("6. Fetching streaming data (like render_candlesticks_frag does):")
streaming_df = streaming_service.get_candles()
print(f"   - Streaming data shape: {streaming_df.shape}")

if not streaming_df.empty:
    print("   - Sample data:")
    print(streaming_df.head(3).to_string())
    print()
    print("   - Data types:")
    print(f"     - index dtype: {streaming_df.index.dtype}")
    for col in ['open', 'high', 'low', 'close', 'volume']:
        print(f"     - {col} dtype: {streaming_df[col].dtype}")
else:
    print("   - No streaming data available")

print("\n" + "=" * 60)
print("TESTING COMPLETE")
print("=" * 60)
