#!/usr/bin/env python3
"""
Analysis of the ATM Order Flow Support/Resistance issue
"""

print("="*70)
print("ANALYSIS: ATM Order Flow Support/Resistance Issue")
print("="*70)

print("\n" + "="*70)
print("FLOW.PY CODE (flow.py:244-249):")
print("="*70)

print("\nIn flow.py, wall retrieval logic:")
print("put_wall_val = atm_svc.get_ticker_put_wall(t_upper) if atm_svc else None")
print("call_wall_val = atm_svc.get_ticker_call_wall(t_upper) if atm_svc else None")
print("if put_wall_val is None and t_upper == current_sym:")
print("    put_wall_val = (s.get('analytics') or {}).get('put_wall')")
print("if call_wall_val is None and t_upper == current_sym:")
print("    call_wall_val = (s.get('analytics') or {}).get('call_wall')")

print("\nTHE PROBLEM:")
print("1. fetch_data() calculates walls via compute_analytics() -> analytics['put_wall'], analytics['call_wall']")
print("2. But analytics is NOT stored to session_state in fetch_data()")
print("3. compute_state() sets session_state.analytics = analytics (at line 390)")
print("4. flow.py tries to read session_state['analytics'].get('put_wall')")
print("5. BUT session_state['analytics'] might be empty or from a different call!")

print("\n" + "="*70)
print("THE FIX")
print("="*70)

print("\nIn app.py fetch_data() function, we need to:")
print("1. Store analytics to session_state BEFORE compute_state()")
print("2. OR prevent compute_state() from overwriting session_state.analytics")
print("\nOption 1 (Recommended):")
print("   In fetch_data(), add: st.session_state.analytics = analytics")
print("   AFTER compute_analytics() is called")
print("\nThis ensures flow.py can read walls from session_state!")

print("\n" + "="*70)
print("CURRENT CODE")
print("="*70)

print("\napp.py fetch_data() at lines 1892-1904:")
print("   atm_svc.set_ticker_walls(_sym, analytics.get('put_wall'), analytics.get('call_wall'))")
print("   return {")
print("       'data': data,")
print("       'spot': spot,")
print("       'analytics': analytics,  <--- analytics is returned")
print("       'rv': rv,")
print("       'symbol': _sym,")
print("       'earnings_date': earnings_date")
print("   }")

print("\nPROBLEM:")
print("analytics is returned but NOT stored to session_state.analytics")
print("flow.py tries to read session_state['analytics'] but gets None or empty dict")

print("\nSOLUTION:")
print("In app.py fetch_data(), AFTER line 1849:")
print("   st.session_state.analytics = analytics  # <--- Add this!")

print("\n" + "="*70)
print("EXPLANATION")
print("="*70)

print("\nThe ATM Order Flow display logic in flow.py:")
print("1. First tries to get walls from ATM service (streaming)")
print("2. If that fails, falls back to session_state['analytics']")
print("3. But session_state['analytics'] is often empty when flow.py runs")
print("4. Therefore, walls are None/None")
print("5. Support/Resistance columns show empty!")

print("\nThe fix ensures session_state['analytics'] contains the calculated walls!")
