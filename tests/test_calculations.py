import pytest

from calculations import (
    _parse_exp_key,
    _find_fallback,
    aggregate_by_expiration,
    aggregate_by_strike,
    calculate_atm_strike,
    calculate_cex,
    calculate_gex,
    compute_totals,
    get_strike_spacing,
    parse_option_chain,
    build_greeks_lookup,
)


# --------------------------------------------------------------------------- #
# Strike spacing / ATM strike
# --------------------------------------------------------------------------- #

class TestStrikeSpacing:
    def test_tier_boundaries(self):
        assert get_strike_spacing(10) == 0.5
        assert get_strike_spacing(25) == 0.5
        assert get_strike_spacing(100) == 1.0
        assert get_strike_spacing(200) == 1.0
        assert get_strike_spacing(300) == 2.5
        assert get_strike_spacing(500) == 2.5
        assert get_strike_spacing(750) == 5.0
        assert get_strike_spacing(1000) == 5.0
        assert get_strike_spacing(1500) == 10.0

    def test_edge_and_negative(self):
        assert get_strike_spacing(0) == 0.5
        assert get_strike_spacing(-1) == 0.5


class TestAtmStrike:
    @pytest.mark.parametrize("spot,expected", [
        (571.5, 570.0),   # 5.0 spacing -> round(114.3)*5 = 570
        (570.0, 570.0),
        (100.0, 100.0),
        (99.9, 100.0),    # 1.0 spacing round()
        (24.9, 25.0),     # 0.5 spacing
    ])
    def test_rounding(self, spot, expected):
        assert calculate_atm_strike(spot) == expected


# --------------------------------------------------------------------------- #
# GEX / CEX math
# --------------------------------------------------------------------------- #

class TestGex:
    def test_single_strike(self):
        # gamma=1e-6, OI=1M, spot=100:
        #   gamma*OI*100*spot^2*0.01 = 1e-6*1e6*100*1e4*0.01 = 10,000
        gex = calculate_gex(1e-6, 1_000_000, 100.0)
        assert gex == pytest.approx(10_000.0)
        assert gex > 0

    def test_zero_oi_gives_zero(self):
        assert calculate_gex(1e-6, 0, 100.0) == 0.0

    def test_negative_gamma_gives_negative(self):
        assert calculate_gex(-1e-6, 1_000_000, 100.0) < 0

    def test_scales_quadratically_with_spot(self):
        g1 = calculate_gex(1e-6, 1_000, 100.0)
        g2 = calculate_gex(1e-6, 1_000, 200.0)
        assert g2 == pytest.approx(4 * g1)


class TestCex:
    def test_zero_when_guards_trip(self):
        assert calculate_cex(0.1, 1e-6, 0.3, 100.0, 100.0, 1, 0, "CALL") == 0.0
        assert calculate_cex(0.1, 1e-6, 0.3, 100.0, 0.0, 1, 10, "CALL") == 0.0
        assert calculate_cex(0.1, 1e-6, 0.3, 100.0, 100.0, 0, 10, "CALL") == 0.0
        assert calculate_cex(0.1, 1e-6, 0.0, 100.0, 100.0, 1, 10, "CALL") == 0.0

    def test_put_is_negative(self):
        c = calculate_cex(0.1, 1e-6, 0.3, 100.0, 100.0, 1, 1000, "PUT")
        assert c <= 0.0

    def test_call_returns_deterministic_rounded_float(self, monkeypatch):
        # Pin clock to 09:30 NY so the intraday charm term is deterministic.
        class _FakeDT:
            @staticmethod
            def now(tz=None):
                from datetime import datetime
                import zoneinfo
                return datetime(2026, 8, 4, 9, 30, 0, tzinfo=zoneinfo.ZoneInfo("America/New_York"))

        monkeypatch.setattr("calculations.datetime", _FakeDT)
        c = calculate_cex(0.05, 1e-6, 0.25, 100.0, 100.0, 1, 1000, "CALL")
        assert isinstance(c, float)
        assert c == round(c, 2)


# --------------------------------------------------------------------------- #
# Option-chain parsing
# --------------------------------------------------------------------------- #

