"""
Test script to verify the V-Guard Inverter integration works with the renamed files.
This script doesn't actually run the integration, but checks that imports work correctly.
"""

import importlib
import sys
import os

# Add the current directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported without errors."""
    modules = [
        "sensor",
        "switch",
        "number",
        "mode_select",  # This was renamed from vguard_select
        "const",
        "__init__"
    ]
    
    errors = []
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"✓ Successfully imported {module}")
        except ImportError as e:
            errors.append(f"✗ Failed to import {module}: {e}")
    
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  {error}")
        return False
    
    return True

def test_references():
    """Test that references between modules are correct."""
    # Import the modules
    try:
        import sensor
        import switch
        import number
        import mode_select
        import __init__ as init
        
        # Check that mode_select is referenced in __init__
        if "mode_select" in str(init.async_setup_entry.__code__.co_consts):
            print("✓ mode_select is referenced in __init__")
        else:
            print("✗ mode_select is not referenced in __init__")
            return False
        
        # Check that schedule_entity_update is imported in mode_select
        if hasattr(mode_select, "schedule_entity_update"):
            print("✓ schedule_entity_update is imported in mode_select")
        else:
            print("✗ schedule_entity_update is not imported in mode_select")
            return False
        
        return True
    except Exception as e:
        print(f"Error testing references: {e}")
        return False

if __name__ == "__main__":
    print("Testing V-Guard Inverter integration...")
    
    imports_ok = test_imports()
    if imports_ok:
        print("\nAll imports successful!")
    else:
        print("\nSome imports failed!")
    
    references_ok = test_references()
    if references_ok:
        print("\nAll references are correct!")
    else:
        print("\nSome references are incorrect!")
    
    if imports_ok and references_ok:
        print("\nIntegration appears to be working correctly with the renamed files!")
    else:
        print("\nIntegration has issues with the renamed files. Please check the errors above.")