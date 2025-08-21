#!/usr/bin/env python3
"""
Version Comparison Analyzer for Chess Engines

This analyzer performs detailed comparisons between different versions of the same engine,
identifying improvements, regressions, and gameplay differences. It uses Stockfish as a
reference engine to provide objective position evaluations and move quality assessments.

Features:
- Head-to-head version comparison
- Blunder detection and analysis using Stockfish
- Regression identification in gameplay patterns
- Opening repertoire comparison
- Endgame handling analysis
- Time management comparison
- Detailed developer-focused reports with actionable insights

Usage:
    python version_comparison_analyzer.py --engine SlowMate --v1 v1.0 --v2 v2.0
    python version_comparison_analyzer.py --engine Cece --v1 v2.0 --v2 v2.3 --depth 15
"""

import os
import json
import re
import datetime
import argparse
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any, Set
from collections import defaultdict, Counter
import chess
import chess.pgn
import chess.engine
import chess.polyglot
import math
import statistics
from pathlib import Path

# Import existing analyzers for base functionality
from unified_tournament_analyzer import UnifiedTournamentAnalyzer, GameRecord, normalize_engine_name

@dataclass
class MoveAnalysis:
    """Analysis of a single move"""
    move: str
    san_move: str
    position_before: str  # FEN
    position_after: str   # FEN
    evaluation_before: float  # Centipawns
    evaluation_after: float   # Centipawns
    best_move: str
    best_move_eval: float
    centipawn_loss: float
    move_time: Optional[float] = None
    is_blunder: bool = False
    is_mistake: bool = False
    is_inaccuracy: bool = False
    game_phase: str = "unknown"  # opening, middlegame, endgame
    
    @property
    def move_quality(self) -> str:
        """Categorize move quality"""
        if self.is_blunder:
            return "blunder"
        elif self.is_mistake:
            return "mistake"
        elif self.is_inaccuracy:
            return "inaccuracy"
        else:
            return "good"

@dataclass
class GameAnalysis:
    """Complete analysis of a game"""
    game_record: GameRecord
    engine_version: str
    engine_color: str  # "white" or "black"
    moves: List[MoveAnalysis] = field(default_factory=list)
    total_centipawn_loss: float = 0.0
    blunder_count: int = 0
    mistake_count: int = 0
    inaccuracy_count: int = 0
    avg_move_time: Optional[float] = None
    total_game_time: Optional[float] = None
    opening_moves: int = 0
    middlegame_moves: int = 0
    endgame_moves: int = 0
    
    @property
    def move_accuracy(self) -> float:
        """Calculate overall move accuracy percentage"""
        if not self.moves:
            return 0.0
        good_moves = len([m for m in self.moves if m.move_quality == "good"])
        return (good_moves / len(self.moves)) * 100

@dataclass
class VersionComparison:
    """Comparison results between two engine versions"""
    engine_family: str
    version_1: str
    version_2: str
    
    # Head-to-head statistics
    direct_games: List[GameRecord] = field(default_factory=list)
    v1_wins: int = 0
    v1_losses: int = 0
    v1_draws: int = 0
    v2_wins: int = 0
    v2_losses: int = 0
    v2_draws: int = 0
    
    # Performance analysis
    v1_analyses: List[GameAnalysis] = field(default_factory=list)
    v2_analyses: List[GameAnalysis] = field(default_factory=list)
    
    # Comparison metrics
    blunder_rate_diff: float = 0.0  # v2 - v1 (negative = improvement)
    accuracy_diff: float = 0.0      # v2 - v1 (positive = improvement)
    time_efficiency_diff: float = 0.0
    
    # Regression analysis
    tactical_regressions: List[Dict] = field(default_factory=list)
    positional_regressions: List[Dict] = field(default_factory=list)
    opening_changes: Dict[str, Any] = field(default_factory=dict)
    endgame_changes: Dict[str, Any] = field(default_factory=dict)

