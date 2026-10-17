"""Read-only MCP server exposing gex_app market data and Schwab account info.

Entry point: python schwab_mcp/main.py (registered in OpenCode config as
`gex-app`).  Tool implementations live in schwab_mcp/tools/, one module per
tool; shared plumbing lives in schwab_mcp/core.py.
"""
