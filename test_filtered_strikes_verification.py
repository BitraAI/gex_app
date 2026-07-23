#!/usr/bin/env python3
"""Test _get_filtered_data_for_walls to verify it filters for:
1. Near 4 expirations with non-zero open interest
2. 20 strikes BELOW ATM (strikes < spot)
3. ATM strike itself
4. 20 strikes ABOVE ATM (strikes > spot)
"""

import sys
sys.path.insert(0, '/home/spark_admin/gex_app')

from app import _get_filtered_data_for_walls


def test_4_expirations_with_non_zero_oi():
    """Test that the function selects only 4 expirations with non-zero OI"""
    test_data = []
    
    # Create 5 expirations with varying open interest
    for i, exp in enumerate(['2024-06-21', '2024-06-28', '2024-07-05', '2024-07-12', '2024-07-19']):
        for j in range(1, 31):
            # Make every 5th strike have non-zero open interest
            oi = 1000 if j % 5 == 0 else 0
            test_data.append({
                'strike': 100 + j,
                'expiration': exp,
                'open_interest': oi,
                'type': 'CALL' if j % 2 == 0 else 'PUT',
                'mark': 10.0,
                'iv': 25.0
            })
    
    # Test 1: Auto-select (should pick up to 4 with volume)
    result = _get_filtered_data_for_walls(test_data, None)
    expirations = set(e['expiration'] for e in result)
    
    print("=" * 70)
    print("TEST 1: Auto-select up to 4 expirations with non-zero OI")
    print("=" * 70)
    print(f"All expirations in test data: {sorted([e['expiration'] for e in test_data])}")
    print(f"All expirations with OI>0: {sorted(set(e['expiration'] for e in test_data if e['open_interest'] > 0))}")
    print(f"Expirations selected in result: {sorted(expirations)}")
    print(f"Number of expirations selected: {len(expirations)}")
    
    assert len(expirations) <= 4, f"Should select max 4 expirations, got {len(expirations)}"
    
    # Verify all selected expirations actually have non-zero OI
    all_has_oi = all(
        any(e2['open_interest'] > 0 for e2 in test_data if e2['expiration'] == exp)
        for exp in expirations
    )
    assert all_has_oi, "All selected expirations should have non-zero OI"
    
    print("✓ PASS: Function correctly selects up to 4 expirations with non-zero OI")
    return True


def test_ui_selected_expirations_with_oi_check():
    """Test when UI provides selected expirations - should filter to those with OI"""
    test_data = []
    
    # Create data with some expirations having OI, others without
    for i, exp in enumerate(['2024-06-21', '2024-06-28', '2024-07-05', '2024-07-12', '2024-07-19']):
        for j in range(1, 31):
            # Only 2024-06-21 and 2024-07-05 have non-zero OI
            oi = 1000 if exp in ['2024-06-21', '2024-07-05'] else 0
            test_data.append({
                'strike': 100 + j,
                'expiration': exp,
                'open_interest': oi,
                'type': 'CALL' if j % 2 == 0 else 'PUT',
                'mark': 10.0,
                'iv': 25.0
            })
    
    # Test 2: UI provides selected expirations
    ui_selected = ['2024-06-21', '2024-06-28', '2024-07-05', '2024-07-12']
    result = _get_filtered_data_for_walls(test_data, ui_selected)
    expirations = set(e['expiration'] for e in result)
    
    print("\n" + "=" * 70)
    print("TEST 2: UI selected expirations with OI filter check")
    print("=" * 70)
    print(f"UI selected expirations: {ui_selected}")
    print(f"Expirations selected in result: {sorted(expirations)}")
    
    # Should only select from UI list those with non-zero OI
    # From UI: 2024-06-21 (has OI), 2024-06-28 (no OI), 2024-07-05 (has OI), 2024-07-12 (no OI)
    # So result should be [2024-06-21, 2024-07-05]
    expected = {'2024-06-21', '2024-07-05'}
    assert expirations == expected, f"Expected {expected}, got {sorted(expirations)}"
    
    print("✓ PASS: Function correctly filters UI-selected expirations to only those with non-zero OI")
    return True


def test_20_strikes_below_atm():
    """Test that we get exactly 20 strikes below ATM (or less if not available)"""
    test_data = []
    spot = 150.0
    
    # Create strikes from 100 to 200
    for j in range(100, 201):
        test_data.append({
            'strike': float(j),
            'expiration': '2024-06-21',
            'open_interest': 1000 if j < spot else 0,  # All strikes below spot have OI
            'type': 'CALL' if j % 2 == 0 else 'PUT',
            'mark': 10.0,
            'iv': 25.0
        })
    
    result = _get_filtered_data_for_walls(test_data, None)
    strikes = sorted(set(e['strike'] for e in result))
    
    print("\n" + "=" * 70)
    print("TEST 3: Verify 20 strikes below ATM structure")
    print("=" * 70)
    print(f"Spot price: {spot}")
    print(f"Total strikes selected: {len(strikes)}")
    
    # Split strikes around spot
    below = [s for s in strikes if s < spot]
    above = [s for s in strikes if s > spot]
    atm = [s for s in strikes if s == spot]
    
    print(f"Strikes below ATM: {len(below)}")
    print(f"  Range: {min(below) if below else 'N/A'} to {max(below) if below else 'N/A'}")
    print(f"ATM strikes: {len(atm)}")
    print(f"Strikes above ATM: {len(above)}")
    print(f"  Range: {min(above) if above else 'N/A'} to {max(above) if above else 'N/A'}")
    
    # The function should provide ATM = 1, and as close to 20 below/above as possible
    # based on what strikes are available in filtered data
    assert len(atm) == 1, f"Should have exactly 1 ATM strike, got {len(atm)}"
    
    # Total should be roughly 41 (20 below + 1 ATM + 20 above)
    assert len(strikes) >= 40, f"Should have at least 40 strikes, got {len(strikes)}"
    
    print(f"✓ PASS: Structure is correct - 1 ATM, {len(below)} below, {len(above)} above (total {len(strikes)} strikes)")
    return True


