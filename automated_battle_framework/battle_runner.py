#!/usr/bin/env python3
"""
🚀 Simple Battle Runner Script
=============================

A streamlined runner for the engine battle framework that works with your existing engines.
Focuses on basic functionality and easy execution.

Usage:
    python battle_runner.py --mode demo
    python battle_runner.py --mode comprehensive
    python battle_runner.py --dashboard
"""

import asyncio
import sys
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Import framework components
from engine_battle_framework import BattleFramework, ChallengeType
from terminal_dashboard import TerminalDashboard, DashboardManager, DashboardConfig

class SimpleBattleRunner:
    """Simplified battle runner for automated engine testing"""
    
    def __init__(self, enable_dashboard: bool = False):
        self.framework = BattleFramework()
        self.enable_dashboard = enable_dashboard
        self.dashboard_manager = None
        
        if enable_dashboard:
            self._setup_dashboard()
    
    def _setup_dashboard(self):
        """Setup dashboard for real-time monitoring"""
        config = DashboardConfig(
            refresh_rate=1.0,
            max_recent_results=10,
            show_detailed_metrics=True
        )
        dashboard = TerminalDashboard(config)
        self.dashboard_manager = DashboardManager(dashboard)
    
    def start_dashboard(self):
        """Start dashboard in background"""
        if self.dashboard_manager:
            self.dashboard_manager.start_dashboard()
            time.sleep(1)  # Give dashboard time to initialize
    
    def stop_dashboard(self):
        """Stop the dashboard"""
        if self.dashboard_manager:
            self.dashboard_manager.stop_dashboard()
    
    async def run_quick_demo(self) -> str:
        """Run a quick demo battle between V7P3R and SlowMate"""
        print("🎮 Starting Quick Demo Battle...")
        
        # Create session
        session_id = await self.framework.create_battle_session(
            "Quick_Demo_Battle",
            "Quick demonstration of engine battle framework"
        )
        
        print(f"📋 Session ID: {session_id}")
        
        if self.enable_dashboard:
            self.start_dashboard()
        
        try:
            # Run speed challenge
            print("\n⚡ Running Speed Challenge...")
            if self.dashboard_manager:
                self.dashboard_manager.update_challenge_progress(
                    "Speed Challenge", "V7P3R", "SlowMate", 0.0, "Starting..."
                )
            
            speed_result = await self.framework.run_challenge(
                session_id,
                ChallengeType.SPEED_CHALLENGE,
                "V7P3R_Current",
                "SlowMate_Current",
                time_limit=3.0
            )
            
            print(f"  ✅ Speed Winner: {speed_result.winner}")
            print(f"  ⏱️  Duration: {speed_result.execution_time:.1f}s")
            
            if self.dashboard_manager:
                self.dashboard_manager.report_challenge_complete({
                    'status': 'completed',
                    'winner': speed_result.winner,
                    'challenge_type': 'speed_challenge',
                    'execution_time': speed_result.execution_time,
                    'timestamp': speed_result.timestamp.isoformat()
                })
            
            # Brief pause
            await asyncio.sleep(1)
            
            # Run traditional game
            print("\n♟️  Running Traditional Game...")
            if self.dashboard_manager:
                self.dashboard_manager.update_challenge_progress(
                    "Traditional Game", "V7P3R", "SlowMate", 0.5, "Playing game..."
                )
            
            game_result = await self.framework.run_challenge(
                session_id,
                ChallengeType.TRADITIONAL_GAME,
                "V7P3R_Current",
                "SlowMate_Current",
                time_control=8.0,
                max_moves=40
            )
            
            print(f"  ✅ Game Winner: {game_result.winner}")
            print(f"  🎯 Moves: {game_result.result_details.get('move_count', 'N/A')}")
            print(f"  ⏱️  Duration: {game_result.execution_time:.1f}s")
            
            if self.dashboard_manager:
                self.dashboard_manager.report_challenge_complete({
                    'status': 'completed',
                    'winner': game_result.winner,
                    'challenge_type': 'traditional_game',
                    'execution_time': game_result.execution_time,
                    'timestamp': game_result.timestamp.isoformat()
                })
            
            # Save session
            self.framework.save_session(session_id)
            
            # Print summary
            summary = self.framework.get_session_summary(session_id)
            print(f"\n📊 Demo Complete!")
            print(f"   Total Challenges: {summary['total_challenges']}")
            print(f"   Engine Wins: {summary['engine_wins']}")
            print(f"   Duration: {summary['duration']:.1f}s")
            
            return session_id
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            raise
        
        finally:
            if self.enable_dashboard:
                print("\n🎯 Demo completed! Dashboard will close in 3 seconds...")
                time.sleep(3)
                self.stop_dashboard()
    
    async def run_comprehensive_battle(self) -> str:
        """Run comprehensive battle with multiple challenge types"""
        print("🚀 Starting Comprehensive Battle...")
        
        session_id = await self.framework.create_battle_session(
            "Comprehensive_Engine_Battle",
            "Full battle suite between V7P3R and SlowMate engines"
        )
        
        print(f"📋 Session ID: {session_id}")
        
        if self.enable_dashboard:
            self.start_dashboard()
        
        challenge_configs = [
            ("Speed Challenge", ChallengeType.SPEED_CHALLENGE, {"time_limit": 5.0}),
            ("Traditional Game 1", ChallengeType.TRADITIONAL_GAME, {"time_control": 10.0, "max_moves": 50}),
            ("Speed Challenge 2", ChallengeType.SPEED_CHALLENGE, {"time_limit": 8.0}),
            ("Traditional Game 2", ChallengeType.TRADITIONAL_GAME, {"time_control": 15.0, "max_moves": 60})
        ]
        
        total_challenges = len(challenge_configs)
        
        try:
            for i, (name, challenge_type, kwargs) in enumerate(challenge_configs):
                print(f"\n🎯 Challenge {i + 1}/{total_challenges}: {name}")
                
                if self.dashboard_manager:
                    progress = i / total_challenges
                    self.dashboard_manager.update_challenge_progress(
                        name, "V7P3R", "SlowMate", progress, f"Challenge {i + 1}/{total_challenges}"
                    )
                
                result = await self.framework.run_challenge(
                    session_id,
                    challenge_type,
                    "V7P3R_Current",
                    "SlowMate_Current",
                    **kwargs
                )
                
                print(f"  ✅ Winner: {result.winner}")
                print(f"  ⏱️  Duration: {result.execution_time:.1f}s")
                
                if self.dashboard_manager:
                    self.dashboard_manager.report_challenge_complete({
                        'status': 'completed',
                        'winner': result.winner,
                        'challenge_type': challenge_type.value,
                        'execution_time': result.execution_time,
                        'timestamp': result.timestamp.isoformat()
                    })
                    
                    # Update session stats
                    session_summary = self.framework.get_session_summary(session_id)
                    self.dashboard_manager.update_session_stats({
                        'total_challenges': session_summary['total_challenges'],
                        'completed_challenges': session_summary['completed_challenges'],
                        'engine_stats': {
                            engine: {'wins': wins, 'total_games': session_summary['total_challenges']}
                            for engine, wins in session_summary['engine_wins'].items()
                        }
                    })
                
                # Brief pause between challenges
                await asyncio.sleep(1)
            
            # Save session
            self.framework.save_session(session_id)
            
            # Final summary
            summary = self.framework.get_session_summary(session_id)
            print(f"\n🏆 Comprehensive Battle Complete!")
            print(f"   Total Challenges: {summary['total_challenges']}")
            print(f"   Completed: {summary['completed_challenges']}")
            print(f"   Engine Wins: {summary['engine_wins']}")
            print(f"   Total Duration: {summary['duration']:.1f}s")
            
            return session_id
            
        except Exception as e:
            print(f"❌ Comprehensive battle failed: {e}")
            raise
        
        finally:
            if self.enable_dashboard:
                print("\n🎯 Battle completed! Dashboard will close in 5 seconds...")
                time.sleep(5)
                self.stop_dashboard()
    
    async def run_gauntlet(self, engine_names: List[str]) -> str:
        """Run gauntlet between multiple engines"""
        if len(engine_names) < 2:
            raise ValueError("Need at least 2 engines for gauntlet")
        
        print(f"🏟️ Starting Engine Gauntlet: {' vs '.join(engine_names)}")
        
        session_id = await self.framework.create_battle_session(
            f"Gauntlet_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            f"Gauntlet battle between: {', '.join(engine_names)}"
        )
        
        if self.enable_dashboard:
            self.start_dashboard()
        
        try:
            # Run battles between all pairs
            total_pairs = len(engine_names) * (len(engine_names) - 1) // 2
            completed_pairs = 0
            
            for i in range(len(engine_names)):
                for j in range(i + 1, len(engine_names)):
                    engine1 = engine_names[i]
                    engine2 = engine_names[j]
                    
                    print(f"\n⚔️  Battle {completed_pairs + 1}/{total_pairs}: {engine1} vs {engine2}")
                    
                    # Run challenges between this pair
                    challenge_types = [ChallengeType.SPEED_CHALLENGE, ChallengeType.TRADITIONAL_GAME]
                    
                    for challenge_type in challenge_types:
                        challenge_name = challenge_type.value.replace('_', ' ').title()
                        
                        if self.dashboard_manager:
                            progress = (completed_pairs * len(challenge_types) + challenge_types.index(challenge_type)) / (total_pairs * len(challenge_types))
                            self.dashboard_manager.update_challenge_progress(
                                challenge_name, engine1, engine2, progress,
                                f"Pair {completed_pairs + 1}/{total_pairs}"
                            )
                        
                        kwargs = {"time_limit": 6.0} if challenge_type == ChallengeType.SPEED_CHALLENGE else {"time_control": 12.0, "max_moves": 50}
                        
                        result = await self.framework.run_challenge(
                            session_id,
                            challenge_type,
                            f"{engine1}_Current",
                            f"{engine2}_Current",
                            **kwargs
                        )
                        
                        print(f"    {challenge_name}: {result.winner} ({result.execution_time:.1f}s)")
                        
                        if self.dashboard_manager:
                            self.dashboard_manager.report_challenge_complete({
                                'status': 'completed',
                                'winner': result.winner,
                                'challenge_type': challenge_type.value,
                                'execution_time': result.execution_time,
                                'timestamp': result.timestamp.isoformat()
                            })
                    
                    completed_pairs += 1
                    await asyncio.sleep(0.5)  # Brief pause
            
            # Save and summarize
            self.framework.save_session(session_id)
            summary = self.framework.get_session_summary(session_id)
            
            print(f"\n🏆 Gauntlet Complete!")
            print(f"   Total Battles: {total_pairs}")
            print(f"   Total Challenges: {summary['total_challenges']}")
            print(f"   Engine Wins: {summary['engine_wins']}")
            print(f"   Duration: {summary['duration']:.1f}s")
            
            return session_id
            
        except Exception as e:
            print(f"❌ Gauntlet failed: {e}")
            raise
        
        finally:
            if self.enable_dashboard:
                print("\n🎯 Gauntlet completed! Dashboard will close in 5 seconds...")
                time.sleep(5)
                self.stop_dashboard()

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Engine Battle Runner")
    parser.add_argument("--mode", choices=["demo", "comprehensive", "gauntlet"], 
                       default="demo", help="Battle mode to run")
    parser.add_argument("--dashboard", action="store_true", help="Enable real-time dashboard")
    parser.add_argument("--engines", nargs="+", default=["V7P3R", "SlowMate"], 
                       help="Engine names for gauntlet mode")
    
    args = parser.parse_args()
    
    print("🤖 Engine Battle Framework Runner")
    print("=" * 40)
    
    runner = SimpleBattleRunner(enable_dashboard=args.dashboard)
    
    try:
        if args.mode == "demo":
            session_id = await runner.run_quick_demo()
            print(f"\n✅ Demo session saved: {session_id}")
        
        elif args.mode == "comprehensive":
            session_id = await runner.run_comprehensive_battle()
            print(f"\n✅ Comprehensive session saved: {session_id}")
        
        elif args.mode == "gauntlet":
            session_id = await runner.run_gauntlet(args.engines)
            print(f"\n✅ Gauntlet session saved: {session_id}")
        
        print("\n🎯 Battle Framework Session Complete!")
        print("📁 Results saved in 'battle_results/' directory")
        
    except KeyboardInterrupt:
        print("\n🛑 Battle interrupted by user")
        runner.stop_dashboard()
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        runner.stop_dashboard()
        sys.exit(1)

if __name__ == "__main__":
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    if script_dir.name == "automated_battle_framework":
        print(f"🎯 Running from: {script_dir}")
    
    asyncio.run(main())
