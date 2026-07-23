#!/usr/bin/env python3
"""Debug the ATM order flow issue"""

print("="*70)
print("DEBUG ATM Order Flow Issue")
print("="*70)

# Check the flow.py logic
print("\n1. flow.py wall retrieval logic (lines 244-249):")
print("   put_wall_val = atm_svc.get_ticker_put_wall(t_upper) if atm_svc else None")
print("   call_wall_val = atm_svc.get_ticker_call_wall(t_upper) if atm_svc else None")
print("   if put_wall_val is None and t_upper == current_sym:")
print("       put_wall_val = (s.get('analytics') or {}).get('put_wall')")
print("   if call_wall_val is None and t_upper == current_sym:")
print("       call_wall_val = (s.get('analytics') or {}).get('call_wall')")

print("\n2. app.py computes analytics (function fetch_data):")
print("   analytics = compute_analytics(filtered_data, spot, r=r, q=q, data_full=data)")
print("   analytics['filtered_flow_data'] = filtered_flow_data")
print("   analytics['put_wall'] = put_wall  # <-- Added this")
print("   analytics['call_wall'] = call_wall")
print("   atm_svc.set_ticker_walls(_sym, analytics.get('put_wall'), analytics.get('call_wall'))")

print("\n3. app.py also has compute_state (called by fetch_data):")
print("   Line 304: atm_svc.set_ticker_walls(_sym, _ana.get('put_wall'), _ana.get('call_wall'))")

print("\n4. The issue is likely in how analytics is stored in session_state:")
print("   - In fetch_data: analytics is returned but not stored to session_state.analytics")
print("   - In compute_state: this DOES store to session_state.analytics")
print("   - When flow.py falls back to session_state, it needs analytics to be stored")

print("\n5. Looking at the flow of data:")
print("   - fetch_data calls compute_state() at line 292")
print("   - compute_state stores analytics to session_state.analytics at line 390")
print("   - fetch_data returns analytics but doesn't store it to session_state")
print("   - flow.py uses session_state to get analytics")

print("\n6. The fix should ensure analytics are stored in session_state:")
print("   - In fetch_data, we should store analytics to session_state.analytics")
print("   - Then flow.py can retrieve from session_state")

print("\n" + "="*70)
print("SOLUTION:")
print("="*70)
print("In fetch_data function, ADD:")
print("   st.session_state.analytics = analytics")
print("This ensures flow.py can access analytics.put_wall and analytics.call_wall")
print("when it falls back to session-state analytics.")
