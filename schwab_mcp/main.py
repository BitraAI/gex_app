#!/usr/bin/env python3
"""Entrypoint for the gex-app MCP server.

Read-only tools over stdio transport:
  - get_spot            — live quotes / last prices
  - get_option_chain    — per-contract marks, greeks, volume, open interest
  - get_gex_analytics   — GEX totals, call/put walls, gamma flip, expected
                          pin, IV skew, SSVI surface (same pipeline as the app)
  - get_candles         — OHLCV bars from the Schwab price-history API
  - get_positions       — account balances and open positions (read-only)

Transport selection (default: stdio):
  python main.py                        — stdio (OpenCode, CLI agents)
  python main.py --transport sse        — SSE at http://localhost:8001/sse
  python main.py --transport streamable-http — HTTP at http://localhost:8001/mcp

Register it in OpenCode (project or global opencode.json(c)):

  "mcp": {
    "servers": {
      "gex-app": {
        "type": "local",
        "command": ["/home/spark_admin/gex_venv/bin/python",
                    "/home/spark_admin/gex_app/schwab_mcp/main.py"]
      }
    }
  }

Register it in Open WebUI (Settings → MCP → Add Server):
  Base URL:  http://localhost:8001/mcp
  or
  SSE URL:   http://localhost:8001/sse
"""

import argparse
import os
import sys
from typing import Callable

# Allow "python schwab_mcp/main.py" (and any cwd) to import the package.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from schwab_mcp.core import server  # noqa: E402
import schwab_mcp.tools  # noqa: E402,F401  (registration side effects)


def _cors_middleware(app: Callable) -> Callable:
    """ASGI middleware that adds CORS headers to every response."""
    async def wrapped(scope, receive, send):
        async def send_with_cors(message):
            if message.get("type") == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"access-control-allow-origin", b"*"))
                headers.append((b"access-control-allow-methods", b"*"))
                headers.append((b"access-control-allow-headers", b"*"))
                headers.append((b"access-control-expose-headers", b"*"))
                message["headers"] = headers
            await send(message)

        if scope["type"] == "http" and scope["method"] == "OPTIONS":
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-length", b"0"),
                    (b"access-control-allow-origin", b"*"),
                    (b"access-control-allow-methods", b"*"),
                    (b"access-control-allow-headers", b"*"),
                    (b"access-control-expose-headers", b"*"),
                ],
            })
            await send({"type": "http.response.body", "body": b""})
            return

        await app(scope, receive, send_with_cors)
    return wrapped


def _run_streamable_http(host: str, port: int) -> None:
    """Start the MCP server as a Streamable HTTP endpoint with CORS."""
    http_app = server.streamable_http_app()
    wrapped_app = _cors_middleware(http_app)

    import uvicorn
    uvicorn.run(wrapped_app, host=host, port=port)


def _run_sse(host: str, port: int) -> None:
    """Start the MCP server as an SSE endpoint with CORS."""
    sse_app = server.sse_app(host=host)
    wrapped_app = _cors_middleware(sse_app)

    import uvicorn
    uvicorn.run(wrapped_app, host=host, port=port)


def _run_stdio() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="gex-app MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport mode (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="HTTP/SSE port (default: 8001)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        _run_stdio()
    elif args.transport == "sse":
        _run_sse(args.host, args.port)
    else:
        _run_streamable_http(args.host, args.port)
