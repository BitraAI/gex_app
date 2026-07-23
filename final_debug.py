import sys
sys.path.insert(0, '/home/spark_admin/gex_app')

# Debugging and fixing the ATM Order Flow issue

print("="*70)
print("DEBUG: ATM Order Flow Support/Resistance Issue")
print("="*70)

print("\n" + "="*70)
print("THE ACTUAL PROBLEM")
print("="*70)

print("\nIn app.py, the FLOW is:")
print("1. fetch_data() -> calls compute_analytics() -> calculates walls")
print("2. fetch_data() -> returns analytics in return dict")
print("3. flow.py -> reads session_state['analytics']")
print("4. BUT: session_state.analytics is NOT set by fetch_data()")
print("5. SO: session_state['analytics'] is empty/None")
print("6. THEREFORE: flow.py gets None for walls")
print("7. ORDER FLOW grid shows EMPTY columns!")

print("\n" + "="*70)
print("THE FIX")
print("="*70)

print("\nIn app.py fetch_data() function, ADD AFTER line 1848:")
print("   st.session_state.analytics = analytics")
print("\nThis stores analytics to session state for flow.py to read!")

print("\nAFTER THE FIX:")
print("1. fetch_data() -> calls compute_analytics() -> calculates walls")
print("2. fetch_data() -> STORES analytics to session_state")
print("3. fetch_data() -> returns analytics in return dict")
print("4. flow.py -> reads session_state['analytics'] (NOW HAS WALLS!)")
print("5. returns walls to display")
print("6. ORDER FLOW grid shows CORRECT support/resistance!")

print("\n" + "="*70)
print("EXPLANATION")
print("="*70)

print("\nThe ATM Order Flow uses walls from session_state['analytics']")
print("Currently: session_state['analytics'] is set to {} in compute_state()")
print("But fetch_data() calculates walls and returns them")
print("However, fetch_data() does NOT store them to session_state!")
print("\nWhen flow.py runs:")
print("1. Tries to get walls from session_state['analytics']")
print("2. Gets {} instead of calculated walls")
print("3. Returns None/None for Support/Resistance")
print("4. Order flow grid displays EMPTY!")

print("\nThe fix - preserve analytics in session_state:")
print(""""
# In fetch_data():
analytics = compute_analytics(...)
# <--- ADD THIS LINE:
st.session_state.analytics = analytics
return {"data": data, "spot": spot, "analytics": analytics, ...}
""")

print("\nNow flow.py can read the calculated walls!")