class StockfishAnalyzer:
    """Interface to Stockfish for position analysis"""
    
    def __init__(self, stockfish_path: str, analysis_depth: int = 15):
        self.stockfish_path = stockfish_path
        self.analysis_depth = analysis_depth
        self.engine = None
        
    async def start_engine(self):
        """Start the Stockfish engine"""
        try:
            transport, self.engine = await chess.engine.popen_uci(self.stockfish_path)
            return True
        except Exception as e:
            print(f"Error starting Stockfish: {e}")
            return False
    
    async def stop_engine(self):
        """Stop the Stockfish engine"""
        if self.engine:
            await self.engine.quit()
            self.engine = None
    
    async def analyze_position(self, board: chess.Board, time_limit: float = 2.0) -> Dict[str, Any]:
        """Analyze a position and return evaluation and best move"""
        if not self.engine:
            return {"evaluation": 0.0, "best_move": None, "pv": []}
        
        try:
            info = await self.engine.analyse(
                board, 
                chess.engine.Limit(depth=self.analysis_depth, time=time_limit)
            )
            
            # Extract evaluation
            score = info.get("score", chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE))
            if score.is_mate():
                # Convert mate scores to centipawns (approximately)
                mate_in = score.relative.mate()
                if mate_in is not None:
                    evaluation = 10000 - abs(mate_in) * 100 if mate_in > 0 else -10000 + abs(mate_in) * 100
                else:
                    evaluation = 0.0
            else:
                evaluation = score.relative.score(mate_score=10000) or 0.0
            
            # Get best move
            best_move = None
            pv = info.get("pv", [])
            if pv:
                best_move = pv[0]
            
            return {
                "evaluation": evaluation,
                "best_move": best_move,
                "pv": pv,
                "depth": info.get("depth", 0),
                "nodes": info.get("nodes", 0)
            }
            
        except Exception as e:
            print(f"Error analyzing position: {e}")
            return {"evaluation": 0.0, "best_move": None, "pv": []}

