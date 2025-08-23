#!/usr/bin/env python3
"""
🧪 Simple Engine Test
====================

Test the battle framework with a minimal working example.
"""

import asyncio
import sys
from pathlib import Path

# Add the framework directory to Python path
framework_dir = Path(__file__).parent
sys.path.insert(0, str(framework_dir))

from engine_battle_framework import BattleFramework, ChallengeType

async def simple_test():
    """Run a simple test of the framework"""
    print("🧪 Testing Engine Battle Framework...")
    
    framework = BattleFramework()
    
    # Create a test session
    try:
        session_id = await framework.create_battle_session(
            "Simple_Test",
            "Basic framework test"
        )
        print(f"✅ Created session: {session_id}")
        
        # Try to run a speed challenge
        print("⚡ Attempting speed challenge...")
        result = await framework.run_challenge(
            session_id,
            ChallengeType.SPEED_CHALLENGE,
            "V7P3R_Current",
            "SlowMate_Current",
            time_limit=3.0
        )
        
        print(f"✅ Speed challenge completed!")
        print(f"   Winner: {result.winner}")
        print(f"   Duration: {result.execution_time:.1f}s")
        
        # Save results
        framework.save_session(session_id)
        print(f"✅ Session saved successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🤖 Simple Engine Battle Framework Test")
    print("=" * 40)
    
    success = await simple_test()
    
    if success:
        print("\n🎯 Framework test successful!")
        print("🚀 Try running: python battle_runner.py --mode demo")
    else:
        print("\n❌ Framework test failed")
        print("💡 Check engine paths and UCI compatibility")

if __name__ == "__main__":
    asyncio.run(main())
