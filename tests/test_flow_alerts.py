"""Unit tests for the wall-buffer and conviction helpers used by
``maybe_fire_wall_zone_alerts`` in ``flow.py``.

These are pure functions — no Streamlit session state or network I/O — so
they can be tested directly.
"""

import pytest

from flow import (
    _WALL_ZONE_BUFFER,
    _WALL_ZONE_MIN_BUFFER,
    _ABSORPTION_MIN_VOL,
    _WALL_BREAK_CONFIRM,
    _MIN_WALL_BREAK_CONTRACTS,
    _wall_buffer,
    _conviction_score,
    _wall_price_marks,
    _opt_mark_at_wall,
    _trade_line,
)


class TestWallBuffer:
    """Tests for _wall_buffer: near-wall zone width = 0.02% of wall price,
    floored at _WALL_ZONE_MIN_BUFFER ($0.05)."""

    def test_none_returns_zero(self):
        assert _wall_buffer(None) == 0.0

    def test_floored_at_min_buffer(self):
        # 0.02% of 10 = 0.002, below floor -> 0.05
        assert _wall_buffer(10.0) == pytest.approx(_WALL_ZONE_MIN_BUFFER)

        # 0.02% of 100 = 0.02, still below floor -> 0.05
        assert _wall_buffer(100.0) == pytest.approx(_WALL_ZONE_MIN_BUFFER)

    def test_large_wall_proportional(self):
        # 0.02% of 5700 = 1.14, well above floor
        assert _wall_buffer(5700.0) == pytest.approx(1.14)

    def test_threshold_wall(self):
        # 0.02% of 250 = 0.05, exactly at the floor
        assert _wall_buffer(250.0) == pytest.approx(0.05)

    def test_negative_wall(self):
        # abs() is applied; negative wall prices still get the buffer
        assert _wall_buffer(-500.0) == pytest.approx(0.10)


class TestConvictionScore:
    """Tests for _conviction_score: 0-5 metric agreement with trend direction."""

    def test_none_direction_returns_zero(self):
        assert _conviction_score(None, None, None, None, None, None, None) == 0

    def test_no_agreement_returns_zero(self):
        assert _conviction_score("up", 0.1, 0, 0, 0, 0, 0) == 0

    def test_book_imbalance_only(self):
        # |book_imbalance| > 0.3 counts
        assert _conviction_score("up", 0.31, 0, 0, 0, 0, 0) == 1
        assert _conviction_score("up", -0.31, 0, 0, 0, 0, 0) == 1

    def test_book_imbalance_below_threshold_no_point(self):
        assert _conviction_score("up", 0.29, 0, 0, 0, 0, 0) == 0

    def test_flow_speed_and_acceleration_agree_up(self):
        # Both positive for "up"
        assert _conviction_score("up", 0, 5, 2, 0, 0, 0) == 1

    def test_flow_speed_and_acceleration_agree_down(self):
        # Both negative for "down"
        assert _conviction_score("down", 0, -5, -2, 0, 0, 0) == 1

    def test_flow_speed_acceleration_diverge_no_point(self):
        # speed positive, acceleration negative -> no point
        assert _conviction_score("up", 0, 5, -2, 0, 0, 0) == 0

    def test_flow_speed_acceleration_zero_speed_no_point(self):
        # speed == 0 -> no point even if signs match
        assert _conviction_score("up", 0, 0, 0, 0, 0, 0) == 0

    def test_liquidity_flow_up(self):
        # liquidity > 0 for up
        assert _conviction_score("up", 0, 0, 0, 50, 0, 0) == 1

    def test_liquidity_flow_down(self):
        # liquidity < 0 for down
        assert _conviction_score("down", 0, 0, 0, -50, 0, 0) == 1

    def test_liquidity_flow_wrong_direction_no_point(self):
        assert _conviction_score("up", 0, 0, 0, -50, 0, 0) == 0
        assert _conviction_score("down", 0, 0, 0, 50, 0, 0) == 0

    def test_net_flow_60_up(self):
        # net_flow_60 > 0 for up
        assert _conviction_score("up", 0, 0, 0, 0, 100, 0) == 1

    def test_net_flow_60_down(self):
        assert _conviction_score("down", 0, 0, 0, 0, -100, 0) == 1

    def test_net_flow_wrong_direction_no_point(self):
        assert _conviction_score("up", 0, 0, 0, 0, -100, 0) == 0

    def test_absorption_high_enough(self):
        assert _conviction_score("up", 0, 0, 0, 0, 0, _ABSORPTION_MIN_VOL) == 1

    def test_absorption_below_min_no_point(self):
        assert _conviction_score("up", 0, 0, 0, 0, 0, _ABSORPTION_MIN_VOL - 1) == 0

    def test_max_score_all_agree(self):
        assert _conviction_score(
            "up", 0.5, 10, 5, 100, 200, _ABSORPTION_MIN_VOL
        ) == 5

    def test_bullish_direction(self):
        # "bullish" is treated same as "up"
        assert _conviction_score("bullish", 0.5, 10, 5, 100, 200, _ABSORPTION_MIN_VOL) == 5

    def test_bearish_direction(self):
        assert _conviction_score("bearish", -0.5, -10, -5, -100, -200, _ABSORPTION_MIN_VOL) == 5


