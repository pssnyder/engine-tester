#!/usr/bin/env python3
"""
V7P3R Weak Engine Rating Assessment
===================================

Since V7P3R struggles against default Stockfish, let's test against 
progressively weaker engines to establish a rating baseline.

Strategy:
1. Test against extremely weak configurations
2. Find where V7P3R dominates (>80% score)  
3. Find where V7P3R struggles (<20% score)
4. Estimate rating from the competitive range
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add framework to path
sys.path.append(str(Path(__file__).parent / 'automated_battle_framework'))

from engine_battle_framework import BattleFramework, ChallengeType, EngineConfig, EngineType

class V7P3RWeakEngineAssessment:
    """Rating assessment against very weak opponents"""
    
    def __init__(self):
        self.framework = BattleFramework()
        
        # Test progression from extremely weak to moderately weak
        self.test_levels = [
            ("slowmate", "SlowMate baseline"),
            ("stockfish_1s", "Stockfish 1-second time limit"),
            ("stockfish_0.5s", "Stockfish 0.5-second time limit"),
            ("stockfish_0.2s", "Stockfish 0.2-second time limit"),
            ("stockfish_0.1s", "Stockfish 0.1-second time limit"),
        ]
        
        self.results = {
            'test_start': datetime.now().isoformat(),
            'v7p3r_version': 'v7.0',
            'test_strategy': 'weak_engine_baseline',
            'tests': [],
            'rating_analysis': {}
        }
    
    async def test_vs_slowmate(self, num_tests: int = 5):
        """Test against SlowMate as baseline"""
        
        print(f"\n🎯 Testing vs SlowMate (baseline) - {num_tests} tests")
        print("=" * 45)
        
        session_id = await self.framework.create_battle_session(
            "V7P3R_vs_SlowMate_Rating",
            "V7P3R vs SlowMate for rating baseline"
        )
        
        wins = 0
        draws = 0 
        losses = 0
        
        for test_num in range(1, num_tests + 1):
            print(f"🎮 Test {test_num}/{num_tests}: ", end='')
            
            try:
                result = await self.framework.run_challenge(
                    session_id,
                    ChallengeType.SPEED_CHALLENGE,
                    "V7P3R_Current",
                    "SlowMate_Current",
                    time_limit=3.0  # 3 seconds per position
                )
                
                if result:
                    if result.winner == "V7P3R_Current":
                        wins += 1
                        print("✅ V7P3R wins")
                    elif result.winner == "SlowMate_Current":
                        losses += 1
                        print("❌ SlowMate wins")
                    else:
                        draws += 1
                        print("⚫ Draw")
                else:
                    print("💥 Test failed")
                    
            except Exception as e:
                print(f"💥 Test crashed: {e}")
        
        total_tests = wins + draws + losses
        score_rate = (wins + 0.5 * draws) / total_tests if total_tests > 0 else 0.0
        
        test_result = {
            'opponent': 'SlowMate_Current',
            'description': 'SlowMate baseline test',
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'total_tests': total_tests,
            'score_rate': score_rate
        }
        
        self.results['tests'].append(test_result)
        
        print(f"📊 vs SlowMate: {wins}W-{draws}D-{losses}L ({score_rate:.1%})")
        return test_result
    
    async def test_vs_time_limited_stockfish(self, time_limit: float, level_name: str, num_tests: int = 5):
        """Test against time-limited Stockfish"""
        
        print(f"\n🎯 Testing vs {level_name} - {num_tests} tests")
        print("=" * 45)
        
        # Configure Stockfish with time limit
        stockfish_path = "s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester/engines/Stockfish/stockfish-windows-x86-64-avx2.exe"
        
        engine_name = f"Stockfish_{level_name.replace(' ', '_')}"
        
        # Remove if exists
        if engine_name in self.framework.engines:
            del self.framework.engines[engine_name]
        
        stockfish_config = EngineConfig(
            name=engine_name,
            engine_type=EngineType.EXE_CONTROL,
            path=stockfish_path,
            version=f"17.1_time_{time_limit}s"
        )
        
        self.framework.add_engine(stockfish_config)
        print(f"✅ Added {engine_name}")
        
        session_id = await self.framework.create_battle_session(
            f"V7P3R_vs_{level_name}",
            f"V7P3R vs {level_name}"
        )
        
        wins = 0
        draws = 0
        losses = 0
        
        for test_num in range(1, num_tests + 1):
            print(f"🎮 Test {test_num}/{num_tests}: ", end='')
            
            try:
                result = await self.framework.run_challenge(
                    session_id,
                    ChallengeType.SPEED_CHALLENGE,
                    "V7P3R_Current",
                    engine_name,
                    time_limit=time_limit  # Use the same time limit for both engines
                )
                
                if result:
                    if result.winner == "V7P3R_Current":
                        wins += 1
                        print("✅ V7P3R wins")
                    elif result.winner == engine_name:
                        losses += 1
                        print("❌ Stockfish wins")
                    else:
                        draws += 1
                        print("⚫ Draw")
                else:
                    print("💥 Test failed")
                    
            except Exception as e:
                print(f"💥 Test crashed: {e}")
        
        total_tests = wins + draws + losses
        score_rate = (wins + 0.5 * draws) / total_tests if total_tests > 0 else 0.0
        
        test_result = {
            'opponent': engine_name,
            'description': level_name,
            'time_limit': time_limit,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'total_tests': total_tests,
            'score_rate': score_rate
        }
        
        self.results['tests'].append(test_result)
        
        print(f"📊 vs {level_name}: {wins}W-{draws}D-{losses}L ({score_rate:.1%})")
        return test_result
    
    async def run_weak_engine_assessment(self):
        """Run complete weak engine assessment"""
        
        print("🚀 V7P3R Weak Engine Rating Assessment")
        print("=" * 50)
        print("🎯 Strategy: Find competitive range against weak engines")
        print("📊 Goal: Establish rating baseline from dominated->competitive->struggling")
        
        try:
            # Test vs SlowMate first (known baseline)
            slowmate_result = await self.test_vs_slowmate(num_tests=5)
            
            # Test vs progressively faster Stockfish
            for level_name, description in [
                ("Stockfish_1s", "Stockfish 1-second limit"),
                ("Stockfish_0.5s", "Stockfish 0.5-second limit"),
                ("Stockfish_0.2s", "Stockfish 0.2-second limit"),
                ("Stockfish_0.1s", "Stockfish 0.1-second limit"),
            ]:
                
                time_limit = float(level_name.split('_')[1].replace('s', ''))
                
                result = await self.test_vs_time_limited_stockfish(
                    time_limit=time_limit,
                    level_name=description,
                    num_tests=5
                )
                
                # Decision logic
                if result['score_rate'] < 0.1:
                    print(f"\n⚠️  V7P3R overwhelmed by {description} ({result['score_rate']:.1%}) - stopping")
                    break
                elif result['score_rate'] > 0.9:
                    print(f"✅ V7P3R dominates {description} ({result['score_rate']:.1%}) - continuing")
                else:
                    print(f"🎯 Competitive range with {description} ({result['score_rate']:.1%})")
                
                # Brief pause
                await asyncio.sleep(2.0)
            
            # Analyze results
            self.analyze_rating()
            self.save_results()
            
        except KeyboardInterrupt:
            print(f"\n⚠️  Assessment interrupted")
            self.save_results()
        except Exception as e:
            print(f"\n💥 Assessment crashed: {e}")
            self.save_results()
    
    def analyze_rating(self):
        """Analyze rating from test results"""
        
        if not self.results['tests']:
            return
        
        # Find performance patterns
        dominated_opponents = []  # >80% score
        competitive_opponents = []  # 20-80% score  
        struggling_opponents = []  # <20% score
        
        for test in self.results['tests']:
            score = test['score_rate']
            opponent = test['description']
            
            if score > 0.8:
                dominated_opponents.append((opponent, score))
            elif score > 0.2:
                competitive_opponents.append((opponent, score))
            else:
                struggling_opponents.append((opponent, score))
        
        # Estimate rating range
        rating_estimate = self.estimate_rating_from_results()
        
        self.results['rating_analysis'] = {
            'dominated_opponents': dominated_opponents,
            'competitive_opponents': competitive_opponents,
            'struggling_opponents': struggling_opponents,
            'estimated_rating_range': rating_estimate,
            'analysis_summary': self.generate_rating_summary()
        }
    
    def estimate_rating_from_results(self) -> dict:
        """Estimate rating from performance against known opponents"""
        
        # Rough rating estimates for our test opponents
        opponent_ratings = {
            'SlowMate baseline test': 800,  # Beginner level
            'Stockfish 1-second limit': 1200,  # Fast but weak
            'Stockfish 0.5-second limit': 1000,  # Very fast, weaker
            'Stockfish 0.2-second limit': 800,   # Extremely fast, very weak
            'Stockfish 0.1-second limit': 600,   # Almost random
        }
        
        estimated_performances = []
        
        for test in self.results['tests']:
            description = test['description']
            score_rate = test['score_rate']
            
            if description in opponent_ratings and test['total_tests'] >= 3:
                opponent_rating = opponent_ratings[description]
                
                # Calculate performance rating
                if score_rate >= 0.99:
                    performance = opponent_rating + 400
                elif score_rate <= 0.01:
                    performance = opponent_rating - 400
                else:
                    import math
                    try:
                        performance = opponent_rating + 400 * math.log10(score_rate / (1 - score_rate))
                    except (ValueError, ZeroDivisionError):
                        continue
                
                estimated_performances.append((description, performance, score_rate))
        
        if estimated_performances:
            # Weight by reliability (higher score rates are more reliable for rating)
            total_weight = 0
            weighted_rating = 0
            
            for desc, perf, score in estimated_performances:
                # Weight by distance from 50% (more extreme scores are more informative)
                weight = abs(score - 0.5) + 0.1  # Minimum weight
                weighted_rating += perf * weight
                total_weight += weight
            
            if total_weight > 0:
                final_estimate = weighted_rating / total_weight
                
                # Calculate confidence range
                performances = [p[1] for p in estimated_performances]
                if len(performances) > 1:
                    import statistics
                    std_dev = statistics.stdev(performances)
                    confidence_range = (final_estimate - std_dev, final_estimate + std_dev)
                else:
                    confidence_range = (final_estimate - 100, final_estimate + 100)
                
                return {
                    'estimated_rating': final_estimate,
                    'confidence_range': confidence_range,
                    'performance_details': estimated_performances
                }
        
        return {
            'estimated_rating': None,
            'confidence_range': None,
            'performance_details': []
        }
    
    def generate_rating_summary(self) -> str:
        """Generate summary of rating analysis"""
        
        rating_estimate = self.results['rating_analysis'].get('estimated_rating_range', {})
        
        if rating_estimate.get('estimated_rating'):
            rating = rating_estimate['estimated_rating']
            range_low, range_high = rating_estimate['confidence_range']
            
            if rating < 800:
                level = "Beginner"
            elif rating < 1200:
                level = "Novice" 
            elif rating < 1600:
                level = "Intermediate"
            elif rating < 2000:
                level = "Advanced"
            else:
                level = "Expert"
            
            return f"V7P3R v7.0 estimated at {rating:.0f} ELO ({range_low:.0f}-{range_high:.0f}), {level} level"
        else:
            return "Insufficient data for rating estimate"
    
    def save_results(self):
        """Save assessment results"""
        
        self.results['test_end'] = datetime.now().isoformat()
        
        # Save detailed results
        results_dir = Path("gauntlet_testing")
        results_dir.mkdir(exist_ok=True)
        
        results_file = results_dir / f"v7p3r_weak_engine_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📁 Results saved: {results_file}")
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive assessment summary"""
        
        print(f"\n🏆 V7P3R Weak Engine Assessment Complete!")
        print("=" * 50)
        
        if self.results['tests']:
            print(f"📊 Test Results:")
            for test in self.results['tests']:
                opponent = test['description']
                score = test['score_rate']
                wins = test['wins']
                draws = test['draws']
                losses = test['losses']
                print(f"   {opponent}: {wins}W-{draws}D-{losses}L ({score:.1%})")
        
        # Rating analysis
        if 'rating_analysis' in self.results:
            analysis = self.results['rating_analysis']
            
            if analysis.get('estimated_rating_range', {}).get('estimated_rating'):
                rating_info = analysis['estimated_rating_range']
                rating = rating_info['estimated_rating']
                range_low, range_high = rating_info['confidence_range']
                
                print(f"\n🎯 Rating Estimate:")
                print(f"   📈 ELO: {rating:.0f}")
                print(f"   📊 Range: {range_low:.0f} - {range_high:.0f}")
                print(f"   📋 Summary: {analysis['analysis_summary']}")
            
            # Performance categories
            dominated = analysis.get('dominated_opponents', [])
            competitive = analysis.get('competitive_opponents', [])
            struggling = analysis.get('struggling_opponents', [])
            
            if dominated:
                print(f"\n✅ Dominated opponents (>80%):")
                for opponent, score in dominated:
                    print(f"   {opponent}: {score:.1%}")
            
            if competitive:
                print(f"\n⚖️  Competitive opponents (20-80%):")
                for opponent, score in competitive:
                    print(f"   {opponent}: {score:.1%}")
            
            if struggling:
                print(f"\n❌ Struggling opponents (<20%):")
                for opponent, score in struggling:
                    print(f"   {opponent}: {score:.1%}")


async def main():
    """Run the weak engine assessment"""
    
    assessment = V7P3RWeakEngineAssessment()
    await assessment.run_weak_engine_assessment()


if __name__ == "__main__":
    asyncio.run(main())