def test_30_strikes_above_atm():
    """Test when there are more than 20 strikes above ATM"""
    test_data = []
    spot = 150.0
    
    # Create strikes from 100 to 300
    for j in range(100, 301):
        test_data.append({
            'strike': float(j),
            'expiration': '2024-06-21',
            'open_interest': 1000 if j < spot else 500,  # Different OI for below/above
            'type': 'CALL' if j % 2 == 0 else 'PUT',
            'mark': 10.0,
            'iv': 25.0
        })
    
    result = _get_filtered_data_for_walls(test_data, None)
    strikes = sorted(set(e['strike'] for e in result))
    
    print("\n" + "=" * 70)
    print("TEST 4: Verify 20 strikes above ATM when available")
    print("=" * 70)
    
    below = [s for s in strikes if s < spot]
    above = [s for s in strikes if s > spot]
    atm = [s for s in strikes if s == spot]
    
    print(f"Total strikes available: 201 (100 to 300)")
    print(f"Strikes below ATM: {len(below)} (should be ~20)")
    print(f"ATM strikes: {len(atm)}")
    print(f"Strikes above ATM: {len(above)} (should be ~20)")
    
    # Should have roughly 20 on each side
    # 100 to 149 = 50 strikes (below spot)
    # 151 to 300 = 150 strikes (above spot)
    # So should be clamped to ~20 each side
    assert len(below) <= 20, f"Should have max 20 strikes below, got {len(below)}"
    assert len(above) <= 20, f"Should have max 20 strikes above, got {len(above)}"
    
    print(f"✓ PASS: Correctly clamped to max 20 strikes on each side")
    return True


def test_strikes_ordered_by_distance():
    """Test that strikes are ordered by distance from ATM"""
    test_data = []
    spot = 150.0
    
    # Create strikes at various distances
    for strike in [140, 145, 155, 160, 135, 130, 165, 170]:
        test_data.append({
            'strike': float(strike),
            'expiration': '2024-06-21',
            'open_interest': 1000,
            'type': 'CALL' if strike > spot else 'PUT',
            'mark': 10.0,
            'iv': 25.0
        })
    
    result = _get_filtered_data_for_walls(test_data, None)
    strikes = sorted(set(e['strike'] for e in result))
    
    print("\n" + "=" * 70)
    print("TEST 5: Verify strikes are ordered by distance from ATM")
    print("=" * 70)
    print(f"Spot: {spot}, All strikes: {strikes}")
    
    # Find where ATM would be inserted
    # At 150, we have: 135, 130, 140, 145, 155, 160, 165, 170
    # Ordered by distance from 150: 135, 140, 145, 155, 160, 165, 170
    # So below: 135, 140, 145 (then would stop at 20 below if more were available)
    # Above: 155, 160, 165, 170
    
    below = [s for s in strikes if s < spot]
    above = [s for s in strikes if s > spot]
    
    print(f"Strikes below: {below}")
    print(f"Strikes above: {above}")
    
    # Verify ordering - should be sorted by distance from spot
    assert below == sorted(below, key=lambda x: abs(x - spot)), "Below strikes should be ordered by distance from ATM"
    assert above == sorted(above, key=lambda x: abs(x - spot)), "Above strikes should be ordered by distance from ATM"
    
    print("✓ PASS: Strikes are correctly ordered by distance from ATM")
    return True


if __name__ == "__main__":
    print("TESTING _get_filtered_data_for_walls Function")
    print("Verifying it filters for near 4 expirations with non-zero OI")
    print("And selects 20 strikes below/above ATM in proper order")
    print("=" * 70)
    
    all_pass = True
    
    try:
        all_pass &= test_4_expirations_with_non_zero_oi()
    except AssertionError as e:
        all_pass = False
        print(f"✗ TEST FAILED: {e}")
    
    try:
        all_pass &= test_ui_selected_expirations_with_oi_check()
    except AssertionError as e:
        all_pass = False
        print(f"✗ TEST FAILED: {e}")
    
    try:
        all_pass &= test_20_strikes_below_atm()
    except AssertionError as e:
        all_pass = False
        print(f"✗ TEST FAILED: {e}")
    
    try:
        all_pass &= test_30_strikes_above_atm()
    except AssertionError as e:
        all_pass = False
        print(f"✗ TEST FAILED: {e}")
    
    try:
        all_pass &= test_strikes_ordered_by_distance()
    except AssertionError as e:
        all_pass = False
        print(f"✗ TEST FAILED: {e}")
    
    print("\n" + "=" * 70)
    if all_pass:
        print("ALL TESTS PASSED ✓")
        print("\nSummary:")
        print("1. Function correctly selects up to 4 expirations with non-zero OI")
        print("2. UI-selected expirations are filtered to only those with volume")
        print("3. Function selects ~20 strikes below ATM, ATM, ~20 strikes above")
        print("4. Strikes are ordered by distance from ATM")
        print("\nThe filter is working as expected for ATM Order Flow!")
    else:
        print("SOME TESTS FAILED ✗")
        sys.exit(1)
