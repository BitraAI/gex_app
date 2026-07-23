#!/usr/bin/env python3
"""Test the _filter_strikes_near_atm from app.py"""

import sys
sys.path.insert(0, '/home/spark_admin/gex_app')

# Import from app
from app import _filter_strikes_near_atm

# Test with spot = 100, strikes from 80-120
test_data = []
for strike_price in range(80, 121):
    opt_type = "CALL" if strike_price > 100 else ("PUT" if strike_price < 100 else "ATM")
    test_data.append({
        "strike": strike_price,
        "type": opt_type,
        "spot": 100,
        "open_interest": 100,
        "gex": 100 if opt_type == "CALL" else -100,
        "call_gex": 100 if opt_type == "CALL" else 0,
        "put_gex": 100 if opt_type == "PUT" else 0,
        "iv": 0.2,
        "net_gex": 100 if opt_type == "CALL" else -100,
        "expiration": "2024-12-20",
        "days_to_exp": 90
    })

print("="*70)
print("Test _filter_strikes_near_atm from app.py")
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

print("\n" + "="*70)
print("ISSUE IDENTIFIED:")
print("="*70)
print("The app.py function returns LIMITED strikes because it only includes")
print("trades that actually exist in the data for those specific strikes!")
print("\nIn our test:")
print(f"  All strikes 80-120 exist, but some have type=ATM (neither CALL nor PUT)")
print(f"  ATM strike (100) has type='ATM', not 'CALL' or 'PUT'")
print(f"\nThis means:")
print(f"  Below strikes (80-99) are all type='PUT' -> included")
print(f"  Above strikes (101-120) are all type='CALL' -> included")
print(f"  ATM strike (100) is type='ATM' -> may be excluded if not filtered")

# Let's check what types we have
print("\n" + "="*70)
print("Type analysis:")
print("="*70)
for strike in [80, 90, 95, 99, 100, 101, 105, 110, 115, 120]:
    for item in test_data:
        if item["strike"] == strike:
            print(f"  Strike {strike}: type='{item['type']}'")
            break

print("\n" + "="*70)
print("The fix: _filter_strikes_near_atm should filter for strikes with")
print("call or put options, not just exist in data")
print("="*70)