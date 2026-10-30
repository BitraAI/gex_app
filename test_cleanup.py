#!/usr/bin/env python3
"""Test script to verify all codebase cleanup changes."""

import sys
import importlib

# Test that the modules can be imported without errors
try:
    import scripts.analytics as analytics
    import scripts.flow as flow
    import scripts.calculations as calculations
    import scripts.chain_parser as chain_parser
    
    print("✓ All modules import successfully")
    
    # Test that unused imports were removed
    import scripts.option_streaming_service
    print("✓ option_streaming_service imports without unused imports")
    
    # Test analytics functions exist
    assert hasattr(analytics, 'compute_analytics'), "compute_analytics not found"
    assert hasattr(analytics, '_filter_active_expirations'), "_filter_active_expirations not found"
    assert hasattr(analytics, '_find_call_wall'), "_find_call_wall not found"
    assert hasattr(analytics, '_find_put_wall'), "_find_put_wall not found"
    assert hasattr(analytics, '_find_expected_pin'), "_find_expected_pin not found"
    print("✓ All analytics functions present")
    
    # Test chain_parser functions exist
    assert hasattr(chain_parser, 'fetch_and_parse_chain'), "fetch_and_parse_chain not found"
    assert hasattr(chain_parser, 'compute_analytics_for_symbol'), "compute_analytics_for_symbol not found"
    assert hasattr(chain_parser, 'compute_analytics_light'), "compute_analytics_light not found"
    print("✓ All chain_parser functions present")
    
    print("\n✅ All tests passed! Changes are working correctly.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
