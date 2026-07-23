import sys
sys.path.insert(0, '/home/spark_admin/gex_app')

# Force update session state analytics
from app import fetch_data

# Simulate the flow for debugging
print("="*70)
print("DEBUG: ATM Order Flow Support/Resistance Issue")
print("="*70)

print("\n1. The Problem:")
print("   - fetch_data() calculates walls via compute_analytics()")
print("   - Walls are stored in analytics['put_wall'] and analytics['call_wall']")
print("   - But session_state.analytics is set to {} in compute_state()")
print("   - This overwrites the calculated walls!")

print("\n2. The Fix Needed:")
print("   In app.py line 303, change:")
print("   ")
print("       st.session_state.analytics = {}")
print("   ")
print("   To:")
print("   ")
print("       if not st.session_state.get('analytics'):")
print("           st.session_state.analytics = {}")
print("   ")
print("   This ensures analytics is preserved from fetch_data()")

print("\n3. The Current broken flow:")
print("   fetch_data() -> compute_analytics() -> stores walls in analytics")
print("                        |")
print("                        v")
print("   compute_state() -> session_state.analytics = {} <--- OVERWRITES!")
print("                        |")
print("                        v")
print("   flow.py -> tries to read walls from session_state['analytics'] -> gets None!")
print("                        |")
print("                        v")
print("   ATM Order Flow grid -> displays empty support/resistance columns!")

print("\n" + "="*70)
print("THE ACTUAL FIX")
print("="*70)

print("\nIn app.py, find this at line 303:")
print("   st.session_state.analytics = {}")
print("\nReplace it with:")
print("   if not st.session_state.get('analytics'):")
print("       st.session_state.analytics = {}")
print("\nThis preserves analytics from fetch_data()")

print("\n" + "="*70)
print("EXPLANATION")
print("="*70)

print("\nThe ATM Order Flow grid uses walls from TWO sources:")
print("1. ATM Service (streaming) - set by fetch_data() via atm_svc.set_ticker_walls()")
print("2. Session State Analytics (REST) - fallback used by flow.py")

print("\nCurrently:")
print("✓ Walls ARE stored in ATM service")
print("❌ Walls are NOT stored in Session State Analytics (overwrite!)")

print("\nWhen flow.py runs:")
print("1. Tries to get walls from session_state['analytics']")
print("2. Gets {} instead of calculated walls")
print("3. Returns None for Support/Resistance")
print("4. Order flow grid shows empty columns!")

print("\nThe simple fix - preserve analytics!")
print(""""
# BEFORE (broken):
def compute_state(_sym):
    # ... code ...
    st.session_state.analytics = {}  # <--- This overwrites walls!
    # ... more code ...

# AFTER (fixed):
def compute_state(_sym):
    # ... code ...
    if not st.session_state.get("analytics"):
        st.session_state.analytics = {}  # <--- Only initialize if not set!
    # ... more code ...
""")

print("\nThis ensures both fetch_data() and flow.py use the correct walls!")