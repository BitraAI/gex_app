#!/usr/bin/env python3
"""Final verification - the fix works correctly!"""

import sys
sys.path.insert(0, '/home/spark_admin/gex_app')

from calculations import parse_option_chain

def create_robust_test_data(spot=100):
    """Create test data with MORE strikes than needed (20 below, 20 above ATM)"""
    
    raw = {
        "underlying": {"mark": spot},
        "callExpDateMap": {},
        "putExpDateMap": {}
    }
    
    expiration_date = "2024-12-20"
    exp_key = f"{expiration_date}:0"
    
    # Create at least 20 strikes BELOW ATM (strikes < 100)
    # We'll make it 25 for good measure
    for strike in range(75, 100):
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
                "delta": -0.5,
                "gamma": 0.03,
                "theta": -0.05,
                "vega": 0.10,
                "rho": 0.05,
            }
        ]
    
    # ATM strike (100)
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
    
    # Create at least 20 strikes ABOVE ATM (strikes > 100)
    # We'll make it 25 for good measure
    for strike in range(101, 126):
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
                "delta": 0.5,
                "gamma": 0.03,
                "theta": -0.05,
                "vega": 0.10,
                "rho": 0.05,
            }
        ]
    
    return raw

def main():
    print("="*70)
    print("Final Verification - Fix is Correct!")
    print("="*70)
    
    # Parse data with ample strikes
    raw = create_robust_test_data(spot=100)
    data, spot = parse_option_chain(raw)
    
    print(f"\nSpot: {spot}")
    print(f"Total option entries: {len(data)}")
    
    # Group strikes
    strikes = sorted(set(e['strike'] for e in data))
    print(f"\nAll unique strikes: {strikes[:10]}...{strikes[-10:]}")
    
    # Test _filter_strikes_near_atm
    print("\n" + "="*70)
    print("_filter_strikes_near_atm Test")
    print("="*70)
    
    # Import from app (which now has the fixed version)
    from app import _filter_strikes_near_atm
    
    filtered_data = _filter_strikes_near_atm(data, spot, n=20)
    
    # Count strikes
    below = len([e for e in filtered_data if e['strike'] < spot])
    atm = len([e for e in filtered_data if e['strike'] == spot])
    above = len([e for e in filtered_data if e['strike'] > spot])
    
    print(f"\n_filtered_strikes_near_atm result:")
    print(f"  Below ATM (< 100): {below} strikes")
    print(f"  ATM (= 100): {atm} strikes")
    print(f"  Above ATM (> 100): {above} strikes")
    
    # Check filtered_data contents
    filtered_strikes = sorted(set(e['strike'] for e in filtered_data))
    print(f"\nFiltered strikes: {filtered_strikes}")
    
    # Verify ordering
    print("\n" + "="*70)
    print("Ordering Verification")
    print("="*70)
    
    # Check that strikes are in distance order from ATM
    # Below strikes should be 99, 98, ..., 80
    expected_below = list(range(99, 79, -1))
    filtered_below = [e['strike'] for e in filtered_data if e['strike'] < spot]
    
    print(f"\nStrikes below ATM:")
    print(f"  Expected (distance-based): {expected_below}")
    print(f"  Got: {filtered_below}")
    print(f"  Match: {filtered_below == expected_below}")
    
    # Above strikes should be 101, 102, ..., 120
    expected_above = list(range(101, 121))
    filtered_above = [e['strike'] for e in filtered_data if e['strike'] > spot]
    
    print(f"\nStrikes above ATM:")
    print(f"  Expected (distance-based): {expected_above}")
    print(f"  Got: {filtered_above}")
    print(f"  Match: {filtered_above == expected_above}")
    
    # ATM
    filtered_atm = [e['strike'] for e in filtered_data if e['strike'] == spot]
    print(f"\nATM strike: {filtered_atm}")
    
    # Verify the fix works
    print("\n" + "="*70)
    print("Fix Verification")
    print("="*70)
    
    all_passed = True
    
    # Test 1: 20 strikes below
    if len(filtered_below) == 20:
        print(f"✅ Test 1 PASSED: Exactly 20 strikes below ATM")
    else:
        print(f"❌ Test 1 FAILED: Expected 20 strikes below ATM, got {len(filtered_below)}")
        all_passed = False
    
    # Test 2: 1 ATM strike
    if len(filtered_atm) == 1 and filtered_atm[0] == 100:
        print(f"✅ Test 2 PASSED: Exactly 1 ATM strike (strike=100)")
    else:
        print(f"❌ Test 2 FAILED: Expected 1 ATM strike (strike=100), got {filtered_atm}")
        all_passed = False
    
    # Test 3: 20 strikes above
    if len(filtered_above) == 20:
        print(f"✅ Test 3 PASSED: Exactly 20 strikes above ATM")
    else:
        print(f"❌ Test 3 FAILED: Expected 20 strikes above ATM, got {len(filtered_above)}")
        all_passed = False
    
    # Test 4: Total 41 strikes
    if len(filtered_below) + len(filtered_atm) + len(filtered_above) == 41:
        print(f"✅ Test 4 PASSED: Total 41 strikes (20+1+20)")
    else:
        print(f"❌ Test 4 FAILED: Expected 41 total strikes, got {len(filtered_below) + len(filtered_atm) + len(filtered_above)}")
        all_passed = False
    
    # Test 5: Ordering (distance-based)
    if filtered_below == expected_below and filtered_above == expected_above:
        print(f"✅ Test 5 PASSED: Strikes ordered by distance from ATM")
    else:
        print(f"❌ Test 5 FAILED: Strikes not ordered by distance from ATM")
        all_passed = False
    
    # Test 6: Check that we got enough strikes in the original data
    # The original data has strikes 75-99 (25 below), 100 (1), 101-125 (25 above)
    # So we should have: 25 below -> 25 selected, 1 ATM, 25 above -> 25 selected
    # But we only asked for 20 below and 20 above
    
    print("\n" + "="*70)
    if all_passed:
        print("SUCCESS! Fix is working correctly!")
        print("="*70)
        print("\nThe fix correctly:")
        print("1. ✅ Selects EXACTLY 20 strikes BELOW ATM")
        print("2. ✅ Selects exactly 1 ATM strike")
        print("3. ✅ Selects EXACTLY 20 strikes ABOVE ATM")
        print("4. ✅ Orders strikes by distance from ATM")
        print("5. ✅ Returns total of 41 strikes")
        print("\nThis ensures the ATM Order Flow support/resistance columns")
        print("will display the correct data in the UI!")
    else:
        print("FAILURE! Fix has issues")
        print("="*70)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)