class TestParseExpKey:
    def test_strips_suffix(self):
        assert _parse_exp_key("2026-08-21:4") == "2026-08-21"
        assert _parse_exp_key("2026-08-21") == "2026-08-21"


class TestFindFallback:
    def test_exact_delta_match(self):
        fb = {("2026-08-21", 0.5, "CALL"): {"gamma": 1.0, "oi": 5, "volume": 7}}
        assert _find_fallback(fb, "2026-08-21", 0.5, "CALL") == fb[("2026-08-21", 0.5, "CALL")]

    def test_nearest_delta_within_tolerance(self):
        fb = {("2026-08-21", 0.5, "CALL"): {"gamma": 1.0, "oi": 5, "volume": 7}}
        res = _find_fallback(fb, "2026-08-21", 0.48, "CALL")
        assert res is fb[("2026-08-21", 0.5, "CALL")]

    def test_rejects_far_delta_and_wrong_side(self):
        fb = {("2026-08-21", 0.5, "CALL"): {"gamma": 1.0, "oi": 5, "volume": 7}}
        assert _find_fallback(fb, "2026-08-21", 0.1, "CALL") is None
        assert _find_fallback(fb, "2026-08-21", 0.5, "PUT") is None
        assert _find_fallback(None, "2026-08-21", 0.5, "CALL") is None


class TestParseOptionChain:
    def _chain(self):
        return {
            "underlying": {"mark": 100.0},
            "callExpDateMap": {
                "2026-08-21:4": {
                    "100.0": [
                        {"putCall": "CALL", "strike": 100.0, "gamma": 1e-6,
                         "delta": 0.5, "openInterest": 1000, "totalVolume": 200,
                         "volatility": 25.0, "theta": -0.1, "vega": 0.2, "mark": 2.5}
                    ]
                }
            },
            "putExpDateMap": {
                "2026-08-21:4": {
                    "100.0": [
                        {"putCall": "PUT", "strike": 100.0, "gamma": 1e-6,
                         "delta": -0.5, "openInterest": 1500, "totalVolume": 300,
                         "volatility": 26.0, "theta": -0.1, "vega": 0.2, "mark": 2.5}
                    ]
                }
            },
        }

    def test_parses_call_and_put(self):
        results, spot = parse_option_chain(self._chain())
        assert spot == 100.0
        types = {r["type"] for r in results}
        assert types == {"CALL", "PUT"}
        call = next(r for r in results if r["type"] == "CALL")
        put = next(r for r in results if r["type"] == "PUT")
        assert call["gex"] > 0
        assert put["gex"] < 0  # put GEX stored negative
        assert call["open_interest"] == 1000
        assert put["open_interest"] == 1500

    def test_spot_falls_back_to_last(self):
        chain = self._chain()
        del chain["underlying"]["mark"]
        chain["underlying"]["last"] = 101.0
        _, spot = parse_option_chain(chain)
        assert spot == 101.0

    def test_ignores_non_option_entries(self):
        chain = self._chain()
        chain["callExpDateMap"]["2026-08-21:4"]["100.0"].append(
            {"putCall": "PUT", "strike": 100.0}  # put in the call map -> skipped
        )
        results, _ = parse_option_chain(chain)
        assert len(results) == 2


class TestBuildGreeksLookup:
    def test_rounds_delta_and_keys_by_type(self):
        chain = {
            "callExpDateMap": {"2026-08-21:4": {"100.0": [
                {"gamma": 1e-6, "delta": 0.504, "openInterest": 10, "totalVolume": 2}]}},
            "putExpDateMap": {"2026-08-21:4": {"100.0": [
                {"gamma": 1e-6, "delta": -0.498, "openInterest": 20, "totalVolume": 3}]}},
        }
        lookup = build_greeks_lookup(chain)
        assert (("2026-08-21", 0.5, "CALL")) in lookup
        assert (("2026-08-21", -0.5, "PUT")) in lookup
        assert lookup[("2026-08-21", 0.5, "CALL")]["oi"] == 10

    def test_skips_missing_greeks(self):
        chain = {
            "callExpDateMap": {"2026-08-21:4": {"100.0": [
                {"delta": 0.5}]}},
            "putExpDateMap": {},
        }
        assert build_greeks_lookup(chain) == {}


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #

