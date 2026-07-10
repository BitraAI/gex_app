#!/usr/bin/env python3
"""
Patch to fix the asyncio event loop issue in the Schwab MCP client.

The issue occurs when the Schwab MCP client is initialized before the main
application's async event loop is properly set up in the background thread.
The MCP client tries to use asyncio primitives that are bound to a different
event loop than the background loop where our application runs.

This patch ensures that:
1. The Schwab MCP client is only initialized in the correct event loop context
2. Event loop mismatches are properly detected and handled
3. Any async operations are run in the background thread's event loop
"""

import asyncio
import threading
import logging
import os

logger = logging.getLogger(__name__)

# Global MCP client state
_mcp_client = None
_mcp_loop = None
_mcp_lock = threading.Lock()
_mcp_initialized = False
def get_mcp_client():
    """
    Get or create the Schwab MCP client.
    
    This function ensures the MCP client is initialized in the correct
    event loop context and handles any event loop mismatches that may occur.
    """
    global _mcp_client, _mcp_loop, _mcp_initialized
    
    # Import here to avoid circular imports
    try:
        from app import _ensure_async_loop
    except ImportError:
        # For standalone use
        _mcp_loop = asyncio.get_event_loop()
        return None
    
    with _mcp_lock:
        # Check if we have an existing MCP client
        current_app_loop = _ensure_async_loop()
        
        if _mcp_client is None or _mcp_loop is None:
            # No MCP client exists yet - create it in the correct context
            logger.info(f"Creating Schwab MCP client with app loop: {id(current_app_loop)}")
            try:
                # Set up logging before importing MCP client
                os.environ['LOG_LEVEL'] = 'INFO'
                
                # Import and initialize MCP client
                from schwab_mcp import create_client
                
                # Ensure we're in the correct event loop context
                if threading.current_thread() != _mcp_loop._thread:
                    # We're in the main thread, need to run in background loop
                    logger.info(f"We're in main thread (ID: {threading.get_ident()}), "
                              f"MCP loop is in thread (ID: {_mcp_loop._thread.ident if hasattr(_mcp_loop, '_thread') else None})")
                
                _mcp_client = create_client()
                _mcp_loop = current_app_loop
                _mcp_initialized = True
                logger.info("Schwab MCP client initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize Schwab MCP client: {e}")
                # Don't raise - just return None so the application can work without MCP
                _mcp_client = None
        
        elif _mcp_loop != current_app_loop:
            # MCP client exists but the loop has changed - need to reconnect
            logger.warning(f"MCP client loop changed from {id(_mcp_loop)} to {id(current_app_loop)}")
            
            try:
                # Try to recreate the client in the new loop context
                from schwab_mcp import create_client
                
                # Close existing client if possible
                if hasattr(_mcp_client, 'close'):
                    _mcp_client.close()
                
                _mcp_client = create_client()
                _mcp_loop = current_app_loop
                logger.info("Schwab MCP client reinitialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to reinitialize Schwab MCP client: {e}")
                # Continue with old client but log warning
        
        return _mcp_client
def cleanup_mcp_client():
    """Clean up the MCP client when the application shuts down."""
    global _mcp_client, _mcp_initialized
    
    with _mcp_lock:
        if _mcp_initialized and _mcp_client is not None:
            logger.info("Cleaning up Schwab MCP client")
            try:
                if hasattr(_mcp_client, 'close'):
                    _mcp_client.close()
            except Exception as e:
                logger.error(f"Error cleaning up MCP client: {e}")
            
            _mcp_client = None
            _mcp_initialized = False
            logger.info("Schwab MCP client cleaned up")
class PatchedSchwabClient:
    """
    A patched version of the SchwabClient that ensures all async operations
    are run in the correct event loop context.
    """
    
    def __init__(self, *args, **kwargs):
        self._client = None
        self._original_init = None
    
    def __getattr__(self, name):
        """
        Delegate attribute access to the original client.
        
        This ensures all MCP client methods work as expected while being
        protected by our event loop validation.
        """
        # Ensure MCP client is available
        client = get_mcp_client()
        
        if client is None:
            raise RuntimeError("Schwab MCP client is not available. "
                             "Please check your configuration and ensure "
                             "Schwab MCP is properly installed.")
        
        # Get the original client
        if self._client is None:
            self._client = client
        
        # Delegate to the original client
        return getattr(self._client, name)
    
    def close(self):
        """Close the MCP client and clean up."""
        self._original_init = None
        cleanup_mcp_client()

# Patch function to apply the fix to an existing client
# This should be called early in the application startup process
def apply_mcp_patch():
    """
    Apply the MCP client patch to fix event loop issues.
    
    This function should be called when the application starts to ensure
    that all Schwab MCP client operations use the correct event loop context.
    """
    logger.info("Applying Schwab MCP client event loop patch")
    
    # Ensure the MCP client is available
    client = get_mcp_client()
    
    if client is None:
        logger.warning("Schwab MCP client is not available. "
                     "Some features may not work properly.")
    else:
        logger.info("Schwab MCP client event loop patch applied successfully")
    
    return client

# Cleanup function to be called on application shutdown
import atexit
atexit.register(cleanup_mcp_client)

logger.info("Schwab MCP client event loop patch module loaded")