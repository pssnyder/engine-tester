#!/usr/bin/env python3
"""
V7P3R vs Weak Stockfish - Framework Test
========================================

Add weak Stockfish to the existing framework and test against V7P3R.
Uses the framework that we know works reliably.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add framework to path  
sys.path.append(str(Path(__file__).parent / 'automated_battle_framework'))

from engine_battle_framework import BattleFramework, ChallengeType, EngineConfig, EngineType

async def add_weak_stockfish_to_framework(framework):
    """Add a weak Stockfish configuration to the framework"""
    
    stockfish_path = Path("s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester/engines/Stockfish/stockfish-windows-x86-64-avx2.exe")
    
    if not stockfish_path.exists():
        print(f"❌ Stockfish not found: {stockfish_path}")
        return False
    
    # Add weak Stockfish as EXE_CONTROL type (like C0BR4)
    weak_stockfish_config = EngineConfig(
        name="WeakStockfish",
        engine_type=EngineType.EXE_CONTROL,
        path=str(stockfish_path),
        version="17.1_weak"
    )
    
    framework.add_engine(weak_stockfish_config)
    print("✅ Added WeakStockfish to framework")
    return True

async def run_v7p3r_vs_weak_stockfish():
    """Run V7P3R against weak Stockfish"""
    
    print("🚀 V7P3R vs Weak Stockfish Test")
    print("=" * 40)
    
    framework = BattleFramework()
    
    # Add weak Stockfish
    if not await add_weak_stockfish_to_framework(framework):
        return False
    
    try:
        # Create session
        session_id = await framework.create_battle_session(
            "V7P3R_vs_WeakStockfish",
            "Testing V7P3R against weakened Stockfish"
        )
        print(f"✅ Session created: {session_id}")
        
        # Show available engines
        print(f"\n📋 Available engines:")
        for name in framework.engines.keys():
            print(f"   - {name}")
        
        # Run test
        print(f"\n🎮 Running V7P3R vs WeakStockfish...")
        
        result = await framework.run_challenge(
            session_id,
            ChallengeType.SPEED_CHALLENGE,  # Start with speed challenge
            "V7P3R_Current",
            "WeakStockfish", 
            time_limit=5.0  # 5 seconds per position
        )
        
        if result:
            print(f"✅ Challenge completed!")
            print(f"   Winner: {result.winner}")
            print(f"   Duration: {result.execution_time:.1f}s")
            
            # Analyze result
            if result.winner == "V7P3R_Current":
                print("🎉 V7P3R beats weak Stockfish!")
                print("✅ Ready to test against stronger Stockfish ELOs")
            elif result.winner == "WeakStockfish":
                print("📈 Weak Stockfish wins")
                print("⚠️  May need even weaker Stockfish settings")
            else:
                print("⚫ Draw - competitive match")
            
            return True
        else:
            print("❌ Challenge failed")
            return False
    
    except Exception as e:
        print(f"💥 Test failed: {e}")
        return False

async def main():
    """Main function"""
    
    try:
        success = await run_v7p3r_vs_weak_stockfish()
        
        if success:
            print("\n🎉 Stockfish integration test PASSED!")
            print("🚀 Ready for full ELO gauntlet testing")
        else:
            print("\n❌ Stockfish integration test FAILED!")
            print("🛠️  Need to debug Stockfish configuration")
    
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted")
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