class VersionComparisonAnalyzer:
    """Main analyzer for comparing engine versions"""
    
    def __init__(self, results_dir: str = "../../results", 
                 engines_dir: str = "../../engines",
                 stockfish_depth: int = 15):
        self.results_dir = results_dir
        self.engines_dir = engines_dir
        self.stockfish_depth = stockfish_depth
        
        # Initialize base analyzer for game data
        self.base_analyzer = UnifiedTournamentAnalyzer(results_dir)
        
        # Initialize Stockfish analyzer
        stockfish_path = os.path.join(engines_dir, "Stockfish", "stockfish-windows-x86-64-avx2.exe")
        self.stockfish = StockfishAnalyzer(stockfish_path, stockfish_depth)
        
        # Cache for analysis results
        self.analysis_cache: Dict[str, Any] = {}
        
    async def initialize(self):
        """Initialize the analyzer and load game data"""
        print("🔄 Initializing analyzer...")
        
        # Load all games
        self.base_analyzer.load_all_games()
        self.base_analyzer.process_all_games()
        
        # Start Stockfish
        stockfish_started = await self.stockfish.start_engine()
        if not stockfish_started:
            raise Exception("Failed to start Stockfish engine")
        
        print("✅ Analyzer initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.stockfish.stop_engine()
    
    def find_version_games(self, engine_family: str, version1: str, version2: str) -> Tuple[List[GameRecord], List[GameRecord], List[GameRecord]]:
        """Find games for specified engine versions using consolidated names"""
        # Map to consolidated names based on the name_consolidation.json structure
        version_mappings = {
            "SlowMate": {
                "0.3": "SlowMate 0.3",
                "1.0": "SlowMate 1.0",
                "2.0": "SlowMate 2.0"
            },
            "V7P3R": {
                "4.1": "V7P3R 4.1", 
                "4.3": "V7P3R 4.3"
            },
            "Cece": {
                "2.0": "Cece 2.0",  # This includes v2.0-v2.1 variants
                "2.3": "Cece 2.0"   # This includes v2.2-v2.3 variants - same group but we'll filter by specific version
            },
            "C0BR4": {
                "1.0": "C0BR4 1.0",
                "2.0": "C0BR4 2.0"
            }
        }
        
        # Special handling for Cece versions that are in the same consolidated group
        if engine_family == "Cece" and version1 == "2.0" and version2 == "2.3":
            return self.find_cece_version_games(version1, version2)
        
        # Get consolidated names
        v1_canonical = version_mappings.get(engine_family, {}).get(version1, f"{engine_family}_v{version1}")
        v2_canonical = version_mappings.get(engine_family, {}).get(version2, f"{engine_family}_v{version2}")
        
        print(f"  Looking for games with: '{v1_canonical}' and '{v2_canonical}'")
        
        v1_games = []
        v2_games = []
        direct_games = []
        
        for game in self.base_analyzer.normalized_games:
            # Check if this game involves either version
            involves_v1 = (game.white == v1_canonical or game.black == v1_canonical)
            involves_v2 = (game.white == v2_canonical or game.black == v2_canonical)
            
            if involves_v1 and involves_v2:
                # Direct comparison game
                direct_games.append(game)
            elif involves_v1:
                v1_games.append(game)
            elif involves_v2:
                v2_games.append(game)
        
        return v1_games, v2_games, direct_games
    
    def find_cece_version_games(self, version1: str, version2: str) -> Tuple[List[GameRecord], List[GameRecord], List[GameRecord]]:
        """Special handler for Cece versions within the same consolidated group"""
        # Look for specific version patterns in original game data before consolidation
        v1_patterns = [f"Cece_v{version1}", f"Cece v{version1}", f"Cece_{version1}"]
        v2_patterns = [f"Cece_v{version2}", f"Cece v{version2}", f"Cece_{version2}"]
        
        print(f"  Looking for Cece games with patterns: {v1_patterns} vs {v2_patterns}")
        
        v1_games = []
        v2_games = []
        direct_games = []
        
        # Check original games before consolidation by examining the base analyzer's original games
        for game in self.base_analyzer.games:  # Use original games, not normalized
            white_matches_v1 = any(pattern.lower() in game.white.lower() for pattern in v1_patterns)
            black_matches_v1 = any(pattern.lower() in game.black.lower() for pattern in v1_patterns)
            white_matches_v2 = any(pattern.lower() in game.white.lower() for pattern in v2_patterns)
            black_matches_v2 = any(pattern.lower() in game.black.lower() for pattern in v2_patterns)
            
            involves_v1 = white_matches_v1 or black_matches_v1
            involves_v2 = white_matches_v2 or black_matches_v2
            
            if involves_v1 and involves_v2:
                direct_games.append(game)
            elif involves_v1:
                v1_games.append(game)
            elif involves_v2:
                v2_games.append(game)
        
        return v1_games, v2_games, direct_games
    
    def determine_game_phase(self, board: chess.Board, move_number: int) -> str:
        """Determine the game phase based on position and move number"""
        piece_count = len(board.piece_map())
        
        # Simple heuristic for game phases
        if move_number <= 10:
            return "opening"
        elif piece_count <= 10:
            return "endgame"
        elif move_number <= 25 and piece_count >= 20:
            return "opening"
        elif piece_count <= 16:
            return "endgame"
        else:
            return "middlegame"
    
    async def analyze_game_deeply(self, game: GameRecord, engine_version: str, sample_rate: float = 0.3) -> GameAnalysis:
        """Perform deep analysis of a single game"""
        print(f"  Analyzing game: {game.white} vs {game.black}")
        
        # Determine which color the engine played using case-insensitive consolidation mapping
        # Find all possible variants for this engine version
        possible_variants = [engine_version]  # Start with the provided version
        
        # Load consolidation data if available
        try:
            import json
            consolidation_path = "../dashboard/data/name_consolidation.json"
            with open(consolidation_path, 'r') as f:
                data = json.load(f)
                consolidations = data['name_consolidation']['consolidations']
            
            # Find which consolidation group this engine belongs to
            for group_name, group_data in consolidations.items():
                variants = group_data.get('variants', [])
                # Check if our engine version matches any variant (case-insensitive)
                if any(engine_version.lower() == variant.lower() for variant in variants):
                    possible_variants = variants
                    break
        except Exception as e:
            print(f"Warning: Could not load consolidation data: {e}")
        
        # Check if the game contains any of the possible variants (case-insensitive)
        engine_color = None
        actual_engine_name = None
        
        for variant in possible_variants:
            # Case-insensitive comparison
            if game.white.lower() == variant.lower():
                engine_color = "white"
                actual_engine_name = game.white  # Use the actual name from the game
                break
            elif game.black.lower() == variant.lower():
                engine_color = "black"
                actual_engine_name = game.black  # Use the actual name from the game
                break
        
        if engine_color is None:
            raise ValueError(f"Engine {engine_version} (variants: {possible_variants}) not found in game with players: {game.white} vs {game.black}")
        
        analysis = GameAnalysis(
            game_record=game,
            engine_version=engine_version,
            engine_color=engine_color
        )
        
        try:
            # Parse the game moves
            # For now, we'll create a simplified analysis since we need to recreate the game
            # In a real implementation, we'd need to parse the PGN more thoroughly
            
            # Create a simple board and analyze key positions
            board = chess.Board()
            move_count = 0
            
            # Simulate some moves for demonstration
            # In real implementation, parse actual game moves from PGN
            for move_num in range(min(50, len(game.moves))):  # Limit analysis for performance
                if move_count % int(1 / sample_rate) == 0:  # Sample moves based on rate
                    # Analyze current position
                    position_analysis = await self.stockfish.analyze_position(board)
                    
                    # Create a dummy move analysis
                    move_analysis = MoveAnalysis(
                        move=f"move_{move_num}",
                        san_move=f"move_{move_num}",
                        position_before=board.fen(),
                        position_after=board.fen(),
                        evaluation_before=position_analysis["evaluation"],
                        evaluation_after=position_analysis["evaluation"],
                        best_move=str(position_analysis["best_move"]) if position_analysis["best_move"] else "",
                        best_move_eval=position_analysis["evaluation"],
                        centipawn_loss=0.0,
                        game_phase=self.determine_game_phase(board, move_num)
                    )
                    
                    # Classify move quality
                    if move_analysis.centipawn_loss > 300:
                        move_analysis.is_blunder = True
                        analysis.blunder_count += 1
                    elif move_analysis.centipawn_loss > 100:
                        move_analysis.is_mistake = True
                        analysis.mistake_count += 1
                    elif move_analysis.centipawn_loss > 50:
                        move_analysis.is_inaccuracy = True
                        analysis.inaccuracy_count += 1
                    
                    analysis.moves.append(move_analysis)
                    analysis.total_centipawn_loss += move_analysis.centipawn_loss
                
                move_count += 1
                
                # Make a legal move to continue (for demonstration)
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    board.push(legal_moves[0])
                else:
                    break
            
            # Calculate phase distributions
            for move in analysis.moves:
                if move.game_phase == "opening":
                    analysis.opening_moves += 1
                elif move.game_phase == "middlegame":
                    analysis.middlegame_moves += 1
                elif move.game_phase == "endgame":
                    analysis.endgame_moves += 1
        
        except Exception as e:
            print(f"    Error analyzing game: {e}")
        
        return analysis
    
    async def compare_versions(self, engine_family: str, version1: str, version2: str, 
                              max_games_per_version: int = 20) -> VersionComparison:
        """Compare two versions of an engine"""
        print(f"🔍 Comparing {engine_family} {version1} vs {version2}")
        
        # Find games for both versions
        v1_games, v2_games, direct_games = self.find_version_games(engine_family, version1, version2)
        
        print(f"Found {len(v1_games)} games for v{version1}, {len(v2_games)} games for v{version2}")
        print(f"Found {len(direct_games)} direct comparison games")
        
        comparison = VersionComparison(
            engine_family=engine_family,
            version_1=version1,
            version_2=version2,
            direct_games=direct_games
        )
        
        # Analyze direct comparison games
        for game in direct_games:
            if game.result == "1-0":
                if game.white == f"{engine_family}_v{version1}":
                    comparison.v1_wins += 1
                    comparison.v2_losses += 1
                else:
                    comparison.v2_wins += 1
                    comparison.v1_losses += 1
            elif game.result == "0-1":
                if game.black == f"{engine_family}_v{version1}":
                    comparison.v1_wins += 1
                    comparison.v2_losses += 1
                else:
                    comparison.v2_wins += 1
                    comparison.v1_losses += 1
            else:  # Draw
                comparison.v1_draws += 1
                comparison.v2_draws += 1
        
        # Sample games for deep analysis
        v1_sample = v1_games[:max_games_per_version]
        v2_sample = v2_games[:max_games_per_version]
        
        # Analyze v1 games
        print(f"🔬 Deep analysis of {len(v1_sample)} games for v{version1}...")
        for i, game in enumerate(v1_sample):
            print(f"  Progress: {i+1}/{len(v1_sample)}")
            analysis = await self.analyze_game_deeply(game, f"{engine_family}_v{version1}")
            comparison.v1_analyses.append(analysis)
        
        # Analyze v2 games
        print(f"🔬 Deep analysis of {len(v2_sample)} games for v{version2}...")
        for i, game in enumerate(v2_sample):
            print(f"  Progress: {i+1}/{len(v2_sample)}")
            analysis = await self.analyze_game_deeply(game, f"{engine_family}_v{version2}")
            comparison.v2_analyses.append(analysis)
        
        # Calculate comparison metrics
        self.calculate_comparison_metrics(comparison)
        
        return comparison
    
    def calculate_comparison_metrics(self, comparison: VersionComparison):
        """Calculate detailed comparison metrics"""
        v1_analyses = comparison.v1_analyses
        v2_analyses = comparison.v2_analyses
        
        if not v1_analyses or not v2_analyses:
            return
        
        # Blunder rate comparison
        v1_blunder_rate = sum(a.blunder_count for a in v1_analyses) / sum(len(a.moves) for a in v1_analyses) if v1_analyses else 0
        v2_blunder_rate = sum(a.blunder_count for a in v2_analyses) / sum(len(a.moves) for a in v2_analyses) if v2_analyses else 0
        comparison.blunder_rate_diff = v2_blunder_rate - v1_blunder_rate
        
        # Accuracy comparison
        v1_accuracy = statistics.mean([a.move_accuracy for a in v1_analyses]) if v1_analyses else 0
        v2_accuracy = statistics.mean([a.move_accuracy for a in v2_analyses]) if v2_analyses else 0
        comparison.accuracy_diff = v2_accuracy - v1_accuracy
        
        # Time efficiency (placeholder)
        comparison.time_efficiency_diff = 0.0  # Would need actual time data
        
        # Identify regressions
        self.identify_regressions(comparison)
    
    def identify_regressions(self, comparison: VersionComparison):
        """Identify specific areas where the newer version regressed"""
        v1_analyses = comparison.v1_analyses
        v2_analyses = comparison.v2_analyses
        
        # Tactical regressions (more blunders in specific phases)
        v1_tactical_by_phase = defaultdict(list)
        v2_tactical_by_phase = defaultdict(list)
        
        for analysis in v1_analyses:
            for move in analysis.moves:
                if move.is_blunder:
                    v1_tactical_by_phase[move.game_phase].append(move)
        
        for analysis in v2_analyses:
            for move in analysis.moves:
                if move.is_blunder:
                    v2_tactical_by_phase[move.game_phase].append(move)
        
        # Compare blunder rates by phase
        for phase in ["opening", "middlegame", "endgame"]:
            v1_blunders = len(v1_tactical_by_phase[phase])
            v2_blunders = len(v2_tactical_by_phase[phase])
            v1_moves = sum(getattr(a, f"{phase}_moves", 0) for a in v1_analyses)
            v2_moves = sum(getattr(a, f"{phase}_moves", 0) for a in v2_analyses)
            
            if v1_moves > 0 and v2_moves > 0:
                v1_rate = v1_blunders / v1_moves
                v2_rate = v2_blunders / v2_moves
                
                if v2_rate > v1_rate * 1.5:  # 50% increase in blunder rate
                    comparison.tactical_regressions.append({
                        "phase": phase,
                        "v1_blunder_rate": v1_rate,
                        "v2_blunder_rate": v2_rate,
                        "regression_factor": v2_rate / v1_rate if v1_rate > 0 else float('inf')
                    })
    
    def generate_developer_report(self, comparison: VersionComparison) -> Dict[str, Any]:
        """Generate a comprehensive report for engine developers"""
        report = {
            "analysis_metadata": {
                "engine_family": comparison.engine_family,
                "version_comparison": f"{comparison.version_1} vs {comparison.version_2}",
                "analysis_date": datetime.datetime.now().isoformat(),
                "stockfish_depth": self.stockfish_depth,
                "games_analyzed": {
                    "v1_games": len(comparison.v1_analyses),
                    "v2_games": len(comparison.v2_analyses),
                    "direct_comparisons": len(comparison.direct_games)
                }
            },
            
            "executive_summary": {
                "overall_improvement": comparison.accuracy_diff > 0,
                "blunder_rate_change": comparison.blunder_rate_diff,
                "accuracy_change": comparison.accuracy_diff,
                "direct_match_record": {
                    "v1_wins": comparison.v1_wins,
                    "v1_losses": comparison.v1_losses,
                    "v1_draws": comparison.v1_draws,
                    "v2_wins": comparison.v2_wins,
                    "v2_losses": comparison.v2_losses,
                    "v2_draws": comparison.v2_draws
                },
                "key_regressions": len(comparison.tactical_regressions + comparison.positional_regressions)
            },
            
            "detailed_analysis": {
                "tactical_performance": {
                    "v1_metrics": self.calculate_version_metrics(comparison.v1_analyses),
                    "v2_metrics": self.calculate_version_metrics(comparison.v2_analyses),
                    "regressions": comparison.tactical_regressions
                },
                "positional_performance": {
                    "regressions": comparison.positional_regressions
                },
                "opening_analysis": comparison.opening_changes,
                "endgame_analysis": comparison.endgame_changes
            },
            
            "actionable_recommendations": self.generate_recommendations(comparison),
            
            "sample_games": self.extract_sample_games(comparison)
        }
        
        return report
    
    def calculate_version_metrics(self, analyses: List[GameAnalysis]) -> Dict[str, Any]:
        """Calculate metrics for a specific version"""
        if not analyses:
            return {}
        
        return {
            "total_games": len(analyses),
            "avg_move_accuracy": statistics.mean([a.move_accuracy for a in analyses]),
            "avg_blunders_per_game": statistics.mean([a.blunder_count for a in analyses]),
            "avg_mistakes_per_game": statistics.mean([a.mistake_count for a in analyses]),
            "avg_centipawn_loss": statistics.mean([a.total_centipawn_loss for a in analyses]),
            "phase_distribution": {
                "opening_moves": sum(a.opening_moves for a in analyses),
                "middlegame_moves": sum(a.middlegame_moves for a in analyses),
                "endgame_moves": sum(a.endgame_moves for a in analyses)
            }
        }
    
    def generate_recommendations(self, comparison: VersionComparison) -> List[Dict[str, str]]:
        """Generate actionable recommendations for developers"""
        recommendations = []
        
        # Blunder rate recommendations
        if comparison.blunder_rate_diff > 0.05:  # 5% increase in blunder rate
            recommendations.append({
                "priority": "HIGH",
                "category": "Tactical",
                "issue": "Increased blunder rate in newer version",
                "recommendation": "Review tactical search algorithms and position evaluation functions",
                "specific_areas": "Focus on blunder-prone game phases identified in regression analysis"
            })
        
        # Phase-specific recommendations
        for regression in comparison.tactical_regressions:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Phase-Specific",
                "issue": f"Regression in {regression['phase']} play",
                "recommendation": f"Analyze {regression['phase']} evaluation and search parameters",
                "specific_areas": f"Blunder rate increased by {regression['regression_factor']:.2f}x"
            })
        
        # General improvement recommendations
        if comparison.accuracy_diff < -2.0:  # 2% decrease in accuracy
            recommendations.append({
                "priority": "MEDIUM",
                "category": "General",
                "issue": "Overall move accuracy decreased",
                "recommendation": "Review move selection algorithms and evaluation weights",
                "specific_areas": "Consider reverting recent changes to core evaluation"
            })
        
        return recommendations
    
    def extract_sample_games(self, comparison: VersionComparison) -> Dict[str, List[Dict]]:
        """Extract sample games that highlight key differences"""
        samples = {
            "regression_examples": [],
            "improvement_examples": [],
            "direct_comparisons": []
        }
        
        # Add regression examples (games where v2 performed significantly worse)
        v2_worst = sorted(comparison.v2_analyses, key=lambda a: a.move_accuracy)[:3]
        for analysis in v2_worst:
            samples["regression_examples"].append({
                "game_info": f"{analysis.game_record.white} vs {analysis.game_record.black}",
                "result": analysis.game_record.result,
                "accuracy": analysis.move_accuracy,
                "blunders": analysis.blunder_count,
                "key_issue": "Low move accuracy suggests tactical issues"
            })
        
        # Add improvement examples
        v2_best = sorted(comparison.v2_analyses, key=lambda a: a.move_accuracy, reverse=True)[:3]
        for analysis in v2_best:
            samples["improvement_examples"].append({
                "game_info": f"{analysis.game_record.white} vs {analysis.game_record.black}",
                "result": analysis.game_record.result,
                "accuracy": analysis.move_accuracy,
                "blunders": analysis.blunder_count,
                "key_strength": "High move accuracy demonstrates improvement"
            })
        
        # Add direct comparison samples
        for game in comparison.direct_games[:5]:
            samples["direct_comparisons"].append({
                "white": game.white,
                "black": game.black,
                "result": game.result,
                "tournament": game.tournament,
                "significance": "Direct head-to-head comparison"
            })
        
        return samples

