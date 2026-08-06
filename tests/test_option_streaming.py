import pytest

import option_streaming_service as oss
from option_streaming_service import AtmOptionVolumeService, _make_option_symbol


# --------------------------------------------------------------------------- #
# OCC option symbol building
# --------------------------------------------------------------------------- #

class TestMakeOptionSymbol:
    def test_call_symbol(self):
        assert _make_option_symbol("SPYW", "260821", "C", 570.0) == "SPYW  260821C00570000"

    def test_put_symbol_and_strike_padding(self):
        assert _make_option_symbol("SPY", "260821", "P", 570.0).endswith("P00570000")

    def test_root_padded_to_6(self):
        sym = _make_option_symbol("SPY", "260821", "C", 100.0)
        assert sym.startswith("SPY   ")  # 3 chars + 3 spaces = 6
        assert len(sym[:6]) == 6

    def test_fractional_strike_rounds_to_integer_millis(self):
        # 570.05 * 1000 = 570050 -> 8-digit int
        sym = _make_option_symbol("SPYW", "260821", "C", 570.05)
        assert sym.endswith("C00570050")


# --------------------------------------------------------------------------- #
# Aggressor direction inference (_infer_dir)
# --------------------------------------------------------------------------- #

class TestInferDir:
    def test_at_or_above_mid_is_buy(self):
        assert AtmOptionVolumeService._infer_dir(None, 100.5, 100.0, 101.0) == "buy"
        assert AtmOptionVolumeService._infer_dir(None, 100.5, 100.0, 101.0) == "buy"  # == mid

    def test_below_mid_is_sell(self):
        assert AtmOptionVolumeService._infer_dir(None, 100.49, 100.0, 101.0) == "sell"

    def test_empty_when_quotes_unavailable(self):
        assert AtmOptionVolumeService._infer_dir(None, 100.0, None, 101.0) == ""
        assert AtmOptionVolumeService._infer_dir(None, 100.0, 100.0, None) == ""
        assert AtmOptionVolumeService._infer_dir(None, 100.0, None, None) == ""
        assert AtmOptionVolumeService._infer_dir(None, 100.0, 102.0, 101.0) == ""  # inverted spread


# --------------------------------------------------------------------------- #
# Executed-flow bucket semantics: buy/sell per side x direction
# --------------------------------------------------------------------------- #

class TestExecutedFlowBuckets:
    def _trade(self, ticker, opt_type, price, size):
        AtmOptionVolumeService._process_trade_ticker(None, ticker, price, size, opt_type)

    def test_buy_call_adds_to_buy(self, svc, ticker):
        svc._process_trade_ticker(ticker, 101.0, 25, "CALL")
        assert ticker["buy_vol"] == 25
        assert ticker["sell_vol"] == 0

    def test_sell_call_adds_to_sell(self, svc, ticker):
        svc._process_trade_ticker(ticker, 100.0, 25, "CALL")
        assert ticker["sell_vol"] == 25
        assert ticker["buy_vol"] == 0

    def test_sell_put_adds_to_buy(self, svc, ticker):
        svc._process_trade_ticker(ticker, 100.0, 25, "PUT")
        assert ticker["buy_vol"] == 25
        assert ticker["sell_vol"] == 0

    def test_buy_put_adds_to_sell(self, svc, ticker):
        svc._process_trade_ticker(ticker, 101.0, 25, "PUT")
        assert ticker["sell_vol"] == 25
        assert ticker["buy_vol"] == 0

    def test_identity_buy_eq_call_buy_plus_put_sell(self, svc, ticker):
        svc._process_trade_ticker(ticker, 101.0, 10, "CALL")
        svc._process_trade_ticker(ticker, 100.0, 5, "PUT")
        assert ticker["buy_vol"] == 15
        assert ticker["sell_vol"] == 0
        svc._process_trade_ticker(ticker, 100.0, 3, "CALL")
        svc._process_trade_ticker(ticker, 101.0, 7, "PUT")
        assert ticker["sell_vol"] == 10
        assert ticker["buy_vol"] == 15


# --------------------------------------------------------------------------- #
# Order absorption
# --------------------------------------------------------------------------- #

class TestAbsorption:
    def test_basic_ratio(self, svc, ticker, fixed_now):
        # spot moved 0.05 over 60s; volume delta 1500 -> 1500 / 0.05
        ticker["spot"] = 570.0
        ticker["spot_history"] = [(fixed_now - 60, 569.95), (fixed_now, 570.0)]
        ticker["vol_history"] = [(fixed_now - 60, 1000.0), (fixed_now, 2500.0)]
        assert svc.get_ticker_absorption("TEST") == pytest.approx(30000.0)

    def test_none_below_min_volume(self, svc, ticker, fixed_now):
        ticker["spot"] = 570.0
        ticker["spot_history"] = [(fixed_now - 60, 569.95), (fixed_now, 570.0)]
        ticker["vol_history"] = [(fixed_now - 60, 0.0), (fixed_now, 10.0)]  # < 20
        assert svc.get_ticker_absorption("TEST") is None

    def test_none_too_few_samples(self, svc, ticker, fixed_now):
        ticker["spot"] = 570.0
        ticker["spot_history"] = [(fixed_now, 570.0)]          # only 1 sample
        ticker["vol_history"] = [(fixed_now - 60, 0.0), (fixed_now, 1000.0)]
        assert svc.get_ticker_absorption("TEST") is None

    def test_none_untracked(self, svc, fixed_now):
        assert svc.get_ticker_absorption("MISSING") is None

    def test_pinned_spot_uses_floor(self, svc, ticker, fixed_now):
        # Price basically pinned: spot delta ~0 -> floor of 0.05 applies
        ticker["spot"] = 570.0
        ticker["spot_history"] = [(fixed_now - 60, 570.0), (fixed_now, 570.0)]
        ticker["vol_history"] = [(fixed_now - 60, 1000.0), (fixed_now, 1500.0)]
        assert svc.get_ticker_absorption("TEST") == pytest.approx(500.0 / 0.05)

    def test_absorbs_more_with_lower_spot_move(self, svc, ticker, fixed_now):
        ticker["spot_history"] = [(fixed_now - 60, 570.0), (fixed_now, 570.5)]
        ticker["vol_history"] = [(fixed_now - 60, 1000.0), (fixed_now, 2000.0)]
        # 1000 vol over 0.5 spot = 2000 vol/$1
        assert svc.get_ticker_absorption("TEST") == pytest.approx(2000.0)