#!/usr/bin/env python3
"""Verify the main fix: filtered_flow_data returns correct strike distribution"""

import sys
sys.path.insert(0, '/home/spark_admin/gex_app')

from analytics import get_filtered_strikes_for_analysis
from calculations import parse_option_chain

def create_simple_test_data(spot=100):
    """Create simple test data with strikes 90-110"""
    
    raw = {
        "underlying": {"mark": spot},
        "callExpDateMap": {},
        "putExpDateMap": {}
    }
    
    expiration_date = "2024-12-20"
    exp_key = f"{expiration_date}:0"
    
    # Strikes 90-99 (PUT options)
    for strike in range(90, 100):
        raw["putExpDateMap"][exp_key] = raw["putExpDateMap"].get(exp_key, {})
        raw["putExpDateMap"][exp_key][str(strike)] = [
            {
                "putCall": "PUT",
                "strike": strike,
                "last": 5.0,
                "bid": 4.9,
                "ask": 5.1,
                "mark": 5.0,
                "openInterest": 100,
                "totalVolume": 1000,
                "volatility": 0.22,
                "delta": -0.5 - ((strike - 90) * 0.01),
                "gamma": 0.03,
                "theta": -0.05,
                "vega": 0.10,
                "rho": 0.05,
            }
        ]
    
    # Strike 100 (ATM)
    raw["callExpDateMap"][exp_key] = raw["callExpDateMap"].get(exp_key, {})
    raw["callExpDateMap"][exp_key]["100"] = [
        {
            "putCall": "CALL",
            "strike": 100,
            "last": 5.0,
            "bid": 4.9,
            "ask": 5.1,
            "mark": 5.0,
            "openInterest": 100,
            "totalVolume": 1000,
            "volatility": 0.22,
            "delta": 0.5,
            "gamma": 0.03,
            "theta": -0.05,
            "vega": 0.10,
            "rho": 0.05,
        }
    ]
    
    # Strikes 101-110 (CALL options)
    for strike in range(101, 111):
        raw["callExpDateMap"][exp_key] = raw["callExpDateMap"].get(exp_key, {})
        raw["callExpDateMap"][exp_key][str(strike)] = [
            {
                "putCall": "CALL",
                "strike": strike,
                "last": 5.0,
                "bid": 4.9,
                "ask": 5.1,
                "mark": 5.0,
                "openInterest": 100,
                "totalVolume": 1000,
                "volatility": 0.22,
                "delta": 0.5 + ((strike - 100) * 0.01),
                "gamma": 0.03,
                "theta": -0.05,
                "vega": 0.10,
                "rho": 0.05,
            }
        ]
    
    return raw

