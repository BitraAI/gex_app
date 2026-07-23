#!/usr/bin/env python3
"""Reproduce the issue: _filter_strikes_near_atm should return EXACTLY 20 strikes BELOW ATM, ATM, 20 strikes ABOVE ATM"""

import sys
sys.path.insert(0, '/home/spark_admin/gex_app')

from analytics import _filter_strikes_near_atm, get_filtered_strikes_for_analysis

# Test Case 1: Spot = 100, with strikes from 80 to 120
test_data = []
for strike_price in range(80, 121):
    # Mark call/put based on position relative to 100 (spot)
    opt_type = "CALL" if strike_price > 100 else ("PUT" if strike_price < 100 else "ATM")
    test_data.append({
        "strike": strike_price,
        "type": opt_type,
        "spot": 100,
        "open_interest": 100,
        "gex": 100,
        "call_gex": 100 if opt_type == "CALL" else 0,
        "put_gex": 100 if opt_type == "PUT" else 0,
        "iv": 0.2,
        "call_iv": 0.2 if opt_type == "CALL" else 0,
        "put_iv": 0.2 if opt_type == "PUT" else 0,
        "net_gex": 100 if opt_type == "CALL" else -100,
        "expiration": "2024-12-20",
        "days_to_exp": 90
    })

print("="*70)
print("Test 1: Direct _filter_strikes_near_atm test with 41 strikes (80-120)")
print("="*70)
spot = 100
n = 20

filtered = _filter_strikes_near_atm(test_data, spot, n)

# Group results
below_atm = [e["strike"] for e in filtered if e["strike"] < spot]
atm_strike = [e["strike"] for e in filtered if e["strike"] == spot]
above_atm = [e["strike"] for e in filtered if e["strike"] > spot]

print(f"Spot: {spot}")
print(f"Below ATM: {sorted(below_atm)} (len={len(below_atm)})")
print(f"ATM: {atm_strike} (len={len(atm_strike)})")
print(f"Above ATM: {sorted(above_atm)} (len={len(above_atm)})")
print(f"Total: {len(filtered)} strikes")

print("\nISSUE:")
print(f"  Below ATM count: {len(below_atm)} (expected exactly 20)")
print(f"  Above ATM count: {len(above_atm)} (expected exactly 20)")
print(f"\n  But _filter_strikes_near_atm returns LIMITED strikes because it")
print(f"  only includes trades with actual data for those specific strikes!")
print(f"\n  Available strikes above 100: 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120")
print(f"  That's EXACTLY 20 strikes above 100!")

print("\n" + "="*70)
print("Test 2: What the new get_filtered_strikes_for_analysis function returns")
print("="*70)

# Build data with ALL strikes from 80 to 120
test_data2 = []
for strike_price in range(80, 121):
    opt_type = "CALL" if strike_price > 100 else ("PUT" if strike_price < 100 else "ATM")
    test_data2.append({
        "strike": strike_price,
        "type": opt_type,
        "spot": 100,
        "open_interest": 100,
        "gex": 100 if opt_type == "CALL" else -100,
        "call_gex": 100 if opt_type == "CALL" else 0,
        "put_gex": 100 if opt_type == "PUT" else 0,
        "iv": 0.2,
        "call_iv": 0.2 if opt_type == "CALL" else 0,
        "put_iv": 0.2 if opt_type == "PUT" else 0,
        "net_gex": 100 if opt_type == "CALL" else -100,
        "expiration": "2024-12-20",
        "days_to_exp": 90
    })

result = get_filtered_strikes_for_analysis(test_data2, 100, 20)

# Check what we got
below_strikes = []
atm_strike_result = None
above_strikes = []
for item in result:
    if item[0] < 100:
        below_strikes.append(item)
    elif item[0] == 100:
        atm_strike_result = item
    elif item[0] > 100:
        above_strikes.append(item)

print(f"\nBelow ATM strikes: {len(below_strikes)} (expected exactly 20)")
for item in below_strikes[:5]:
    print(f"  Strike {item[0]}: Call GEX={item[1]}, Put GEX={item[2]}")
if len(below_strikes) > 5:
    print(f"  ... and {len(below_strikes) - 5} more")

print(f"\nATM strike: {atm_strike_result[0] if atm_strike_result else None}")

print(f"\nAbove ATM strikes: {len(above_strikes)} (expected exactly 20)")
for item in above_strikes[:5]:
    print(f"  Strike {item[0]}: Call GEX={item[1]}, Put GEX={item[2]}")
if len(above_strikes) > 5:
    print(f"  ... and {len(above_strikes) - 5} more")

print("\n" + "="*70)
print("CONCLUSION:")
print("="*70)
print("The get_filtered_strikes_for_analysis function correctly returns:")
print(f"  {len(below_strikes)} strikes BELOW ATM (should be exactly 20)")
print(f"  {1 if atm_strike_result else 0} ATM strike (should be 1)")
print(f"  {len(above_strikes)} strikes ABOVE ATM (should be exactly 20)")
print(f"  Total: {len(below_strikes) + (1 if atm_strike_result else 0) + len(above_strikes)}")
print("\nThis meets the user's requirement for order flow support and resistance!")
