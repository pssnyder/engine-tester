#!/usr/bin/env python3
"""
🚀 Enhanced Engine Battle Framework with Dashboard Integration
============================================================

Complete automated engine testing system with:
- All challenge types (traditional, speed, puzzle, depth, tactical, position analysis)
- Real-time terminal dashboard
- Historical version gauntlets
- Comprehensive metrics and session management
- Modular, extensible architecture
"""

import asyncio
import sys
import threading
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import our framework components
from engine_battle_framework import (
    BattleFramework, EngineConfig, ChallengeType, BattleSession,
    TraditionalGameChallenge, SpeedChallenge
)
from advanced_challenges import (
    PuzzleSolveChallenge, DepthChallenge, PositionAnalysisChallenge, TacticalChallenge
)
from terminal_dashboard import TerminalDashboard, DashboardManager, DashboardConfig

class EnhancedBattleFramework:
    """Enhanced battle framework with dashboard integration"""
    
    def __init__(self, dashboard_enabled: bool = True):
        self.core_framework = BattleFramework()
        self.dashboard_enabled = dashboard_enabled
        self.dashboard_manager = None
        
        # Register all challenge types
        self._register_challenges()
        
        # Setup dashboard if enabled
        if dashboard_enabled:
            self._setup_dashboard()
    
    def _register_challenges(self):
        """Register all available challenge types"""
        self.core_framework.register_challenge(ChallengeType.TRADITIONAL_GAME, TraditionalGameChallenge())
        self.core_framework.register_challenge(ChallengeType.SPEED_CHALLENGE, SpeedChallenge())
        self.core_framework.register_challenge(ChallengeType.PUZZLE_SOLVE, PuzzleSolveChallenge())
        self.core_framework.register_challenge(ChallengeType.DEPTH_CHALLENGE, DepthChallenge())
        self.core_framework.register_challenge(ChallengeType.POSITION_ANALYSIS, PositionAnalysisChallenge())
        self.core_framework.register_challenge(ChallengeType.TACTICAL_CHALLENGE, TacticalChallenge())
    
    def _setup_dashboard(self):
        """Setup the dashboard manager"""
        dashboard_config = DashboardConfig(
            refresh_rate=1.0,
            max_recent_results=15,
            show_detailed_metrics=True,
            show_progress_bars=True
        )
        
        dashboard = TerminalDashboard(dashboard_config)
        self.dashboard_manager = DashboardManager(dashboard)
    
    def start_dashboard(self):
        """Start the dashboard in background"""
        if self.dashboard_manager:
            self.dashboard_manager.start_dashboard()
            time.sleep(1)  # Give dashboard time to start
    
    def stop_dashboard(self):
        """Stop the dashboard"""
        if self.dashboard_manager:
            self.dashboard_manager.stop_dashboard()
    
    async def run_comprehensive_battle(self, engine_configs: List[EngineConfig], 
                                     session_name: str = None) -> BattleSession:
        """Run a comprehensive battle with all challenge types"""
        
        if len(engine_configs) < 2:
            raise ValueError("Need at least 2 engines for battles")
        
        # Create session
        session_name = session_name or f"comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session = self.core_framework.create_session(session_name)
        
        # Start dashboard if enabled
        if self.dashboard_enabled:
            self.start_dashboard()
        
        try:
            # Run battles between all engine pairs
            total_pairs = len(engine_configs) * (len(engine_configs) - 1) // 2
            completed_pairs = 0
            
            for i in range(len(engine_configs)):
                for j in range(i + 1, len(engine_configs)):
                    engine1_config = engine_configs[i]
                    engine2_config = engine_configs[j]
                    
                    print(f"\n🎯 Battle: {engine1_config.name} vs {engine2_config.name}")
                    
                    # Run all challenge types
                    challenge_results = await self._run_all_challenges(
                        engine1_config, engine2_config, session.session_id
                    )
                    
                    # Add results to session
                    for result in challenge_results:
                        session.add_result(result)
                        
                        # Update dashboard
                        if self.dashboard_manager:
                            self.dashboard_manager.report_challenge_complete(result.__dict__)
                    
                    completed_pairs += 1
                    
                    # Update session stats on dashboard
                    if self.dashboard_manager:
                        self._update_dashboard_stats(session, completed_pairs, total_pairs)
        
        finally:
            # Save session and stop dashboard
            self.core_framework.save_session(session)
            
            if self.dashboard_enabled:
                # Give user time to see final results
                print(f"\n✅ Session completed! Results saved. Dashboard will close in 5 seconds...")
                time.sleep(5)
                self.stop_dashboard()
        
        return session
    
    async def _run_all_challenges(self, engine1_config: EngineConfig, engine2_config: EngineConfig,
                                session_id: str) -> List:
        """Run all challenge types between two engines"""
        results = []
        
        challenge_configs = [
            (ChallengeType.SPEED_CHALLENGE, {"game_count": 3, "time_per_game": 10.0}),
            (ChallengeType.PUZZLE_SOLVE, {"puzzle_count": 5, "time_limit": 15.0}),
            (ChallengeType.DEPTH_CHALLENGE, {"time_limit": 8.0}),
            (ChallengeType.TACTICAL_CHALLENGE, {"time_limit": 12.0}),
            (ChallengeType.POSITION_ANALYSIS, {"time_limit": 8.0}),
            (ChallengeType.TRADITIONAL_GAME, {"game_count": 2, "time_per_game": 30.0})
        ]
        
        total_challenges = len(challenge_configs)
        
        for i, (challenge_type, kwargs) in enumerate(challenge_configs):
            challenge_name = challenge_type.value.replace('_', ' ').title()
            
            # Update dashboard progress
            if self.dashboard_manager:
                progress = i / total_challenges
                self.dashboard_manager.update_challenge_progress(
                    challenge_name,
                    engine1_config.name,
                    engine2_config.name,
                    progress,
                    f"Challenge {i + 1} of {total_challenges}"
                )
            
            print(f"  🔄 Running {challenge_name}...")
            
            try:
                result = await self.core_framework.run_challenge(
                    challenge_type, engine1_config, engine2_config, session_id, **kwargs
                )
                results.append(result)
                
                # Quick result summary
                winner = result.winner or "Draw"
                exec_time = result.execution_time
                print(f"    ✅ {challenge_name}: Winner = {winner} ({exec_time:.1f}s)")
                
            except Exception as e:
                print(f"    ❌ {challenge_name}: Failed - {e}")
        
        return results
    
    def _update_dashboard_stats(self, session: BattleSession, completed_pairs: int, total_pairs: int):
        """Update dashboard with current session statistics"""
        if not self.dashboard_manager:
            return
        
        # Calculate engine stats
        engine_stats = {}
        challenge_type_stats = {}
        total_nodes = 0
        total_depth = 0
        depth_count = 0
        
        for result in session.results:
            # Engine wins
            if result.winner:
                if result.winner not in engine_stats:
                    engine_stats[result.winner] = {'wins': 0, 'total_games': 0}
                engine_stats[result.winner]['wins'] += 1
            
            # Total games for both engines
            for engine in [result.engine1, result.engine2]:
                if engine not in engine_stats:
                    engine_stats[engine] = {'wins': 0, 'total_games': 0}
                engine_stats[engine]['total_games'] += 1
            
            # Challenge type stats
            challenge_type = result.challenge_type.value
            challenge_type_stats[challenge_type] = challenge_type_stats.get(challenge_type, 0) + 1
            
            # Metrics aggregation
            if result.metrics:
                nodes = result.metrics.get('total_nodes_engine1', 0) + result.metrics.get('total_nodes_engine2', 0)
                total_nodes += nodes
                
                depth = result.metrics.get('max_depth', 0)
                if depth > 0:
                    total_depth += depth
                    depth_count += 1
        
        # Calculate averages
        completed_challenges = len(session.results)
        failed_challenges = len([r for r in session.results if r.status.value == 'failed'])
        avg_challenge_time = sum(r.execution_time for r in session.results) / max(completed_challenges, 1)
        avg_depth = total_depth / max(depth_count, 1)
        
        # Update dashboard
        session_stats = {
            'total_challenges': completed_challenges,
            'completed_challenges': completed_challenges - failed_challenges,
            'failed_challenges': failed_challenges,
            'engine_stats': engine_stats,
            'detailed_metrics': {
                'average_challenge_time': avg_challenge_time,
                'total_nodes_analyzed': total_nodes,
                'average_depth': avg_depth,
                'challenge_type_stats': challenge_type_stats
            }
        }
        
        self.dashboard_manager.update_session_stats(session_stats)
    
    async def run_historical_gauntlet(self, current_engine: EngineConfig, 
                                    historical_versions: List[EngineConfig],
                                    challenge_types: List[ChallengeType] = None) -> BattleSession:
        """Run current engine against historical versions"""
        
        challenge_types = challenge_types or [
            ChallengeType.SPEED_CHALLENGE,
            ChallengeType.PUZZLE_SOLVE,
            ChallengeType.TRADITIONAL_GAME
        ]
        
        session_name = f"gauntlet_{current_engine.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session = self.core_framework.create_session(session_name)
        
        if self.dashboard_enabled:
            self.start_dashboard()
        
        try:
            total_versions = len(historical_versions)
            
            for i, historical_engine in enumerate(historical_versions):
                print(f"\n🏟️ Gauntlet Round {i + 1}/{total_versions}: {current_engine.name} vs {historical_engine.name}")
                
                for challenge_type in challenge_types:
                    if self.dashboard_manager:
                        progress = (i * len(challenge_types) + challenge_types.index(challenge_type)) / (total_versions * len(challenge_types))
                        self.dashboard_manager.update_challenge_progress(
                            f"Gauntlet {challenge_type.value}",
                            current_engine.name,
                            historical_engine.name,
                            progress,
                            f"Round {i + 1}/{total_versions}"
                        )
                    
                    # Use appropriate challenge parameters
                    kwargs = self._get_challenge_kwargs(challenge_type)
                    
                    result = await self.core_framework.run_challenge(
                        challenge_type, current_engine, historical_engine, session.session_id, **kwargs
                    )
                    
                    session.add_result(result)
                    
                    if self.dashboard_manager:
                        self.dashboard_manager.report_challenge_complete(result.__dict__)
                        self._update_dashboard_stats(session, i + 1, total_versions)
        
        finally:
            self.core_framework.save_session(session)
            
            if self.dashboard_enabled:
                print(f"\n🏆 Gauntlet completed! Results saved. Dashboard will close in 5 seconds...")
                time.sleep(5)
                self.stop_dashboard()
        
        return session
    
    def _get_challenge_kwargs(self, challenge_type: ChallengeType) -> Dict[str, Any]:
        """Get appropriate parameters for each challenge type"""
        kwargs_map = {
            ChallengeType.SPEED_CHALLENGE: {"game_count": 2, "time_per_game": 8.0},
            ChallengeType.PUZZLE_SOLVE: {"puzzle_count": 3, "time_limit": 10.0},
            ChallengeType.DEPTH_CHALLENGE: {"time_limit": 6.0},
            ChallengeType.TACTICAL_CHALLENGE: {"time_limit": 8.0},
            ChallengeType.POSITION_ANALYSIS: {"time_limit": 6.0},
            ChallengeType.TRADITIONAL_GAME: {"game_count": 1, "time_per_game": 20.0}
        }
        return kwargs_map.get(challenge_type, {})
    
    def print_session_summary(self, session: BattleSession):
        """Print a detailed session summary"""
        print(f"\n{'=' * 60}")
        print(f"🏆 SESSION SUMMARY: {session.session_id}")
        print(f"{'=' * 60}")
        print(f"Total Challenges: {len(session.results)}")
        print(f"Session Duration: {session.get_duration():.1f} seconds")
        
        # Engine performance
        engine_wins = {}
        challenge_type_counts = {}
        
        for result in session.results:
            if result.winner:
                engine_wins[result.winner] = engine_wins.get(result.winner, 0) + 1
            
            challenge_type = result.challenge_type.value
            challenge_type_counts[challenge_type] = challenge_type_counts.get(challenge_type, 0) + 1
        
        print(f"\n🎯 Engine Performance:")
        for engine, wins in sorted(engine_wins.items(), key=lambda x: x[1], reverse=True):
            print(f"  {engine}: {wins} wins")
        
        print(f"\n📊 Challenge Types:")
        for challenge_type, count in challenge_type_counts.items():
            print(f"  {challenge_type.replace('_', ' ').title()}: {count}")
        
        print(f"\n📁 Results saved to: {session.get_results_file()}")