class TestAggregateByStrike:
    def _entries(self):
        # Two entries share the same strike: one call, one put.
        base = {
            "expiration": "2026-08-21",
            "gamma": 1e-6,
            "delta": 0.0,
            "vega": 0.2,
            "theta": -0.1,
            "iv": 25.0,
            "volume": 100,
            "mark": 2.5,
            "days_to_exp": 5,
        }
        call = {**base, "type": "CALL", "strike": 100.0, "open_interest": 1000,
                "gex": 1_000_000.0, "vex": 200.0, "cex": 50.0}
        put = {**base, "type": "PUT", "strike": 100.0, "open_interest": 2000,
               "gex": -2_000_000.0, "vex": -400.0, "cex": -100.0}
        return [call, put]

    def test_net_gex_is_signed_sum(self):
        row = aggregate_by_strike(self._entries(), spot=100.0)[0]
        assert row["call_gex"] == 1_000_000.0
        assert row["put_gex"] == 2_000_000.0   # stored as abs
        assert row["net_gex"] == -1_000_000.0   # -2M + 1M

    def test_min_oi_filter(self):
        # call oi=1000, put oi=2000.  min_oi=1500 drops the call, keeps the put.
        rows = aggregate_by_strike(self._entries(), spot=100.0, min_oi=1500)
        assert len(rows) == 1
        assert rows[0]["num_calls"] == 0
        assert rows[0]["num_puts"] == 1
        # min_oi=500 keeps both on the same strike -> still 1 row.
        assert len(aggregate_by_strike(self._entries(), spot=100.0, min_oi=500)) == 1

    def test_itm_flag(self):
        rows = aggregate_by_strike([{**self._entries()[0], "strike": 101.0}], spot=100.0)
        assert rows[0]["itm"] is False
        rows = aggregate_by_strike([{**self._entries()[0], "strike": 99.0}], spot=100.0)
        assert rows[0]["itm"] is True

    def test_sorted_by_strike(self):
        e = self._entries()[0]
        rows = aggregate_by_strike(
            [{**e, "strike": 200.0}, {**e, "strike": 100.0}], spot=100.0)
        assert [r["strike"] for r in rows] == [100.0, 200.0]


class TestAggregateByExpiration:
    def test_aggregates_across_strikes(self):
        base = {
            "expiration": "2026-08-21", "strike": 100.0, "gamma": 1e-6,
            "delta": 0.0, "iv": 25.0, "days_to_exp": 5,
        }
        data = [
            {**base, "type": "CALL", "open_interest": 1000, "gex": 1.0},
            {**base, "type": "PUT", "open_interest": 1000, "gex": -2.0},
            {**base, "type": "PUT", "strike": 105.0, "open_interest": 500, "gex": -3.0},
        ]
        rows = aggregate_by_expiration(data, spot=100.0)
        assert len(rows) == 1
        row = rows[0]
        assert row["call_gex"] == 1.0
        assert row["put_gex"] == 5.0
        assert row["net_gex"] == -4.0
        assert row["num_calls"] == 1
        assert row["num_puts"] == 2

    def test_atm_iv_uses_nearest_strike(self):
        base = {
            "expiration": "2026-08-21", "gamma": 1e-6, "delta": 0.0,
            "days_to_exp": 5, "open_interest": 100,
        }
        data = [
            {**base, "type": "CALL", "strike": 99.0, "gex": 1.0, "iv": 25.0},
            {**base, "type": "CALL", "strike": 100.0, "gex": 1.0, "iv": 30.0},
        ]
        rows = aggregate_by_expiration(data, spot=99.5)
        # Nearest strike to 99.5 is 99 -> iv 25/100 = 25%
        assert rows[0]["atm_iv"] == 0.25


class TestComputeTotals:
    def test_signs(self):
        data = [
            {"type": "CALL", "gex": 100.0},
            {"type": "PUT", "gex": -40.0},
            {"type": "PUT", "gex": -10.0},
        ]
        totals = compute_totals(data)
        assert totals == {
            "total_call_gex": 100.0,
            "total_put_gex": 50.0,
            "net_gex": 50.0,
        }