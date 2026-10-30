"""Shared plumbing for the gex-app MCP server.

Hosts the MCPServer instance, the shared Schwab client singleton, the request
semaphore, JSON helpers, and the risk-free/dividend-yield lookup used by the
analytics pipeline.  Tool modules import from here and register themselves
with `@server.tool()`.
"""

import asyncio
import json
import math
import os
import sys
from typing import Any

# Allow imports of the repo's data modules (client, analytics, calculations)
# no matter which cwd the server process is started in.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# mcp v2: MCPServer lives at mcp.server.mcpserver
from mcp.server.mcpserver import MCPServer

server = MCPServer(
    name="gex-app",
    title="GEX App",
    description="Market data (option chains, greeks, open interest, GEX analytics, candles), Schwab account positions, and equity order execution (code-gated confirm)",
    instructions=(
        "Tools query the Schwab Trader API and compute gex_app analytics locally. "
        "Data tools are READ-ONLY: no order placement, modification, or "
        "cancellation. The ONLY trading tools are place_buy_order, "
        "place_sell_order, replace_order (three-step: 1) call with "
        "confirm=false for a preview + confirmation_code, which submits "
        "nothing; 2) present the preview AND code to the user and WAIT for "
        "explicit approval; 3) re-call with confirm=true plus that "
        "confirmation_code — a confirm call without the matching code is "
        "rejected before reaching Schwab). Equity MARKET/LIMIT, DAY/GTC only. "
        "cancel_order previews live state and is not code-gated. "
        "Use get_gex_analytics for walls/gamma structure, get_option_chain for "
        "per-strike data, get_spot for live prices, get_positions for the "
        "linked account (account number truncated for safety)."
    ),
)

_client: Any = None
_client_lock = asyncio.Lock()
# Schwab REST API shouldn't be hammered with parallel calls; MCP clients may
# fire several tools in one burst (OpenCode does).
_schwab_sem = asyncio.Semaphore(4)


async def _get_client() -> Any:
    """Shared Schwab AsyncClient (token auto-refresh handled by schwab-py)."""
    global _client
    if _client is None:
        async with _client_lock:
            if _client is None:
                from scripts.client import create_client
                _client = create_client()
    return _client


def _jsonable(obj: Any) -> Any:
    """Convert numpy/decimal/special types into plain JSON-safe values."""
    if obj is None or isinstance(obj, (str, bool, int)):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    # numpy scalars / pandas values
    item = getattr(obj, "item", None)
    if callable(item):
        try:
            return _jsonable(item())
        except Exception:
            pass
    iso = getattr(obj, "isoformat", None)
    if callable(iso):
        return iso()
    try:
        return float(obj)
    except Exception:
        return str(obj)


def _ok(data: Any) -> str:
    return json.dumps(_jsonable(data), ensure_ascii=False)


def _err(msg: str) -> str:
    return json.dumps({"error": msg})


async def _r_and_q(symbol: str) -> tuple[float, float]:
    """Risk-free rate proxy + dividend yield, same sources as app.py."""
    from scripts.client import get_interest_rate, get_yield
    try:
        r = float(await get_interest_rate(await _get_client())) / 100.0
    except Exception:
        r = 0.05
    try:
        q = float(await get_yield(await _get_client(), symbol)) / 100.0
    except Exception:
        q = 0.0
    return r, q
