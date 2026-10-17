"""Import all tool modules so each registers itself with the shared server."""

from schwab_mcp.tools import (  # noqa: F401  (registration side effects)
    candles,
    gex_analytics,
    market_hours,
    movers,
    option_chain,
    orders,
    positions,
    spot,
    transactions,
)
