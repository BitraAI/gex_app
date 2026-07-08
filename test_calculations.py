import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from calculations import (
    calculate_gex,
    calculate_atm_strike,
    get_strike_spacing,
    _parse_exp_key,
    compute_totals,
    aggregate_by_strike,
    aggregate_by_expiration,
    dealer_position,
)


class TestGEXCalculations(unittest.TestCase):

    def setUp(self):
        self.spot = 500.0
        self.sample_calls = [
            {"strike": 490, "expiration": "2026-07-17", "type": "CALL",
             "gamma": 0.05, "delta": 0.6, "vega": 0.2, "theta": -0.1,
             "iv": 0.25, "open_interest": 10000, "volume": 5000, "mark": 15.0,
              "gex": 0.0, "vex": 0.0, "cex": 0.0, "days_to_exp": 22, "spot": 500.0},
            {"strike": 500, "expiration": "2026-07-17", "type": "CALL",
             "gamma": 0.08, "delta": 0.5, "vega": 0.3, "theta": -0.15,
             "iv": 0.22, "open_interest": 20000, "volume": 8000, "mark": 10.0,
             "gex": 0.0, "vex": 0.0, "cex": 0.0, "days_to_exp": 22, "spot": 500.0},
            {"strike": 510, "expiration": "2026-07-17", "type": "CALL",
             "gamma": 0.03, "delta": 0.3, "vega": 0.15, "theta": -0.05,
             "iv": 0.28, "open_interest": 5000, "volume": 2000, "mark": 5.0,
             "gex": 0.0, "vex": 0.0, "cex": 0.0, "days_to_exp": 22, "spot": 500.0},
        ]
        self.sample_puts = [
            {"strike": 490, "expiration": "2026-07-17", "type": "PUT",
             "gamma": 0.04, "delta": -0.4, "vega": 0.18, "theta": -0.08,
             "iv": 0.26, "open_interest": 8000, "volume": 4000, "mark": 8.0,
             "gex": 0.0, "vex": 0.0, "cex": 0.0, "days_to_exp": 22, "spot": 500.0},
            {"strike": 500, "expiration": "2026-07-17", "type": "PUT",
             "gamma": 0.07, "delta": -0.5, "vega": 0.28, "theta": -0.12,
             "iv": 0.23, "open_interest": 15000, "volume": 6000, "mark": 12.0,
             "gex": 0.0, "vex": 0.0, "cex": 0.0, "days_to_exp": 22, "spot": 500.0},
        ]
        self.data = self.sample_calls + self.sample_puts

        # Pre-calculate GEX for each entry
        for entry in self.data:
            gex = calculate_gex(entry["gamma"], entry["open_interest"], self.spot)
            if entry["type"] == "PUT":
                gex = -abs(gex)
            entry["gex"] = gex

    def test_calculate_gex_call(self):
        gex = calculate_gex(0.05, 10000, 500.0)
        expected = 0.05 * 10000 * 100 * (500 ** 2) * 0.01
        self.assertAlmostEqual(gex, expected)

    def test_calculate_gex_zero_oi(self):
        gex = calculate_gex(0.05, 0, 500.0)
        self.assertEqual(gex, 0.0)

    def test_calculate_gex_zero_spot(self):
        gex = calculate_gex(0.05, 10000, 0.0)
        self.assertEqual(gex, 0.0)

    def test_calculate_atm_strike(self):
        self.assertEqual(calculate_atm_strike(505.0), 505.0)
        self.assertEqual(calculate_atm_strike(502.3), 500.0)
        self.assertEqual(calculate_atm_strike(15.5), 15.5)

    def test_get_strike_spacing(self):
        self.assertEqual(get_strike_spacing(3.0), 0.5)
        self.assertEqual(get_strike_spacing(15.0), 0.5)
        self.assertEqual(get_strike_spacing(100.0), 1.0)
        self.assertEqual(get_strike_spacing(300.0), 2.5)
        self.assertEqual(get_strike_spacing(700.0), 5.0)
        self.assertEqual(get_strike_spacing(2000.0), 10.0)

    def test_parse_exp_key(self):
        self.assertEqual(_parse_exp_key("2026-07-17:0"), "2026-07-17")
        self.assertEqual(_parse_exp_key("2026-07-17:15"), "2026-07-17")
        self.assertEqual(_parse_exp_key("2026-07-17"), "2026-07-17")

    def test_compute_totals(self):
        totals = compute_totals(self.data)
        self.assertIn("total_call_gex", totals)
        self.assertIn("total_put_gex", totals)
        self.assertIn("net_gex", totals)
        self.assertGreater(totals["total_call_gex"], 0)
        self.assertGreater(totals["total_put_gex"], 0)

    def test_aggregate_by_strike(self):
        strikes = aggregate_by_strike(self.data, self.spot)
        self.assertGreater(len(strikes), 0)
        for s in strikes:
            self.assertIn("strike", s)
            self.assertIn("net_gex", s)
            self.assertIn("call_gex", s)
            self.assertIn("put_gex", s)
            self.assertIn("net_cex", s)
            self.assertIn("call_cex", s)
            self.assertIn("put_cex", s)

    def test_aggregate_by_expiration(self):
        by_exp = aggregate_by_expiration(self.data)
        self.assertGreater(len(by_exp), 0)
        for e in by_exp:
            self.assertIn("expiration", e)
            self.assertIn("net_gex", e)

    def test_dealer_position_long_gamma(self):
        call_data = self.sample_calls[:]
        for entry in call_data:
            gex = calculate_gex(entry["gamma"], entry["open_interest"], self.spot)
            entry["gex"] = gex
            entry["type"] = "CALL"
        pos = dealer_position(call_data, self.spot)
        self.assertEqual(pos, "Long Gamma")

    def test_dealer_position_short_gamma(self):
        put_data = self.sample_puts[:]
        for entry in put_data:
            gex = -abs(calculate_gex(entry["gamma"], entry["open_interest"], self.spot))
            entry["gex"] = gex
            entry["type"] = "PUT"
        pos = dealer_position(put_data, self.spot)
        self.assertEqual(pos, "Short Gamma")


if __name__ == "__main__":
    unittest.main()
