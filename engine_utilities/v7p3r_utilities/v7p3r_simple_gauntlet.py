#!/usr/bin/env python3
"""
V7P3R Simplified ELO Gauntlet
============================

Simple ELO assessment using speed challenges:
1. Tests V7P3R against multiple Stockfish configurations
2. Uses the framework approach that we know works
3. Gradually increases difficulty to find V7P3R's ceiling

Based on success: V7P3R beat default Stockfish, so test UPWARD!
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add framework to path
sys.path.append(str(Path(__file__).parent / 'automated_battle_framework'))

from engine_battle_framework import BattleFramework, ChallengeType, EngineConfig, EngineType

class V7P3RSimpleGauntlet:
    """Simple ELO assessment with progressive difficulty"""
    
    def __init__(self):
        self.framework = BattleFramework()
        self.stockfish_path = "s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester/engines/Stockfish/stockfish-windows-x86-64-avx2.exe"
        
        # Progressive difficulty levels
        self.difficulty_levels = [
            "default",      # Default Stockfish (we beat this)
            "fast_weak",    # Fast weak version
            "slow_weak",    # Slower weak version  
            "medium",       # Medium strength
            "strong",       # Strong version
            "very_strong"   # Very strong version
        ]
        
        self.results = {
            'test_start': datetime.now().isoformat(),
            'v7p3r_version': 'v7.0',
            'tests': [],
            'summary': {}
        }
    
    async def add_stockfish_variant(self, variant_name: str):
        """Add different Stockfish variants"""
        
        engine_name = f"Stockfish_{variant_name}"
        
        # Remove if exists
        if engine_name in self.framework.engines:
            del self.framework.engines[engine_name]
        
        # Configure based on variant
        stockfish_config = EngineConfig(
            name=engine_name,
            engine_type=EngineType.EXE_CONTROL,
            path=self.stockfish_path,
            version=f"17.1_{variant_name}"
        )
        
        self.framework.add_engine(stockfish_config)
        print(f"✅ Added {engine_name}")
        return engine_name
    
    async def test_difficulty_level(self, level: str, num_tests: int = 3):
        """Test V7P3R against a difficulty level"""
        
        print(f"\n🎯 Testing Level: {level} ({num_tests} tests)")
        print("=" * 35)
        
        # Add Stockfish variant
        stockfish_name = await self.add_stockfish_variant(level)
        
        # Create session
        session_id = await self.framework.create_battle_session(
            f"V7P3R_vs_{level}",
            f"V7P3R v7.0 vs Stockfish {level}"
        )
        
        wins = 0
        draws = 0
        losses = 0
        
        # Run tests
        for test_num in range(1, num_tests + 1):
            print(f"🎮 Test {test_num}/{num_tests}: ", end='')
            
            try:
                result = await self.framework.run_challenge(
                    session_id,
                    ChallengeType.SPEED_CHALLENGE,
                    "V7P3R_Current",
                    stockfish_name,
                    time_limit=5.0  # 5 seconds per position
                )
                
                if result:
                    if result.winner == "V7P3R_Current":
                        wins += 1
                        print("✅ V7P3R wins")
                    elif result.winner == stockfish_name:
                        losses += 1
                        print("❌ Stockfish wins")
                    else:
                        draws += 1
                        print("⚫ Draw")
                else:
                    print("💥 Test failed")
                    
            except Exception as e:
                print(f"💥 Test crashed: {e}")
        
        # Calculate performance
        total_tests = wins + draws + losses
        if total_tests > 0:
            score_rate = (wins + 0.5 * draws) / total_tests
        else:
            score_rate = 0.0
        
        level_result = {
            'level': level,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'total_tests': total_tests,
            'score_rate': score_rate,
            'performance_assessment': self.assess_performance(score_rate)
        }
        
        self.results['tests'].append(level_result)
        
        print(f"📊 Level {level}: {wins}W-{draws}D-{losses}L ({score_rate:.1%})")
        print(f"🎯 Assessment: {level_result['performance_assessment']}")
        
        return level_result
    
    def assess_performance(self, score_rate: float) -> str:
        """Assess performance based on score rate"""
        if score_rate >= 0.8:
            return "DOMINANT - continue to harder level"
        elif score_rate >= 0.6:
            return "STRONG - competitive at this level"
        elif score_rate >= 0.4:
            return "COMPETITIVE - close match"
        elif score_rate >= 0.2:
            return "STRUGGLING - near ceiling"
        else:
            return "OVERWHELMED - exceeded ceiling"
    
    async def run_progressive_gauntlet(self):
        """Run progressive difficulty gauntlet"""
        
        print("🚀 V7P3R Progressive ELO Gauntlet")
        print("=" * 40)
        print(f"📈 Difficulty progression: {self.difficulty_levels}")
        print(f"⚡ Test type: Speed challenges")
        print(f"🎮 Tests per level: 3")
        
        try:
            for level in self.difficulty_levels:
                level_result = await self.test_difficulty_level(level, num_tests=3)
                
                # Decision logic
                score_rate = level_result['score_rate']
                
                if score_rate < 0.2:
                    print(f"\n⚠️  V7P3R overwhelmed at {level} ({score_rate:.1%}) - stopping")
                    break
                elif score_rate < 0.4:
                    print(f"🎯 Found competitive range at {level} ({score_rate:.1%})")
                    # Continue but we're near the ceiling
                elif score_rate >= 0.8:
                    print(f"✅ V7P3R dominant at {level} ({score_rate:.1%}) - continuing")
                
                # Brief pause between levels
                await asyncio.sleep(2.0)
            
            # Generate final summary
            self.generate_summary()
            self.save_results()
            
        except KeyboardInterrupt:
            print(f"\n⚠️  Gauntlet interrupted by user")
            self.save_results()
        except Exception as e:
            print(f"\n💥 Gauntlet crashed: {e}")
            self.save_results()
    
    def generate_summary(self):
        """Generate final assessment summary"""
        
        if not self.results['tests']:
            return
        
        total_wins = sum(t['wins'] for t in self.results['tests'])
        total_draws = sum(t['draws'] for t in self.results['tests'])
        total_losses = sum(t['losses'] for t in self.results['tests'])
        total_tests = total_wins + total_draws + total_losses
        
        if total_tests > 0:
            overall_score = (total_wins + 0.5 * total_draws) / total_tests
        else:
            overall_score = 0.0
        
        # Find peak performance level
        best_level = None
        best_score = 0
        
        for test in self.results['tests']:
            if test['score_rate'] > best_score:
                best_score = test['score_rate']
                best_level = test['level']
        
        # Find competitive range
        competitive_levels = [t['level'] for t in self.results['tests'] if 0.4 <= t['score_rate'] <= 0.8]
        
        self.results['summary'] = {
            'total_tests': total_tests,
            'overall_score_rate': overall_score,
            'peak_level': best_level,
            'peak_score_rate': best_score,
            'competitive_levels': competitive_levels,
            'overall_assessment': self.assess_performance(overall_score)
        }
    
    def save_results(self):
        """Save gauntlet results"""
        
        self.results['test_end'] = datetime.now().isoformat()
        
        # Save detailed results
        results_dir = Path("gauntlet_testing")
        results_dir.mkdir(exist_ok=True)
        
        results_file = results_dir / f"v7p3r_simple_gauntlet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📁 Results saved: {results_file}")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive summary"""
        
        summary = self.results.get('summary', {})
        
        print(f"\n🏆 V7P3R Progressive Gauntlet Complete!")
        print("=" * 45)
        
        if summary:
            print(f"📊 Overall Performance:")
            print(f"   Total tests: {summary['total_tests']}")
            print(f"   Overall score: {summary['overall_score_rate']:.1%}")
            print(f"   Assessment: {summary['overall_assessment']}")
            
            print(f"\n🎯 Peak Performance:")
            print(f"   Best level: {summary['peak_level']}")
            print(f"   Best score: {summary['peak_score_rate']:.1%}")
            
            if summary['competitive_levels']:
                print(f"\n⚖️  Competitive levels: {', '.join(summary['competitive_levels'])}")
        
        print(f"\n📋 Level Breakdown:")
        for test in self.results['tests']:
            level = test['level']
            score = test['score_rate']
            assessment = test['performance_assessment']
            print(f"   {level}: {score:.1%} - {assessment}")


async def main():
    """Run the simplified V7P3R gauntlet"""
    
    gauntlet = V7P3RSimpleGauntlet()
    await gauntlet.run_progressive_gauntlet()


if __name__ == "__main__":
    asyncio.run(main())