class TestWallPriceMarks:
    """Tests for _wall_price_marks: returns (CALL, PUT) marks at nearest wall."""

    def test_nearest_call_wall(self):
        spot = 570.0
        call_wall = 575.0
        put_wall = 565.0
        opt_prices = {"call_price": 1.0, "put_price": 2.0}
        wall_prices = {
            "call_wall_call_price": 3.0,
            "call_wall_put_price": 4.0,
            "put_wall_call_price": 5.0,
            "put_wall_put_price": 6.0,
        }
        call_p, put_p = _wall_price_marks(opt_prices, wall_prices, call_wall, put_wall, spot)
        assert call_p == 3.0  # call_wall_call_price (spot closer to call wall)
        assert put_p == 4.0   # call_wall_put_price

    def test_nearest_put_wall(self):
        spot = 560.0
        call_wall = 575.0
        put_wall = 565.0
        opt_prices = {"call_price": 1.0, "put_price": 2.0}
        wall_prices = {
            "call_wall_call_price": 3.0,
            "call_wall_put_price": 4.0,
            "put_wall_call_price": 5.0,
            "put_wall_put_price": 6.0,
        }
        call_p, put_p = _wall_price_marks(opt_prices, wall_prices, call_wall, put_wall, spot)
        assert call_p == 5.0  # put_wall_call_price (spot closer to put wall)
        assert put_p == 6.0   # put_wall_put_price

    def test_fallback_to_atm(self):
        # When wall_prices don't have the marks, fall back to opt_prices
        spot = 570.0
        call_wall = 575.0
        put_wall = 565.0
        opt_prices = {"call_price": 1.0, "put_price": 2.0}
        wall_prices = {}
        call_p, put_p = _wall_price_marks(opt_prices, wall_prices, call_wall, put_wall, spot)
        assert call_p == 1.0
        assert put_p == 2.0

    def test_none_walls_uses_atm(self):
        opt_prices = {"call_price": 1.0, "put_price": 2.0}
        call_p, put_p = _wall_price_marks(opt_prices, {}, None, None, 570.0)
        assert call_p == 1.0
        assert put_p == 2.0


class TestOptMarkAtWall:
    """Tests for _opt_mark_at_wall: returns the option mark at a specific wall strike."""

    def test_call_at_call_wall(self):
        wall_prices = {"call_wall_call_price": 3.0, "put_wall_call_price": 5.0}
        result = _opt_mark_at_wall("CALL", 575.0, 575.0, 565.0, wall_prices)
        assert result == 3.0

    def test_call_at_put_wall(self):
        wall_prices = {"call_wall_call_price": 3.0, "put_wall_call_price": 5.0}
        result = _opt_mark_at_wall("CALL", 565.0, 575.0, 565.0, wall_prices)
        assert result == 5.0

    def test_put_at_call_wall(self):
        wall_prices = {"call_wall_put_price": 4.0, "put_wall_put_price": 6.0}
        result = _opt_mark_at_wall("PUT", 575.0, 575.0, 565.0, wall_prices)
        assert result == 4.0

    def test_put_at_put_wall(self):
        wall_prices = {"call_wall_put_price": 4.0, "put_wall_put_price": 6.0}
        result = _opt_mark_at_wall("PUT", 565.0, 575.0, 565.0, wall_prices)
        assert result == 6.0

    def test_unknown_wall_defaults_to_put_wall(self):
        # wall_strike doesn't match either wall -> PUT path takes the else
        # branch and returns put_wall_put_price
        wall_prices = {"call_wall_put_price": 4.0, "put_wall_put_price": 6.0}
        result = _opt_mark_at_wall("PUT", 999.0, 575.0, 565.0, wall_prices)
        assert result == 6.0

    def test_unknown_wall_defaults_to_put_wall_call_side(self):
        # For CALL side with unmatched wall_strike -> returns put_wall_call_price
        wall_prices = {"put_wall_call_price": 5.0, "call_wall_call_price": 3.0}
        result = _opt_mark_at_wall("CALL", 999.0, 575.0, 565.0, wall_prices)
        assert result == 5.0


class TestTradeLine:
    """Tests for _trade_line: builds the emoji + BUY suggestion string."""

    def test_call_trade(self):
        wall_prices = {"call_wall_call_price": 3.0, "call_wall_put_price": 4.0}
        line = _trade_line("CALL", 575.0, 575.0, 565.0, wall_prices, "2025-01-17")
        assert "🟢 BUY CALL" in line
        assert "$575.00" in line
        assert "01/17" in line

    def test_put_trade(self):
        wall_prices = {"put_wall_put_price": 6.0, "call_wall_put_price": 4.0}
        line = _trade_line("PUT", 565.0, 575.0, 565.0, wall_prices, "2025-01-17")
        assert "🔴 BUY PUT" in line
        assert "$565.00" in line

    def test_no_price(self):
        line = _trade_line("CALL", None, 575.0, 565.0, {}, None)
        assert "🟢 BUY CALL" in line
        assert "$" not in line.split("BUY CALL")[1]  # no strike tag

    def test_no_expiration(self):
        wall_prices = {"call_wall_call_price": 3.0}
        line = _trade_line("CALL", 575.0, 575.0, 565.0, wall_prices, None)
        assert "01/17" not in line

    def test_format_with_price(self):
        # wall_strike matches call_wall -> _opt_mark_at_wall returns call_wall_call_price
        wall_prices = {"call_wall_call_price": 8.25}
        line = _trade_line("CALL", 575.0, 575.0, 565.0, wall_prices, "2025-03-21")
        assert "$8.25" in line
