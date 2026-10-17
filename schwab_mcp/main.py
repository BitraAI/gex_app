#!/usr/bin/env python3
"""Entrypoint for the gex-app MCP server (stdio transport).

Read-only tools over stdio transport:
  - get_spot            — live quotes / last prices
  - get_option_chain    — per-contract marks, greeks, volume, open interest
  - get_gex_analytics   — GEX totals, call/put walls, gamma flip, expected
                          pin, IV skew, SSVI surface (same pipeline as the app)
  - get_candles         — OHLCV bars from the Schwab price-history API
  - get_positions       — account balances and open positions (read-only)

Tool implementations live one-per-module in schwab_mcp/tools/; shared plumbing
(Schwab client singleton, semaphore, JSON helpers) lives in schwab_mcp/core.py.

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
"""

import os
import sys

# Allow "python schwab_mcp/main.py" (and any cwd) to import the package.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from schwab_mcp.core import server  # noqa: E402
import schwab_mcp.tools  # noqa: E402,F401  (registration side effects)

if __name__ == "__main__":
    server.run()
