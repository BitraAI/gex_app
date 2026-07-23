#!/usr/bin/env python3
"""Test script to verify _filter_strikes_near_atm filter correctly with 20 strikes below/above ATM"""

import sys
sys.path.insert(0, '/home/spark_admin/gex_app')

from analytics import _filter_strikes_near_atm

# Create test data with strikes from -30 to +30 at 1-point spacing
test_data = []
for strike_price in range(-30, 31):
    test_data.append({
        "strike": strike_price,
        "type": "CALL" if strike_price > 0 else "PUT"
    })

# Test with spot = 0 (ATM strike should be 0)
print("Test with spot = 0 (ATM strike should be 0):")
filtered = _filter_strikes_near_atm(test_data, 0, 20)

# Group results
below_atm = [e["strike"] for e in filtered if e["strike"] < 0]
atm_strike = [e["strike"] for e in filtered if e["strike"] == 0]
above_atm = [e["strike"] for e in filtered if e["strike"] > 0]

print(f"  Strikes below ATM (< 0): {sorted(below_atm)}")
print(f"  ATM strike: {atm_strike}")
print(f"  Strikes above ATM (> 0): {sorted(above_atm)}")
print(f"  Count below ATM: {len(below_atm)} (expected 20)")
print(f"  Count above ATM: {len(above_atm)} (expected 20)")

assert len(below_atm) == 20, f"Expected 20 strikes below ATM, got {len(below_atm)}"
assert len(above_atm) == 20, f"Expected 20 strikes above ATM, got {len(above_atm)}"
assert atm_strike == [0], f"Expected ATM strike to be 0, got {atm_strike}"
print("  ✓ Test passed!\n")

# Test with spot = 25 (ATM strike should be 25)
print("Test with spot = 25 (ATM strike should be 25):")
filtered = _filter_strikes_near_atm(test_data, 25, 20)

below_atm = [e["strike"] for e in filtered if e["strike"] < 25]
atm_strike = [e["strike"] for e in filtered if e["strike"] == 25]
above_atm = [e["strike"] for e in filtered if e["strike"] > 25]

print(f"  Strikes below ATM (< 25): {sorted(below_atm)}")
print(f"  ATM strike: {atm_strike}")
print(f"  Strikes above ATM (> 25): {sorted(above_atm)}")
print(f"  Count below ATM: {len(below_atm)} (expected 20)")
print(f"  Count above ATM: {len(above_atm)} (expected 20)")

assert len(below_atm) == 20, f"Expected 20 strikes below ATM, got {len(below_atm)}"
assert len(above_atm) == 20, f"Expected 20 strikes above ATM, got {len(above_atm)}"
assert atm_strike == [25], f"Expected ATM strike to be 25, got {atm_strike}"
print("  ✓ Test passed!\n")

# Test with spot = 5 (ATM strike should be 5)
print("Test with spot = 5 (ATM strike should be 5):")
filtered = _filter_strikes_near_atm(test_data, 5, 20)

below_atm = [e["strike"] for e in filtered if e["strike"] < 5]
atm_strike = [e["strike"] for e in filtered if e["strike"] == 5]
above_atm = [e["strike"] for e in filtered if e["strike"] > 5]

print(f"  Strikes below ATM (< 5): {sorted(below_atm)}")
print(f"  ATM strike: {atm_strike}")
print(f"  Strikes above ATM (> 5): {sorted(above_atm)}")
print(f"  Count below ATM: {len(below_atm)} (expected 20)")
print(f"  Count above ATM: {len(above_atm)} (expected 20)")

assert len(below_atm) == 20, f"Expected 20 strikes below ATM, got {len(below_atm)}"
assert len(above_atm) == 20, f"Expected 20 strikes above ATM, got {len(above_atm)}"
assert atm_strike == [5], f"Expected ATM strike to be 5, got {atm_strike}"
print("  ✓ Test passed!")

print("\n✓ All tests passed!")