#!/usr/bin/env python3
"""
Test V7P3R vs BongcloudEnthusiast (307 ELO)
Simple proof of concept to see if the compiled Chess Challenge bot works
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'automated_battle_framework'))

from engine_battle_framework import BattleFramework

def test_v7p3r_vs_bongcloud():
    """Test V7P3R against compiled BongcloudEnthusiast"""
    
    framework = BattleFramework()
    
    # Define engines
    v7p3r_path = "s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester/engines/V7P3R/V7P3R_v7.0.exe"
    bongcloud_path = "s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester/engines/BongcloudEnthusiast_307_ELO.exe"
    
    print("🚀 Testing V7P3R v7.0 vs BongcloudEnthusiast (307 ELO)")
    print(f"V7P3R: {v7p3r_path}")
    print(f"Bongcloud: {bongcloud_path}")
    
    # Check if files exist
    if not os.path.exists(v7p3r_path):
        print("❌ V7P3R executable not found!")
        return False
        
    if not os.path.exists(bongcloud_path):
        print("❌ BongcloudEnthusiast executable not found!")
        return False
    
    # Run battle
    try:
        result = framework.run_engine_battle(
            engine1_path=v7p3r_path,
            engine1_name="V7P3R_v7.0",
            engine2_path=bongcloud_path,
            engine2_name="BongcloudEnthusiast_307_ELO",
            time_control=10.0,  # 10 seconds per move
            max_moves=100
        )
        
        if result:
            print("\n🎉 Battle completed successfully!")
            print(f"Result: {result}")
            return True
        else:
            print("\n❌ Battle failed")
            return False
            
    except Exception as e:
        print(f"\n💥 Battle crashed: {e}")
        return False

if __name__ == "__main__":
    success = test_v7p3r_vs_bongcloud()
    if success:
        print("\n✅ Proof of concept successful - we can test V7P3R against rated bots!")
    else:
        print("\n🚧 Need to debug the Chess Challenge bot interface")
