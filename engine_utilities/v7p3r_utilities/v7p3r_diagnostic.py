#!/usr/bin/env python3
"""
V7P3R Engine Diagnostic
======================

Quick diagnostic to understand why V7P3R is losing to SlowMate.
Let's run a single manual test and examine the results closely.
"""

import asyncio
import sys
from pathlib import Path

# Add framework to path
sys.path.append(str(Path(__file__).parent / 'automated_battle_framework'))

from engine_battle_framework import BattleFramework, ChallengeType, EngineConfig, EngineType

async def run_diagnostic():
    """Run detailed diagnostic of V7P3R performance"""
    
    print("🔍 V7P3R Engine Diagnostic")
    print("=" * 30)
    
    framework = BattleFramework()
    
    # List available engines
    print("📋 Available engines:")
    for name, config in framework.engines.items():
        print(f"   - {name}: {config.engine_type.value}")
    
    # Create session
    session_id = await framework.create_battle_session(
        "V7P3R_Diagnostic",
        "Detailed diagnostic of V7P3R vs SlowMate"
    )
    
    print(f"\n🎮 Running single diagnostic test...")
    print("   V7P3R vs SlowMate (speed challenge)")
    
    try:
        result = await framework.run_challenge(
            session_id,
            ChallengeType.SPEED_CHALLENGE,
            "V7P3R_Current",
            "SlowMate_Current",
            time_limit=5.0  # 5 seconds per position
        )
        
        if result:
            print(f"\n📊 Diagnostic Results:")
            print(f"   Winner: {result.winner}")
            print(f"   Execution time: {result.execution_time:.2f}s")
            print(f"   Challenge type: {result.challenge_type.value}")
            print(f"   Status: {result.status.value}")
            
            # Examine result details
            if hasattr(result, 'result_details') and result.result_details:
                details = result.result_details
                print(f"\n🔍 Detailed Analysis:")
                
                if 'engine1_times' in details:
                    v7p3r_times = details.get('engine1_times', [])
                    slowmate_times = details.get('engine2_times', [])
                    
                    print(f"   V7P3R times: {v7p3r_times}")
                    print(f"   SlowMate times: {slowmate_times}")
                    
                    if v7p3r_times and slowmate_times:
                        avg_v7p3r = sum(v7p3r_times) / len(v7p3r_times)
                        avg_slowmate = sum(slowmate_times) / len(slowmate_times)
                        
                        print(f"   V7P3R avg time: {avg_v7p3r:.3f}s")
                        print(f"   SlowMate avg time: {avg_slowmate:.3f}s")
                        
                        if avg_v7p3r > avg_slowmate:
                            print(f"   ⚠️  V7P3R is SLOWER than SlowMate!")
                            print(f"   🐌 Speed disadvantage: {avg_v7p3r - avg_slowmate:.3f}s")
                        else:
                            print(f"   ✅ V7P3R is faster than SlowMate")
                            print(f"   ⚡ Speed advantage: {avg_slowmate - avg_v7p3r:.3f}s")
                
                if 'engine1_moves' in details:
                    v7p3r_moves = details.get('engine1_moves', [])
                    slowmate_moves = details.get('engine2_moves', [])
                    
                    print(f"\n🎯 Move Analysis:")
                    for i, (v7_move, sm_move) in enumerate(zip(v7p3r_moves, slowmate_moves)):
                        print(f"   Position {i+1}: V7P3R={v7_move}, SlowMate={sm_move}")
            
            # Metrics
            if hasattr(result, 'metrics') and result.metrics:
                print(f"\n📈 Performance Metrics:")
                for key, value in result.metrics.items():
                    print(f"   {key}: {value}")
        
        else:
            print("❌ Diagnostic test failed")
    
    except Exception as e:
        print(f"💥 Diagnostic crashed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run the diagnostic"""
    await run_diagnostic()


if __name__ == "__main__":
    asyncio.run(main())
