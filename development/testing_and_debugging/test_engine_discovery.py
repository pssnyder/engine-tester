"""
Test script for Universal Engine Manager
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from universal_engine_manager import UniversalEngineManager

def universal_engine_discovery():
    """Test the engine discovery system"""
    print("Testing Universal Engine Manager...")
    print("=" * 50)
    
    # Create manager and discover engines
    manager = UniversalEngineManager()
    
    print(f"\nDiscovered {len(manager.available_configs)} engines:")
    print("-" * 30)
    
    for name, config in manager.available_configs.items():
        print(f"Engine: {name}")
        print(f"  Type: {config.type}")
        print(f"  Description: {config.description}")
        print(f"  Capabilities: {', '.join(config.capabilities or [])}")
        if config.path:
            print(f"  Path: {config.path}")
        if config.executable:
            print(f"  Executable: {config.executable}")
        print()
    
    # Try to auto-load default engines
    print("Auto-loading default engines...")
    success = manager.auto_load_default_engines()
    print(f"Auto-load successful: {success}")
    
    # Show loaded engines
    loaded = manager.list_engines()
    print(f"\nLoaded engines: {loaded}")
    
    # Show current engine
    current = manager.get_current_engine()
    if current:
        print(f"Current engine: {current.name}")
        print(f"Engine ready: {current.is_ready()}")
    else:
        print("No current engine")
    
    # Test engine info
    print("\nDetailed engine info:")
    for name in manager.list_available_engines():
        info = manager.get_engine_info(name)
        if info:
            print(f"{name}: {info}")
    
    manager.stop_all()
    print("\nTest completed.")

if __name__ == "__main__":
    universal_engine_discovery()