# Example usage and main function
async def main():
    """Main function demonstrating the enhanced framework"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Engine Battle Framework")
    parser.add_argument("--mode", choices=["comprehensive", "gauntlet", "demo"], 
                       default="demo", help="Battle mode")
    parser.add_argument("--no-dashboard", action="store_true", help="Disable dashboard")
    parser.add_argument("--engines", nargs="+", help="Engine names to battle")
    args = parser.parse_args()
    
    # Create framework
    framework = EnhancedBattleFramework(dashboard_enabled=not args.no_dashboard)
    
    # Setup engine configurations
    # These paths should be adjusted to match your actual engine locations
    engine_configs = [
        EngineConfig(
            name="V7P3R",
            path="s:/Maker Stuff/Programming/Chess Engines/V7P3R Chess Engine/v7p3r-chess-engine",
            executable="python",
            args=["play_chess.py"],
            type="python"
        ),
        EngineConfig(
            name="SlowMate",
            path="s:/Maker Stuff/Programming/Chess Engines/SlowMate Chess Engine/slowmate-chess-engine/src",
            executable="python",
            args=["slowmate_uci.py"],
            type="python"
        )
    ]
    
    # Add C0BR4 control engine if available
    cobra_path = "s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester/downloaded_engines/C0BR4.exe"
    if Path(cobra_path).exists():
        engine_configs.append(
            EngineConfig(
                name="C0BR4",
                path=str(Path(cobra_path).parent),
                executable=str(Path(cobra_path)),
                args=[],
                type="executable"
            )
        )
    
    try:
        if args.mode == "comprehensive":
            print("🚀 Starting comprehensive battle between all engines...")
            session = await framework.run_comprehensive_battle(engine_configs, "comprehensive_test")
            framework.print_session_summary(session)
        
        elif args.mode == "gauntlet":
            if len(engine_configs) < 2:
                print("❌ Need at least 2 engines for gauntlet mode")
                return
            
            current_engine = engine_configs[0]  # Use first as current
            historical_versions = engine_configs[1:]  # Rest as historical
            
            print(f"🏟️ Starting gauntlet: {current_engine.name} vs historical versions...")
            session = await framework.run_historical_gauntlet(current_engine, historical_versions)
            framework.print_session_summary(session)
        
        else:  # demo mode
            print("🎮 Starting demo battle (limited challenges)...")
            
            # Run just a quick demo with 2 engines
            demo_engines = engine_configs[:2]
            session = framework.core_framework.create_session("demo_session")
            
            if framework.dashboard_enabled:
                framework.start_dashboard()
            
            try:
                # Run a few quick challenges
                challenges = [
                    (ChallengeType.SPEED_CHALLENGE, {"game_count": 2, "time_per_game": 5.0}),
                    (ChallengeType.PUZZLE_SOLVE, {"puzzle_count": 3, "time_limit": 8.0})
                ]
                
                for challenge_type, kwargs in challenges:
                    result = await framework.core_framework.run_challenge(
                        challenge_type, demo_engines[0], demo_engines[1], 
                        session.session_id, **kwargs
                    )
                    session.add_result(result)
                    
                    if framework.dashboard_manager:
                        framework.dashboard_manager.report_challenge_complete(result.__dict__)
                        framework._update_dashboard_stats(session, 1, 1)
                
                framework.core_framework.save_session(session)
                framework.print_session_summary(session)
                
            finally:
                if framework.dashboard_enabled:
                    print("Demo completed! Dashboard will close in 3 seconds...")
                    time.sleep(3)
                    framework.stop_dashboard()
    
    except KeyboardInterrupt:
        print("\n🛑 Battle interrupted by user")
        framework.stop_dashboard()
    
    except Exception as e:
        print(f"❌ Error during battle: {e}")
        framework.stop_dashboard()
        raise

if __name__ == "__main__":
    asyncio.run(main())
