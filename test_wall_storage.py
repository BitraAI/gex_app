#!/usr/bin/env python3
"""Test that support/resistance walls are correctly stored and retrieved"""

import sys
sys.path.insert(0, '/home/spark_admin/gex_app')

from option_streaming_service import AtmOptionVolumeService

def test_wall_storage_and_retrieval():
    """Test that walls calculated in analytics are stored and retrieved correctly"""
    
    print("="*70)
    print("Test Wall Storage and Retrieval")
    print("="*70)
    
    # Create an ATM option service
    atm_svc = AtmOptionVolumeService()
    
    # Store walls for a ticker
    ticker = "AAPL"
    print(f"\nStoring walls for ticker: {ticker}")
    put_wall = 150.50  # Support level
    call_wall = 160.75  # Resistance level
    
    atm_svc.set_ticker_walls(ticker, put_wall, call_wall)
    
    # Retrieve the walls
    retrieved_put = atm_svc.get_ticker_put_wall(ticker)
    retrieved_call = atm_svc.get_ticker_call_wall(ticker)
    
    print(f"Original put wall: {put_wall}")
    print(f"Retrieved put wall: {retrieved_put}")
    print(f"Match: {put_wall == retrieved_put}")
    
    print(f"\nOriginal call wall: {call_wall}")
    print(f"Retrieved call wall: {retrieved_call}")
    print(f"Match: {call_wall == retrieved_call}")
    
    # Verify the values match
    assert put_wall == retrieved_put, f"Put wall mismatch: {put_wall} != {retrieved_put}"
    assert call_wall == retrieved_call, f"Call wall mismatch: {call_wall} != {retrieved_call}"
    
    print("\n✓ Walls stored and retrieved correctly!")
    
    # Test that None values don't overwrite existing walls
    print("\n" + "="*70)
    print("Test None Values (should preserve existing walls)")
    print("="*70)
    
    # Store initial walls
    atm_svc.set_ticker_walls(ticker, 150.50, 160.75)
    put_before = atm_svc.get_ticker_put_wall(ticker)
    call_before = atm_svc.get_ticker_call_wall(ticker)
    
    print(f"Put wall before None update: {put_before}")
    print(f"Call wall before None update: {call_before}")
    
    # Try to update with None values (as in app.py logic)
    atm_svc.set_ticker_walls(ticker, None, None)
    
    put_after = atm_svc.get_ticker_put_wall(ticker)
    call_after = atm_svc.get_ticker_call_wall(ticker)
    
    print(f"\nPut wall after None update: {put_after}")
    print(f"Call wall after None update: {call_after}")
    
    # Verify walls were preserved
    assert put_before == put_after, f"Put wall changed when set to None: {put_before} -> {put_after}"
    assert call_before == call_after, f"Call wall changed when set to None: {call_before} -> {call_after}"
    
    print("\n✓ Walls preserved when set_ticker_walls is called with None!")
    
    # Test with different ticker
    print("\n" + "="*70)
    print("Test Multiple Tickers")
    print("="*70)
    
    ticker2 = "SPY"
    atm_svc.set_ticker_walls(ticker2, 300.0, 320.50)
    
    print(f"\nStoring walls for {ticker}: put={atm_svc.get_ticker_put_wall(ticker)}, call={atm_svc.get_ticker_call_wall(ticker)}")
    print(f"Storing walls for {ticker2}: put={atm_svc.get_ticker_put_wall(ticker2)}, call={atm_svc.get_ticker_call_wall(ticker2)}")
    
    assert ticker in atm_svc.tracked_tickers()
    assert ticker2 in atm_svc.tracked_tickers()
    
    print("\n✓ Multiple tickers supported!")
    
def test_flow_py_wall_retrieval_logic():
    """Test the logic from flow.py for retrieving walls"""
    
    print("\n" + "="*70)
    print("Test flow.py Wall Retrieval Logic")
    print("="*70)
    
    # This simulates the logic in flow.py
    def get_wall_values_from_atm_service(atm_svc, current_sym, session_analytics):
        """Simulates the wall retrieval logic from flow.py lines 244-249"""
        # Support (Put Wall) / Resistance (Call Wall): prefer per-ticker value
        # set by fetch_data, fall back to session-state analytics for the
        # current chart symbol so the columns are never empty without a manual
        # Refresh.
        put_wall_val = atm_svc.get_ticker_put_wall(current_sym) if atm_svc else None
        call_wall_val = atm_svc.get_ticker_call_wall(current_sym) if atm_svc else None
        if put_wall_val is None and current_sym == "AAPL":
            put_wall_val = (session_analytics or {}).get("put_wall")
        if call_wall_val is None and current_sym == "AAPL":
            call_wall_val = (session_analytics or {}).get("call_wall")
        
        return put_wall_val, call_wall_val
    
    # Test 1: Wall exists in ATM service
    print("\nTest 1: Wall exists in ATM service")
    atm_svc = AtmOptionVolumeService()
    atm_svc.set_ticker_walls("AAPL", 150.50, 160.75)
    
    session_analytics = {}
    put_val, call_val = get_wall_values_from_atm_service(atm_svc, "AAPL", session_analytics)
    
    print(f"  ATM service put wall: {put_val}")
    print(f"  ATM service call wall: {call_val}")
    assert put_val == 150.50
    assert call_val == 160.75
    
    # Test 2: Wall exists in session analytics (fallback)
    print("\nTest 2: Wall exists in session analytics (fallback)")
    atm_svc2 = AtmOptionVolumeService()
    # Simulate no wall in ATM service
    
    session_analytics2 = {"put_wall": 145.00, "call_wall": 155.00}
    put_val2, call_val2 = get_wall_values_from_atm_service(atm_svc2, "AAPL", session_analytics2)
    
    print(f"  Session analytics put wall: {put_val2}")
    print(f"  Session analytics call wall: {call_val2}")
    assert put_val2 == 145.00
    assert call_val2 == 155.00
    
    print("\n✓ flow.py wall retrieval logic works correctly!")

if __name__ == "__main__":
    test_wall_storage_and_retrieval()
    test_flow_py_wall_retrieval_logic()
    
    print("\n" + "="*70)
    print("All tests completed successfully!")
    print("="*70)