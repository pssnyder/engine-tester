#!/usr/bin/env python3
"""
ELO Rating System for Chess Engines
Provides reliable ELO estimation using various methods including integration with external tools
"""

import os
import json
import asyncio
import subprocess
import tempfile
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import chess
import chess.engine
import chess.pgn

@dataclass
class EloGame:
    """Single game result for ELO calculation"""
    white_engine: str
    black_engine: str
    result: float  # 1.0 = white wins, 0.5 = draw, 0.0 = black wins
    moves: int
    time_control: str
    date: str
    pgn_text: Optional[str] = None

@dataclass
class EloRating:
    """ELO rating information for an engine"""
    engine_name: str
    elo: float
    games_played: int
    wins: int
    losses: int
    draws: int
    confidence_interval: Tuple[float, float]
    rating_method: str  # "bayeselo", "elostat", "internal", "ordo"
    last_updated: str

class EloRatingSystem:
    """Comprehensive ELO rating system with multiple calculation methods"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.ratings_dir = self.base_dir / "elo_testing"
        self.ratings_dir.mkdir(parents=True, exist_ok=True)
        
        # Known reference engines with their approximate ELO ratings
        self.reference_engines = {
            "Stockfish": 3500,
            "Stockfish 1%": 2650,
            "Random Playing Opponent": 100,
            "Random_Opponent": 100
        }
        
        self.games: List[EloGame] = []
        self.ratings: Dict[str, EloRating] = {}
        
    def add_game(self, white_engine: str, black_engine: str, result: float, 
                 moves: int = 0, time_control: str = "unknown", pgn_text: Optional[str] = None):
        """Add a game result to the rating system"""
        game = EloGame(
            white_engine=white_engine,
            black_engine=black_engine,
            result=result,
            moves=moves,
            time_control=time_control,
            date=datetime.now().isoformat(),
            pgn_text=pgn_text
        )
        self.games.append(game)
        
    def load_games_from_pgn_files(self, pgn_directory: str):
        """Load games from PGN files in a directory"""
        print(f"Loading games from {pgn_directory}")
        pgn_path = Path(pgn_directory)
        
        if not pgn_path.exists():
            print(f"Warning: PGN directory not found: {pgn_directory}")
            return
            
        game_count = 0
        for pgn_file in pgn_path.glob("**/*.pgn"):
            print(f"Processing {pgn_file.name}")
            
            try:
                # Try multiple encodings to handle character issues
                game_content = None
                for encoding in ['utf-8', 'latin-1', 'cp1252', 'utf-8-sig']:
                    try:
                        with open(pgn_file, 'r', encoding=encoding, errors='ignore') as f:
                            game_content = f
                            while True:
                                game = chess.pgn.read_game(f)
                                if game is None:
                                    break
                                    
                                white = game.headers.get("White", "Unknown")
                                black = game.headers.get("Black", "Unknown")
                                result_str = game.headers.get("Result", "*")
                                
                                # Convert result to numeric
                                if result_str == "1-0":
                                    result = 1.0
                                elif result_str == "0-1":
                                    result = 0.0
                                elif result_str == "1/2-1/2":
                                    result = 0.5
                                else:
                                    continue  # Skip unfinished games
                                    
                                # Count moves
                                moves = sum(1 for _ in game.mainline())
                                
                                # Get time control
                                time_control = game.headers.get("TimeControl", "unknown")
                                
                                self.add_game(white, black, result, moves, time_control, str(game))
                                game_count += 1
                        break  # Successfully read with this encoding
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        print(f"    Error reading games from {pgn_file}: {e}")
                        break
                        
            except Exception as e:
                print(f"Error processing {pgn_file}: {e}")
                
        print(f"Loaded {game_count} games total")
        
    def export_pgn_for_external_tools(self, output_file: str) -> str:
        """Export games in PGN format for external ELO calculation tools"""
        output_path = self.ratings_dir / output_file
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, game in enumerate(self.games):
                # Write PGN headers
                f.write(f'[Event "Rating Games"]\n')
                f.write(f'[Site "Engine Testing"]\n')
                f.write(f'[Date "{game.date[:10].replace("-", ".")}"]\n')
                f.write(f'[Round "{i+1}"]\n')
                f.write(f'[White "{game.white_engine}"]\n')
                f.write(f'[Black "{game.black_engine}"]\n')
                
                if game.result == 1.0:
                    f.write('[Result "1-0"]\n')
                elif game.result == 0.0:
                    f.write('[Result "0-1"]\n')
                else:
                    f.write('[Result "1/2-1/2"]\n')
                    
                f.write(f'[TimeControl "{game.time_control}"]\n')
                f.write('\n')
                
                # Write moves (if available) or placeholder
                if game.pgn_text:
                    # Extract just the moves from the PGN text
                    lines = game.pgn_text.split('\n')
                    move_lines = [line for line in lines if not line.startswith('[') and line.strip()]
                    if move_lines:
                        f.write(' '.join(move_lines))
                    else:
                        f.write('1. e4 e5 *')  # Placeholder
                else:
                    f.write('1. e4 e5 *')  # Placeholder
                    
                f.write('\n\n')
                
        print(f"Exported {len(self.games)} games to {output_path}")
        return str(output_path)
        
    def calculate_elo_internal(self, k_factor: float = 32) -> Dict[str, EloRating]:
        """Internal ELO calculation using simple ELO algorithm"""
        print("Calculating ELO ratings using internal algorithm...")
        
        # Initialize ratings - start everyone at 1500, but use reference engines
        engine_ratings = {}
        engine_games = {}
        engine_stats = {}
        
        # Collect all unique engines
        all_engines = set()
        for game in self.games:
            all_engines.add(game.white_engine)
            all_engines.add(game.black_engine)
            
        # Initialize ratings
        for engine in all_engines:
            if engine in self.reference_engines:
                engine_ratings[engine] = float(self.reference_engines[engine])
            else:
                engine_ratings[engine] = 1500.0
            engine_games[engine] = 0
            engine_stats[engine] = {"wins": 0, "losses": 0, "draws": 0}
            
        # Process games in chronological order
        for game in self.games:
            white = game.white_engine
            black = game.black_engine
            
            # Skip games with unknown engines
            if white not in engine_ratings or black not in engine_ratings:
                continue
                
            # Get current ratings
            white_rating = engine_ratings[white]
            black_rating = engine_ratings[black]
            
            # Calculate expected scores
            white_expected = 1 / (1 + 10**((black_rating - white_rating) / 400))
            black_expected = 1 - white_expected
            
            # Calculate actual scores
            white_score = game.result
            black_score = 1 - game.result
            
            # Update ratings (but don't update reference engines)
            if white not in self.reference_engines:
                white_new_rating = white_rating + k_factor * (white_score - white_expected)
                engine_ratings[white] = white_new_rating
                
            if black not in self.reference_engines:
                black_new_rating = black_rating + k_factor * (black_score - black_expected)
                engine_ratings[black] = black_new_rating
                
            # Update game counts and statistics
            engine_games[white] += 1
            engine_games[black] += 1
            
            if game.result == 1.0:  # White wins
                engine_stats[white]["wins"] += 1
                engine_stats[black]["losses"] += 1
            elif game.result == 0.0:  # Black wins
                engine_stats[white]["losses"] += 1
                engine_stats[black]["wins"] += 1
            else:  # Draw
                engine_stats[white]["draws"] += 1
                engine_stats[black]["draws"] += 1
                
        # Create EloRating objects
        ratings = {}
        for engine, rating in engine_ratings.items():
            if engine_games[engine] > 0:  # Only include engines that played games
                # Simple confidence interval based on number of games
                margin = max(50, 200 / (engine_games[engine] ** 0.5))
                
                ratings[engine] = EloRating(
                    engine_name=engine,
                    elo=rating,
                    games_played=engine_games[engine],
                    wins=engine_stats[engine]["wins"],
                    losses=engine_stats[engine]["losses"], 
                    draws=engine_stats[engine]["draws"],
                    confidence_interval=(rating - margin, rating + margin),
                    rating_method="internal",
                    last_updated=datetime.now().isoformat()
                )
                
        self.ratings = ratings
        return ratings
        
    def run_bayeselo(self, pgn_file: str, bayeselo_path: Optional[str] = None) -> Dict[str, EloRating]:
        """Run BayesElo external tool for ELO calculation"""
        print("Running BayesElo calculation...")
        
        if bayeselo_path and os.path.exists(bayeselo_path):
            print(f"Using BayesElo at: {bayeselo_path}")
            # TODO: Implement BayesElo integration
            # For now, fall back to internal calculation
            return self.calculate_elo_internal()
        else:
            print("BayesElo not found, using internal calculation")
            return self.calculate_elo_internal()
            
    def run_elostat(self, pgn_file: str, elostat_path: Optional[str] = None) -> Dict[str, EloRating]:
        """Run Elostat external tool for ELO calculation"""
        print("Running Elostat calculation...")
        
        if elostat_path and os.path.exists(elostat_path):
            print(f"Using Elostat at: {elostat_path}")
            # TODO: Implement Elostat integration
            # For now, fall back to internal calculation
            return self.calculate_elo_internal()
        else:
            print("Elostat not found, using internal calculation")
            return self.calculate_elo_internal()
            
    def generate_rating_report(self, output_file: str = "elo_ratings_report.json"):
        """Generate a comprehensive rating report"""
        if not self.ratings:
            print("No ratings calculated yet. Run calculate_elo_* first.")
            return
            
        output_path = self.ratings_dir / output_file
        
        # Sort engines by rating (descending)
        sorted_engines = sorted(self.ratings.items(), key=lambda x: x[1].elo, reverse=True)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_games": len(self.games),
            "total_engines": len(self.ratings),
            "rating_method": sorted_engines[0][1].rating_method if sorted_engines else "unknown",
            "engines": [
                {
                    "rank": i + 1,
                    "engine_name": rating.engine_name,
                    "elo": round(rating.elo, 1),
                    "confidence_interval": [round(rating.confidence_interval[0], 1), 
                                          round(rating.confidence_interval[1], 1)],
                    "games_played": rating.games_played,
                    "wins": rating.wins,
                    "losses": rating.losses,
                    "draws": rating.draws,
                    "win_rate": round(rating.wins / max(rating.games_played, 1) * 100, 1),
                    "score_percentage": round((rating.wins + rating.draws * 0.5) / max(rating.games_played, 1) * 100, 1)
                }
                for i, (engine_name, rating) in enumerate(sorted_engines)
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"Rating report saved to {output_path}")
        
        # Print summary to console
        print("\n" + "="*60)
        print("ELO RATINGS SUMMARY")
        print("="*60)
        print(f"{'Rank':<4} {'Engine':<25} {'ELO':<6} {'±':<4} {'Games':<6} {'Score':<6}")
        print("-"*60)
        
        for i, (engine_name, rating) in enumerate(sorted_engines[:15]):  # Top 15
            margin = (rating.confidence_interval[1] - rating.confidence_interval[0]) / 2
            score_pct = (rating.wins + rating.draws * 0.5) / max(rating.games_played, 1) * 100
            
            print(f"{i+1:<4} {engine_name[:24]:<25} {rating.elo:<6.0f} {margin:<4.0f} {rating.games_played:<6} {score_pct:<6.1f}%")
            
        return report
        
    def compare_engine_versions(self, engine_base_name: str) -> Dict[str, Any]:
        """Compare different versions of the same engine"""
        version_ratings = {}
        
        for engine_name, rating in self.ratings.items():
            if engine_base_name.lower() in engine_name.lower():
                version_ratings[engine_name] = rating
                
        if len(version_ratings) < 2:
            return {"error": f"Not enough versions found for {engine_base_name}"}
            
        # Sort by ELO
        sorted_versions = sorted(version_ratings.items(), key=lambda x: x[1].elo, reverse=True)
        
        return {
            "engine_family": engine_base_name,
            "versions_analyzed": len(sorted_versions),
            "strongest_version": {
                "name": sorted_versions[0][0],
                "elo": sorted_versions[0][1].elo,
                "games": sorted_versions[0][1].games_played
            },
            "weakest_version": {
                "name": sorted_versions[-1][0],
                "elo": sorted_versions[-1][1].elo,
                "games": sorted_versions[-1][1].games_played
            },
            "elo_range": sorted_versions[0][1].elo - sorted_versions[-1][1].elo,
            "all_versions": [
                {
                    "name": name,
                    "elo": rating.elo,
                    "games": rating.games_played,
                    "win_rate": rating.wins / max(rating.games_played, 1) * 100
                }
                for name, rating in sorted_versions
            ]
        }

def main():
    """Example usage of the ELO rating system"""
    elo_system = EloRatingSystem()
    
    # Load games from tournament results
    results_dir = "../results"
    elo_system.load_games_from_pgn_files(results_dir)
    
    if len(elo_system.games) > 0:
        print(f"Loaded {len(elo_system.games)} games")
        
        # Export PGN for external tools
        pgn_file = elo_system.export_pgn_for_external_tools("rating_games.pgn")
        
        # Calculate ratings using internal method
        ratings = elo_system.calculate_elo_internal()
        
        # Generate report
        report = elo_system.generate_rating_report()
        
        # Compare specific engine versions
        for engine_family in ["SlowMate", "Cece", "V7P3R", "C0BR4"]:
            comparison = elo_system.compare_engine_versions(engine_family)
            if "error" not in comparison:
                print(f"\n{engine_family} Version Comparison:")
                print(f"  Strongest: {comparison['strongest_version']['name']} ({comparison['strongest_version']['elo']:.0f} ELO)")
                print(f"  ELO Range: {comparison['elo_range']:.0f} points")
    else:
        print("No games found to analyze")

if __name__ == "__main__":
    main()
