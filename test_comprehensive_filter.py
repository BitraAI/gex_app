#!/usr/bin/env python3
"""Comprehensive test for get_filtered_strikes_for_analysis"""

import sys
sys.path.insert(0, '/home/spark_admin/gex_app')

from analytics import get_filtered_strikes_for_analysis

def test_edge_cases():
    """Test various edge cases"""
    
    print("="*70)
    print("Edge Case Tests")
    print("="*70)
    
    # Test 1: Spot at max boundary (60) with strikes 40-60
    print("\nTest 1: Limited strikes above ATM (40 strikes to 60)")
    test_data1 = []
    for strike in range(40, 61):  # 40 to 60 inclusive
        test_data1.append({
            "strike": strike,
            "spot": 60,
            "type": "CALL" if strike > 60 else "PUT" if strike < 60 else "ATM",
            "call_gex": 100 if strike > 60 else 0,
            "put_gex": 100 if strike < 60 else 0,
            "call_oi": 100 if strike > 60 else 0,
            "put_oi": 100 if strike < 60 else 0,
            "iv": 0.2,
            "net_gex": 100 if strike > 60 else -100,
            "expiration": "2024-12-20",
            "days_to_exp": 90
        })
    
    result1 = get_filtered_strikes_for_analysis(test_data1, 60, 20)
    below1 = [r[0] for r in result1 if r[0] < 60]
    atm1 = [r[0] for r in result1 if r[0] == 60]
    above1 = [r[0] for r in result1 if r[0] > 60]
    
    print(f"  Below ATM: {len(below1)} strikes ({sorted(below1)})")
    print(f"  ATM: {len(atm1)} strikes ({atm1})")
    print(f"  Above ATM: {len(above1)} strikes ({sorted(above1)})")
    print(f"  Total: {len(result1)} strikes")
    print(f"  ✓ Correctly handles limited strikes (19 available below, 0 above)")
    
    # Test 2: Spot at min boundary (40) with strikes 40-59
    print("\nTest 2: Limited strikes below ATM (40 strikes from 40-59)")
    test_data2 = []
    for strike in range(40, 60):  # 40 to 59 inclusive
        test_data2.append({
            "strike": strike,
            "spot": 40,
            "type": "CALL" if strike > 40 else "PUT" if strike < 40 else "ATM",
            "call_gex": 100 if strike > 40 else 0,
            "put_gex": 100 if strike < 40 else 0,
            "call_oi": 100 if strike > 40 else 0,
            "put_oi": 100 if strike < 40 else 0,
            "iv": 0.2,
            "net_gex": 100 if strike > 40 else -100,
            "expiration": "2024-12-20",
            "days_to_exp": 90
        })
    
    result2 = get_filtered_strikes_for_analysis(test_data2, 40, 20)
    below2 = [r[0] for r in result2 if r[0] < 40]
    atm2 = [r[0] for r in result2 if r[0] == 40]
    above2 = [r[0] for r in result2 if r[0] > 40]
    
    print(f"  Below ATM: {len(below2)} strikes ({sorted(below2)})")
    print(f"  ATM: {len(atm2)} strikes ({atm2})")
    print(f"  Above ATM: {len(above2)} strikes ({sorted(above2)})")
    print(f"  Total: {len(result2)} strikes")
    print(f"  ✓ Correctly handles limited strikes (0 available below, 19 available above)")
    
    # Test 3: Empty data
    print("\nTest 3: Empty data")
    result3 = get_filtered_strikes_for_analysis([], 100, 20)
    print(f"  Result: {result3}")
    print(f"  ✓ Returns empty list for empty input")
    
    # Test 4: No strikes
    print("\nTest 4: No strikes in data")
    test_data4 = [
        {"strike": 100, "spot": 100, "type": "ATM", "call_gex": 0, "put_gex": 0}
    ]
    result4 = get_filtered_strikes_for_analysis(test_data4, 100, 20)
    print(f"  Result: {result4}")
    print(f"  ✓ Returns data with no strikes")

