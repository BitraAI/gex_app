import sys
sys.path.insert(0, '/home/spark_admin/gex_app')

# Simple test to verify the fix for ATM Order Flow Support/Resistance display

print("="*70)
print("VERIFICATION: ATM Order Flow Support/Resistance Fix")
print("="*70)

print("\n" + "="*70)
print("ISSUE: ATM Order flow support and resistance columns are empty")
print("="*70)

print("\nLooking at app.py fetch_data function:")
print("1. Line 1842-1900: fetch_data() calculates analytics")
print("2. Line 1849: analytics['filtered_flow_data'] = filtered_flow_data")
print("3. Lines 1900-1904: Returns analytics in return dict")
print("4. BUT analytics is NOT stored to session_state in fetch_data()")

print("\nLooking at app.py compute_state() line 390:")
print("   st.session_state.analytics = analytics")
print("\nThis stores analytics to session state!")

print("\n" + "="*70)
print("THE FIX")
print("="*70)

print("\nIn app.py fetch_data() function, AFTER line 1849:")
print("   Add: st.session_state.analytics = analytics")
print("\nThis stores analytics to session state BEFORE return!")

print("\nResult:")
print("1. fetch_data() calculates walls via compute_analytics()")
print("2. fetch_data() stores analytics to session_state")
print("3. fetch_data() returns analytics in result")
print("4. flow.py can read walls from session_state")
print("5. ATM Order Flow grid displays support/resistance!")

print("\n" + "="*70)
print("IMPORTANT CONFIG VS DATA")
print("="*70)

print("\nNote: There's a distinction between CONFIG and DATA in the app:")
print("CONFIG: Charts, settings, UI state (session_state)")
print("DATA: Option chain data (st.session_state.data)")
print("\nWalls are calculated from DATA (data, spot)")
print("Walls are displayed in Charts (session_state)")
print("Fix: Store analytics to session_state so charts can access walls")

print("\n" + "="*70)
print("EXAMPLE FIX")
print("="*70)

print("\nIn app.py, find fetch_data() function:")
print("Current near line 1848-1850:")
print("   analytics = compute_analytics(...)")
print("   analytics['filtered_flow_data'] = filtered_flow_data")
print("   # Line 1850: <--- ADD AFTER THIS:")
print("   st.session_state.analytics = analytics")
print("   return {...}")

print("\nThis fix ensures analytics (with put_wall and call_wall)")
print("are stored to session_state analytics for flow.py to read!")