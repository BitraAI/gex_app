"""Shared async event loop for the GEX application.

Both app.py and flow_page.py import from here to ensure they use the
*same* event loop — avoiding the "bound to a different event loop"
RuntimeError that occurs when an httpx AsyncClient is dispatched on
multiple loops.
"""

import asyncio
import threading

_LOOP: asyncio.AbstractEventLoop | None = None
_THREAD: threading.Thread | None = None
_LOCK = threading.Lock()


def _run_forever(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def get_loop() -> asyncio.AbstractEventLoop:
    """Return the singleton background event loop, creating it if needed."""
    global _LOOP, _THREAD
    with _LOCK:
        if _LOOP is None or _LOOP.is_closed():
            _LOOP = asyncio.new_event_loop()
            _THREAD = threading.Thread(
                target=_run_forever, args=(_LOOP,), daemon=True,
            )
            _THREAD.start()
    return _LOOP