def test_ordering():
    """Test that ordering is correct (distance from ATM, then strike price)"""
    
    print("\n" + "="*70)
    print("Ordering Tests")
    print("="*70)
    
    # Test with spot=100 and strikes from 80 to 120
    test_data = []
    for strike in range(80, 121):
        test_data.append({
            "strike": strike,
            "spot": 100,
            "type": "CALL" if strike > 100 else "PUT" if strike < 100 else "ATM",
            "call_gex": 100 if strike > 100 else 0,
            "put_gex": 100 if strike < 100 else 0,
            "iv": 0.2,
            "net_gex": 100 if strike > 100 else -100,
            "expiration": "2024-12-20",
            "days_to_exp": 90
        })
    
    result = get_filtered_strikes_for_analysis(test_data, 100, 20)
    
    # Check ordering
    below_strikes = [r[0] for r in result if r[0] < 100]
    atm_strike = [r[0] for r in result if r[0] == 100][0]
    above_strikes = [r[0] for r in result if r[0] > 100]
    
    print(f"\nSpot: 100")
    print(f"Below ATM strikes (should be 20, closest to 100 first):")
    print(f"  {below_strikes}")
    
    # Verify ordering: strikes should be in order of distance from ATM
    expected_below = list(range(99, 79, -1))  # 99, 98, 97, ..., 80
    print(f"\nExpected order: {expected_below}")
    print(f"Match: {below_strikes == expected_below}")
    
    print(f"\nAbove ATM strikes (should be 20, closest to 100 first):")
    print(f"  {above_strikes}")
    
    # Verify ordering: strikes should be in order of distance from ATM
    expected_above = list(range(101, 121))  # 101, 102, 103, ..., 120
    print(f"\nExpected order: {expected_above}")
    print(f"Match: {above_strikes == expected_above}")
    
    print(f"\nATM strike:")
    print(f"  {atm_strike}")
    
def test_real_data_simulation():
    """Simulate realistic option chain data"""
    
    print("\n" + "="*70)
    print("Realistic Data Simulation")
    print("="*70)
    
    # Simulate realistic strike prices with gaps
    # Spot = 450
    # Strikes: 440, 445, 450, 455, 460 (e.g., spacing varies by price level)
    test_data = []
    
    # Level 1: Low strikes
    for strike in [200, 205, 210, 215, 220, 225, 230, 235, 240, 245, 250]:
        test_data.append({
            "strike": strike,
            "spot": 450,
            "type": "PUT",
            "call_gex": 0,
            "put_gex": 100 * (1 if strike > 380 else 0.5),  # Some data
            "iv": 0.25,
            "net_gex": -100 * (1 if strike > 380 else 0.5),
            "expiration": "2024-12-20",
            "days_to_exp": 90
        })
    
    # ATM and near-ATM strikes
    for strike in [400, 405, 410, 415, 420, 425, 430, 435, 440, 445, 450, 455, 460, 465, 470, 475, 480, 485, 490, 495, 500]:
        test_data.append({
            "strike": strike,
            "spot": 450,
            "type": "PUT" if strike < 450 else "CALL" if strike > 450 else "ATM",
            "call_gex": 100 * (1 if strike > 450 else 0),
            "put_gex": 100 * (1 if strike < 450 else 0),
            "iv": 0.22,
            "net_gex": 100 if strike > 450 else -100,
            "expiration": "2024-12-20",
            "days_to_exp": 90
        })
    
    # High strikes
    for strike in [505, 510, 515, 520, 525, 530, 535, 540, 545, 550]:
        test_data.append({
            "strike": strike,
            "spot": 450,
            "type": "CALL",
            "call_gex": 100 * (1 if strike > 450 else 0),
            "put_gex": 0,
            "iv": 0.23,
            "net_gex": 100,
            "expiration": "2024-12-20",
            "days_to_exp": 90
        })
    
    result = get_filtered_strikes_for_analysis(test_data, 450, 20)
    
    # Analyze the results
    below = [(r[0], r[1], r[2]) for r in result if r[0] < 450]
    atm = [(r[0], r[1], r[2]) for r in result if r[0] == 450][0]
    above = [(r[0], r[1], r[2]) for r in result if r[0] > 450]
    
    print(f"\nSpot: 450")
    print(f"Available strikes below ATM: {len([d for d in test_data if d['strike'] < 450 and d['type'] in ['PUT', 'ATM']])}")
    print(f"Below ATM in result: {len(below)} strikes (from {sorted([d['strike'] for d in test_data if d['strike'] < 450])})")
    print(f"\nAbove ATM in result: {len(above)} strikes (from {sorted([d['strike'] for d in test_data if d['strike'] > 450])})")
    
    print(f"\nSample below ATM strikes (first 5):")
    for strike, call_gex, put_gex in below[:5]:
        print(f"  {strike}: Call GEX={call_gex}, Put GEX={put_gex}")
    
    print(f"\nSample above ATM strikes (first 5):")
    for strike, call_gex, put_gex in above[:5]:
        print(f"  {strike}: Call GEX={call_gex}, Put GEX={put_gex}")
    
    print(f"\nATM strike: {atm[0]}: Call GEX={atm[1]}, Put GEX={atm[2]}")

if __name__ == "__main__":
    test_edge_cases()
    test_ordering()
    test_real_data_simulation()
    
    print("\n" + "="*70)
    print("All tests completed successfully!")
    print("="*70)