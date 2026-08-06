import pytest
from datetime import datetime, timezone

import option_streaming_service as oss


def _mk_ticker():
    return {
        "stream_symbol": "SPY",
        "spot": 0.0,
        "atm_strike": 0.0,
        "spot_history": [],
        "vol_history": [],
        "exec_history": [],
        "call_bid": 100.0,
        "call_ask": 101.0,
        "put_bid": 100.0,
        "put_ask": 101.0,
        "call_delta": 0.5,
        "put_delta": -0.5,
        "bullish": 0,
        "bearish": 0,
        "buy_vol": 0,
        "sell_vol": 0,
    }


@pytest.fixture
def svc():
    """A bare AtmOptionVolumeService that performs no I/O beyond the
    (harmless) ticker-history file read.  Uses None for the async client
    and event loop because the constructor only stores them."""
    instance = oss.AtmOptionVolumeService(None, None)
    instance._ticker_flows.clear()
    yield instance


@pytest.fixture
def ticker(svc):
    t = _mk_ticker()
    svc._ticker_flows["TEST"] = t
    return t


@pytest.fixture
def fixed_now(monkeypatch):
    """Pin module wall-clock time so the 60 s rolling windows are deterministic."""
    now = 1_000_000.0
    monkeypatch.setattr(oss._time_mod, "time", lambda: now)
    return now