#!/usr/bin/env python3
"""
Simple test of .bat engine with universal puzzle analyzer
"""

import sys
import os

# Set up the path
engine_tester_path = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester"
sys.path.append(os.path.join(engine_tester_path, 'engine_utilities'))

# Test the engine directly
v14_2_path = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\V7P3R\V7P3R_v14.2\V7P3R_v14.2.bat"

print(f"Testing .bat engine: {v14_2_path}")
print(f"Engine exists: {os.path.exists(v14_2_path)}")

if os.path.exists(v14_2_path):
    try:
        from universal_puzzle_analyzer import UniversalPuzzleAnalyzer
        
        print("Importing analyzer...")
        analyzer = UniversalPuzzleAnalyzer(v14_2_path)
        print(f"Engine type: {analyzer.engine_type}")
        print(f"Engine command: {analyzer.engine_command}")
        print(f"Engine name: {analyzer.engine_name}")
        
        # Try to get engine info
        print("Getting engine info...")
        print(f"Engine info: {analyzer.engine_info}")
        
        print("✅ Basic .bat engine support test passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ Test engine not found")