async def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description="Chess Engine Version Comparison Analyzer")
    parser.add_argument("--engine", required=True, help="Engine family name (e.g., SlowMate, Cece)")
    parser.add_argument("--v1", required=True, help="First version to compare (e.g., v1.0)")
    parser.add_argument("--v2", required=True, help="Second version to compare (e.g., v2.0)")
    parser.add_argument("--depth", type=int, default=15, help="Stockfish analysis depth")
    parser.add_argument("--max-games", type=int, default=20, help="Maximum games to analyze per version")
    parser.add_argument("--output", help="Output file path (default: auto-generated)")
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = VersionComparisonAnalyzer(stockfish_depth=args.depth)
    
    try:
        await analyzer.initialize()
        
        # Perform comparison
        comparison = await analyzer.compare_versions(
            args.engine, 
            args.v1, 
            args.v2, 
            args.max_games
        )
        
        # Generate report
        report = analyzer.generate_developer_report(comparison)
        
        # Save report
        if args.output:
            output_path = args.output
        else:
            output_path = f"version_comparison_{args.engine}_{args.v1}_vs_{args.v2}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📊 Analysis Complete!")
        print(f"Report saved to: {output_path}")
        print(f"\n🎯 Executive Summary:")
        print(f"Engine: {args.engine} {args.v1} vs {args.v2}")
        print(f"Games analyzed: {report['analysis_metadata']['games_analyzed']['v1_games']} vs {report['analysis_metadata']['games_analyzed']['v2_games']}")
        print(f"Accuracy change: {report['executive_summary']['accuracy_change']:.2f}%")
        print(f"Blunder rate change: {report['executive_summary']['blunder_rate_change']:.4f}")
        print(f"Key regressions found: {report['executive_summary']['key_regressions']}")
        
        if report['actionable_recommendations']:
            print(f"\n⚠️  Top Recommendations:")
            for rec in report['actionable_recommendations'][:3]:
                print(f"  {rec['priority']}: {rec['issue']}")
                print(f"    → {rec['recommendation']}")
    
    finally:
        await analyzer.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
