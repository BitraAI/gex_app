"""Index symbol REST API polling service for SPX, RUT, NDX spots.

This service continuously polls Schwab REST API for index symbol quotes
($SPX:X, $RUT:X, $NDX:X) every 2 seconds and updates the ATM Order Flow
grid and candlestick charts with live spot prices.

This ensures index symbols update in real-time in both the order flow
grid and the main chart display.
"""

import asyncio
import logging
from typing import Any, Dict, List

from client import fetch_quotes
from _constants import INDEX_QUOTE_MAP

logger = logging.getLogger(__name__)

# Polling interval for index spot updates (2 seconds)
POLL_INTERVAL = 2.0




class IndexSpotPoller:
    """Background service for polling index symbol quotes via REST API.
    
    This service runs continuously in the background, fetching index symbol
    quotes every 2 seconds and updating the ATM Order Volume Service with live
    spot prices. This ensures index symbols ($SPX, $RUT, $NDX) display
    real-time prices in both the Order Flow grid and candlestick charts.
    
    The poller avoids hammer-the-gate by using rate limiting and efficient
    batching of API requests, while maintaining a robust fallback mechanism
    if API calls fail.
    """
    
    def __init__(self, async_client, loop):
        self._client = async_client
        self._loop = loop
        self._running = False
        self._task = None
        
        # Cache for avoiding redundant API calls
        self._last_quotes: Dict[str, Dict[str, Any]] = {}
        self._last_poll_time = 0
        
    @property
    def is_running(self) -> bool:
        """Check if the poller is currently running."""
        return self._running
        
    def update_tickers(self, tickers: List[str]):
        """Update the set of tickers to monitor for index symbols.
        
        Args:
            tickers: List of ticker symbols to monitor.
                    Only SPX, RUT, NDX (and variants) are polled.
        """
        # Only include index symbols, always preserve base symbols
        base = set(INDEX_QUOTE_MAP.keys())
        extra = {
            t.upper().lstrip("$") 
            for t in tickers 
            if t.upper().lstrip("$") in INDEX_QUOTE_MAP
        }
        self._tickers = base | extra
        logger.info(f"Index poller monitoring tickers: {self._tickers}")
        
    def start(self, atm_service):
        """Start the background polling service.
        
        Args:
            atm_service: AtmOptionVolumeService instance to update with live spots.
        """
        if self._running:
            logger.warning("Index poller already running")
            return
            
        self._running = True
        self._atm_service = atm_service
        
        logger.info("Starting index symbol poller")
        
        # Start background polling task
        self._task = asyncio.run_coroutine_threadsafe(
            self._poll_loop(), self._loop
        )
        
    def stop(self):
        """Stop the background polling service."""
        logger.info("Stopping index symbol poller")
        
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
            
    async def _poll_loop(self):
        """Main polling loop that runs every 2 seconds.
        
        This method implements the core polling logic:
        1. Sleeps for POLL_INTERVAL (2 seconds) or longer if previously throttled
        2. Fetches index quotes for all tracked tickers
        3. Updates the ATM service with live spot prices
        4. Implements proper error handling and rate limiting
        """
        logger.info("Index poller loop started")
        
        while self._running:
            try:
                # Throttle calls if we've recently polled to avoid hammering the API
                current_time = asyncio.get_event_loop().time()
                time_since_last_poll = current_time - self._last_poll_time
                
                if time_since_last_poll < POLL_INTERVAL:
                    sleep_time = POLL_INTERVAL - time_since_last_poll
                    await asyncio.sleep(sleep_time)
                    continue
                
                # Fetch quotes for all index symbols we track
                index_syms_to_fetch = [
                    INDEX_QUOTE_MAP[t] for t in self._tickers
                ]
                
                if not index_syms_to_fetch:
                    # No index tickers to track - sleep longer
                    await asyncio.sleep(POLL_INTERVAL * 10)
                    continue
                    
                try:
                    MAX_RETRIES = 3
                    for attempt in range(MAX_RETRIES):
                        try:
                            idx_resp = await fetch_quotes(self._client, index_syms_to_fetch)
                            break
                        except Exception:
                            if attempt < MAX_RETRIES - 1:
                                await asyncio.sleep(1.0)
                            else:
                                raise
                    
                    self._last_poll_time = current_time
                    self._last_quotes = idx_resp
                    
                    # Process and update each ticker's spot price
                    for ticker_upper, oauth_symbol in INDEX_QUOTE_MAP.items():
                        if ticker_upper not in self._tickers:
                            continue
                            
                        # Get quote response for this index symbol
                        qd = idx_resp.get(oauth_symbol, {}) or {}
                        quote = qd.get("quote", {}) or qd.get(oauth_symbol, {})
                        
                        # Extract last price with multiple fallback options
                        last_price = (
                            quote.get("lastPrice") or 
                            quote.get("mark") or 
                            quote.get("closePrice")
                        )
                        
                        if last_price is not None and float(last_price) > 0:
                            spot_price = float(last_price)
                            
                            # Update ATM service with live spot
                            logger.debug(f"Updating index {ticker_upper} spot: ${spot_price:.2f}")
                            self._atm_service.set_ticker_spot(ticker_upper, spot_price)
                        else:
                            logger.debug(f"Index {ticker_upper} quote returned no valid price: {quote}")
                            
                except Exception as e:
                    # Log the error but continue running
                    logger.warning(f"Failed to fetch index quotes: {str(e)}")
                    # Continue running even if this fails
                    await asyncio.sleep(POLL_INTERVAL)
                    continue
                    
                # Sleep for the polling interval
                await asyncio.sleep(POLL_INTERVAL)
                
            except asyncio.CancelledError:
                logger.info("Index poller loop cancelled")
                break
            except Exception as e:
                logger.error(f"Unexpected error in index poller loop: {str(e)}")
                await asyncio.sleep(POLL_INTERVAL * 5)  # Wait longer on unexpected errors
                
        self._task = None
        logger.info("Index poller loop stopped")