def main():
    print("="*70)
    print("Verify Main Fix: filtered_flow_data Strike Distribution")
    print("="*70)
    
    # Parse data
    raw = create_simple_test_data(spot=100)
    data, spot = parse_option_chain(raw)
    
    print(f"\nSpot: {spot}")
    print(f"Total unique strikes in data: {len(set(e['strike'] for e in data))}")
    
    # Get unique strikes
    strikes = sorted(set(e['strike'] for e in data))
    print(f"Strikes: {strikes}")
    
    # Test _filter_strikes_near_atm from app.py
    print("\n" + "="*70)
    print("Test _filter_strikes_near_atm (app.py logic)")
    print("="*70)
    
    # We can't easily import app.py's function, so we'll test the logic
    from analytics import _filter_strikes_near_atm as analytics_filter
    filtered_data = analytics_filter(data, spot, n=20)
    
    # Count strikes
    below = len([e for e in filtered_data if e['strike'] < spot])
    atm = len([e for e in filtered_data if e['strike'] == spot])
    above = len([e for e in filtered_data if e['strike'] > spot])
    
    print(f"\n_filtered_strikes_near_atm (analytics.py) result:")
    print(f"  Below ATM (< 100): {below} strikes")
    print(f"  ATM (= 100): {atm} strikes")
    print(f"  Above ATM (> 100): {above} strikes")
    
    # Now test get_filtered_strikes_for_analysis
    print("\n" + "="*70)
    print("Test get_filtered_strikes_for_analysis")
    print("="*70)
    
    filtered_flow_data = get_filtered_strikes_for_analysis(data, spot, n=20)
    
    print(f"\nFiltered flow data length: {len(filtered_flow_data)}")
    
    # Count strikes in filtered_flow_data
    strikes_below = [r[0] for r in filtered_flow_data if r[0] < spot]
    strikes_atm = [r[0] for r in filtered_flow_data if r[0] == spot]
    strikes_above = [r[0] for r in filtered_flow_data if r[0] > spot]
    
    print(f"\nFiltered flow data strike distribution:")
    print(f"  Below ATM (< 100): {len(strikes_below)} strikes")
    print(f"    Examples: {strikes_below[:10]}{'...' if len(strikes_below) > 10 else ''}")
    print(f"  ATM (= 100): {len(strikes_atm)} strikes")
    print(f"    ATM strike: {strikes_atm[0] if strikes_atm else 'None'}")
    print(f"  Above ATM (> 100): {len(strikes_above)} strikes")
    print(f"    Examples: {strikes_above[:10]}{'...' if len(strikes_above) > 10 else ''}")
    
    # Verify the fix
    print("\n" + "="*70)
    print("VERIFICATION")
    print("="*70)
    
    success = True
    
    if len(strikes_below) != 20:
        print(f"❌ FAIL: Expected exactly 20 strikes below ATM, got {len(strikes_below)}")
        success = False
    else:
        print(f"✅ PASS: Exactly 20 strikes below ATM")
    
    if len(strikes_atm) != 1:
        print(f"❌ FAIL: Expected exactly 1 ATM strike, got {len(strikes_atm)}")
        success = False
    else:
        print(f"✅ PASS: Exactly 1 ATM strike")
    
    if len(strikes_above) != 20:
        print(f"❌ FAIL: Expected exactly 20 strikes above ATM, got {len(strikes_above)}")
        success = False
    else:
        print(f"✅ PASS: Exactly 20 strikes above ATM")
    
    # Verify the order (should be distance-based)
    print(f"\nVerifying strike order (distance from ATM):")
    
    # Check that strikes below are in order of distance from ATM
    expected_below = list(range(99, 79, -1))  # 99, 98, ..., 80
    if strikes_below == expected_below:
        print(f"✅ PASS: Strikes below ATM in correct distance order")
    else:
        print(f"❌ FAIL: Strikes below ATM not in correct order")
        print(f"  Expected: {expected_below}")
        print(f"  Got: {strikes_below}")
        success = False
    
    # Check that strikes above are in order of distance from ATM
    expected_above = list(range(101, 121))  # 101, 102, ..., 120
    if strikes_above == expected_above:
        print(f"✅ PASS: Strikes above ATM in correct distance order")
    else:
        print(f"❌ FAIL: Strikes above ATM not in correct order")
        print(f"  Expected: {expected_above}")
        print(f"  Got: {strikes_above}")
        success = False
    
    # Verify total
    if len(strikes_below) + len(strikes_atm) + len(strikes_above) != 41:
        print(f"❌ FAIL: Expected total 41 strikes, got {len(strikes_below) + len(strikes_atm) + len(strikes_above)}")
        success = False
    else:
        print(f"✅ PASS: Total strikes = {len(strikes_below) + len(strikes_atm) + len(strikes_above)} (expected 41)")
    
    print("\n" + "="*70)
    if success:
        print("SUCCESS! All requirements met!")
        print("="*70)
        print("\nThe fix correctly ensures:")
        print("  1. Exactly 20 strikes BELOW ATM")
        print("  2. Exactly 1 ATM strike")
        print("  3. Exactly 20 strikes ABOVE ATM")
        print("  4. Strikes ordered by distance from ATM")
        print("  5. Total of 41 strikes")
        print("\nThis ensures the ATM Order flow support and resistance columns")
        print("will display correctly in the UI!")
    else:
        print("FAILURE! Some requirements not met.")
        print("="*70)
    
    return success

if __name__ == "__main__":
    exit(0 if main() else 1)