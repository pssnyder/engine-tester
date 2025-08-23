#!/usr/bin/env python3
"""
Man vs Machine Analyzer

Specialized analyzer for V7P3R vs SlowMate competitive metrics.
Processes tournament results to extract head-to-head performance,
version tracking, and advanced chess metrics.
"""

import os
import sys
import json
import re
import chess
import chess.pgn
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
import pandas as pd

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent / "analytics_and_dashboard" / "analyzers"))

# Try to import optional analyzers - gracefully handle missing dependencies
name_mapper = None
pgn_analyzer = None

try:
    from name_mapper import EngineNameMapper
    name_mapper = EngineNameMapper
except ImportError:
    print("Note: name_mapper not available - using basic engine name detection")

try:
    from enhanced_pgn_analyzer import EnhancedPGNAnalyzer
    pgn_analyzer = EnhancedPGNAnalyzer
except ImportError:
    print("Note: enhanced_pgn_analyzer not available - basic analysis only")

class ManVsMachineAnalyzer:
    """Analyzer specifically for V7P3R vs SlowMate competition"""
    
    def __init__(self, results_dir: Optional[str] = None):
        self.results_dir = results_dir or str(Path(__file__).parent.parent.parent / "results")
        self.name_mapper = None
        self.pgn_analyzer = None
        
        # Initialize analyzers if available
        global name_mapper, pgn_analyzer
        try:
            if name_mapper:
                self.name_mapper = name_mapper()
        except Exception as e:
            print(f"Could not initialize name_mapper: {e}")
            
        try:
            if pgn_analyzer:
                self.pgn_analyzer = pgn_analyzer()
        except Exception as e:
            print(f"Could not initialize pgn_analyzer: {e}")
        
        # Target engines - Updated patterns for better matching
        self.v7p3r_patterns = [
            r'V7P3R.*', r'v7p3r.*', r'V7P3R_.*', r'v7p3r_.*',
            r'.*V7P3R.*', r'.*v7p3r.*'  # More flexible patterns
        ]
        self.slowmate_patterns = [
            r'SlowMate.*', r'slowmate.*', r'SlowMate_.*', r'slowmate_.*', r'Slowmate.*',
            r'.*SlowMate.*', r'.*slowmate.*', r'.*Slowmate.*'  # More flexible patterns
        ]
        
    def is_v7p3r_engine(self, name: str) -> bool:
        """Check if engine name is V7P3R variant"""
        return any(re.match(pattern, name) for pattern in self.v7p3r_patterns)
    
    def is_slowmate_engine(self, name: str) -> bool:
        """Check if engine name is SlowMate variant"""
        return any(re.match(pattern, name) for pattern in self.slowmate_patterns)
    
    def extract_version(self, engine_name: str) -> str:
        """Extract version information from engine name"""
        # Look for version patterns like v1.0, _v2, etc.
        version_patterns = [
            r'[vV](\d+(?:\.\d+)*)',
            r'_(\d+(?:\.\d+)*)',
            r'-(\d+(?:\.\d+)*)',
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, engine_name)
            if match:
                return match.group(1)
        
        return "unknown"
    
    def classify_game_result(self, game: chess.pgn.Game) -> Dict[str, Any]:
        """Classify game result with detailed analysis"""
        headers = game.headers
        
        # Basic result
        result = headers.get("Result", "*")
        termination = headers.get("Termination", "")
        
        # Players
        white = headers.get("White", "")
        black = headers.get("Black", "")
        
        # Classify result type
        result_type = "unknown"
        if "checkmate" in termination.lower():
            result_type = "checkmate"
        elif "stalemate" in termination.lower():
            result_type = "stalemate"
        elif "resignation" in termination.lower():
            result_type = "resignation"
        elif "time" in termination.lower():
            result_type = "time"
        elif "material" in termination.lower():
            result_type = "insufficient_material"
        elif "draw" in termination.lower():
            result_type = "draw_agreement"
        
        return {
            "result": result,
            "result_type": result_type,
            "termination": termination,
            "white": white,
            "black": black
        }
    
    def analyze_game_for_blunders(self, game: chess.pgn.Game) -> Dict[str, Any]:
        """Analyze game for missed wins and blunders"""
        if not self.pgn_analyzer:
            return {"error": "PGN analyzer not available"}
        
        try:
            # Use enhanced PGN analyzer for blunder detection
            analysis = self.pgn_analyzer.analyze_game_detailed(game)
            
            # Extract relevant metrics
            return {
                "total_moves": analysis.get("total_moves", 0),
                "blunders": analysis.get("blunders", []),
                "missed_wins": analysis.get("missed_wins", []),
                "evaluation_swings": analysis.get("evaluation_swings", []),
                "tactical_shots": analysis.get("tactical_shots", [])
            }
        except Exception as e:
            return {"error": f"Analysis failed: {e}"}
    
    def analyze_opening_repertoire(self, games: List[chess.pgn.Game], engine_name: str) -> Dict[str, Any]:
        """Analyze opening repertoire for an engine"""
        opening_stats = defaultdict(int)
        opening_results = defaultdict(lambda: {"wins": 0, "losses": 0, "draws": 0})
        
        for game in games:
            headers = game.headers
            opening = headers.get("Opening", "Unknown")
            eco = headers.get("ECO", "")
            
            if opening == "Unknown" and eco:
                opening = f"ECO {eco}"
            
            opening_stats[opening] += 1
            
            # Determine if this engine won
            white = headers.get("White", "")
            black = headers.get("Black", "")
            result = headers.get("Result", "*")
            
            engine_is_white = self.is_engine_match(white, engine_name)
            
            if result == "1-0":
                if engine_is_white:
                    opening_results[opening]["wins"] += 1
                else:
                    opening_results[opening]["losses"] += 1
            elif result == "0-1":
                if engine_is_white:
                    opening_results[opening]["losses"] += 1
                else:
                    opening_results[opening]["wins"] += 1
            elif result == "1/2-1/2":
                opening_results[opening]["draws"] += 1
        
        # Calculate success rates
        repertoire_analysis = {}
        for opening, count in opening_stats.items():
            stats = opening_results[opening]
            total = stats["wins"] + stats["losses"] + stats["draws"]
            if total > 0:
                repertoire_analysis[opening] = {
                    "games": count,
                    "wins": stats["wins"],
                    "losses": stats["losses"],
                    "draws": stats["draws"],
                    "success_rate": (stats["wins"] + 0.5 * stats["draws"]) / total
                }
        
        return repertoire_analysis
    
    def is_engine_match(self, name: str, target_engine: str) -> bool:
        """Check if name matches target engine"""
        if self.is_v7p3r_engine(target_engine):
            return self.is_v7p3r_engine(name)
        elif self.is_slowmate_engine(target_engine):
            return self.is_slowmate_engine(name)
        else:
            return name.lower() == target_engine.lower()
    
    def process_tournament_file(self, pgn_file: str) -> Dict[str, Any]:
        """Process a single tournament PGN file"""
        results = {
            "file": pgn_file,
            "games": [],
            "v7p3r_games": [],
            "slowmate_games": [],
            "head_to_head": [],
            "error": None
        }
        
        try:
            # Try different encodings to handle problematic files
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            file_opened = False
            
            for encoding in encodings:
                try:
                    with open(pgn_file, 'r', encoding=encoding) as f:
                        file_opened = True
                        break
                except UnicodeDecodeError:
                    continue
            
            if not file_opened:
                results["error"] = "Could not decode file with any supported encoding"
                return results
            
            with open(pgn_file, 'r', encoding=encoding) as f:
                while True:
                    try:
                        game = chess.pgn.read_game(f)
                        if game is None:
                            break
                    except (chess.IllegalMoveError, ValueError, UnicodeDecodeError) as e:
                        # Skip malformed games and continue
                        print(f"Skipping malformed game in {pgn_file}: {e}")
                        continue
                    
                    game_analysis = self.classify_game_result(game)
                    white = game_analysis["white"]
                    black = game_analysis["black"]
                    
                    # Check for V7P3R vs SlowMate matchups
                    v7p3r_is_white = self.is_v7p3r_engine(white)
                    v7p3r_is_black = self.is_v7p3r_engine(black)
                    slowmate_is_white = self.is_slowmate_engine(white)
                    slowmate_is_black = self.is_slowmate_engine(black)
                    
                    is_head_to_head = ((v7p3r_is_white and slowmate_is_black) or 
                                     (v7p3r_is_black and slowmate_is_white))
                    
                    # Add game analysis
                    game_data = {
                        **game_analysis,
                        "is_head_to_head": is_head_to_head,
                        "v7p3r_version": self.extract_version(white) if v7p3r_is_white else self.extract_version(black) if v7p3r_is_black else None,
                        "slowmate_version": self.extract_version(white) if slowmate_is_white else self.extract_version(black) if slowmate_is_black else None,
                    }
                    
                    # Add detailed analysis if available
                    if self.pgn_analyzer:
                        try:
                            detailed_analysis = self.analyze_game_for_blunders(game)
                            game_data["detailed_analysis"] = detailed_analysis
                        except:
                            # Skip detailed analysis if it fails
                            pass
                    
                    results["games"].append(game_data)
                    
                    # Categorize games
                    if v7p3r_is_white or v7p3r_is_black:
                        results["v7p3r_games"].append(game_data)
                    
                    if slowmate_is_white or slowmate_is_black:
                        results["slowmate_games"].append(game_data)
                    
                    if is_head_to_head:
                        results["head_to_head"].append(game_data)
        
        except Exception as e:
            results["error"] = str(e)
            print(f"Error processing {pgn_file}: {e}")
        
        return results
    
    def analyze_all_tournaments(self) -> Dict[str, Any]:
        """Analyze all tournament results for MvM metrics"""
        print("🔍 Analyzing Man vs Machine tournament results...")
        
        all_results = {
            "analysis_date": datetime.now().isoformat(),
            "tournaments": {},
            "v7p3r_summary": {},
            "slowmate_summary": {},
            "head_to_head_summary": {},
            "version_tracking": {
                "v7p3r_versions": {},
                "slowmate_versions": {}
            },
            "advanced_metrics": {}
        }
        
        # Find all PGN files
        pgn_files = []
        for root, dirs, files in os.walk(self.results_dir):
            for file in files:
                if file.endswith('.pgn'):
                    pgn_files.append(os.path.join(root, file))
        
        print(f"📁 Found {len(pgn_files)} PGN files to analyze")
        
        # Process each tournament
        total_h2h_games = 0
        total_v7p3r_games = 0
        total_slowmate_games = 0
        
        for pgn_file in pgn_files:
            print(f"📊 Processing {os.path.basename(pgn_file)}...")
            tournament_results = self.process_tournament_file(pgn_file)
            
            tournament_name = os.path.basename(pgn_file).replace('.pgn', '')
            all_results["tournaments"][tournament_name] = tournament_results
            
            total_h2h_games += len(tournament_results["head_to_head"])
            total_v7p3r_games += len(tournament_results["v7p3r_games"])
            total_slowmate_games += len(tournament_results["slowmate_games"])
        
        print(f"📈 Total Head-to-Head games found: {total_h2h_games}")
        print(f"🤖 Total V7P3R games: {total_v7p3r_games}")
        print(f"🧠 Total SlowMate games: {total_slowmate_games}")
        
        # Generate summaries
        all_results["v7p3r_summary"] = self._generate_engine_summary("V7P3R", all_results["tournaments"])
        all_results["slowmate_summary"] = self._generate_engine_summary("SlowMate", all_results["tournaments"])
        all_results["head_to_head_summary"] = self._generate_head_to_head_summary(all_results["tournaments"])
        all_results["version_tracking"] = self._generate_version_tracking(all_results["tournaments"])
        all_results["advanced_metrics"] = self._generate_advanced_metrics(all_results["tournaments"])
        
        return all_results
    
    def _generate_engine_summary(self, engine_type: str, tournaments: Dict) -> Dict[str, Any]:
        """Generate summary statistics for an engine"""
        is_v7p3r = engine_type == "V7P3R"
        
        total_games = 0
        wins = 0
        losses = 0
        draws = 0
        decisive_wins = 0  # Checkmate wins
        missed_wins = 0
        total_moves = 0
        
        for tournament_name, tournament_data in tournaments.items():
            games = tournament_data["v7p3r_games"] if is_v7p3r else tournament_data["slowmate_games"]
            
            for game in games:
                total_games += 1
                
                # Determine if engine won
                white = game["white"]
                black = game["black"]
                result = game["result"]
                
                engine_is_white = (self.is_v7p3r_engine(white) if is_v7p3r else self.is_slowmate_engine(white))
                
                if result == "1-0":
                    if engine_is_white:
                        wins += 1
                        if game["result_type"] == "checkmate":
                            decisive_wins += 1
                    else:
                        losses += 1
                elif result == "0-1":
                    if engine_is_white:
                        losses += 1
                    else:
                        wins += 1
                        if game["result_type"] == "checkmate":
                            decisive_wins += 1
                elif result == "1/2-1/2":
                    draws += 1
                
                # Add detailed analysis if available
                if "detailed_analysis" in game and "total_moves" in game["detailed_analysis"]:
                    total_moves += game["detailed_analysis"]["total_moves"]
                    missed_wins += len(game["detailed_analysis"].get("missed_wins", []))
        
        return {
            "total_games": total_games,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "win_rate": wins / total_games if total_games > 0 else 0,
            "score_percentage": (wins + 0.5 * draws) / total_games * 100 if total_games > 0 else 0,
            "decisive_wins": decisive_wins,
            "decisive_win_rate": decisive_wins / wins if wins > 0 else 0,
            "missed_wins": missed_wins,
            "missed_win_rate": missed_wins / total_games if total_games > 0 else 0,
            "average_moves": total_moves / total_games if total_games > 0 else 0
        }
    
    def _generate_head_to_head_summary(self, tournaments: Dict) -> Dict[str, Any]:
        """Generate head-to-head summary between V7P3R and SlowMate"""
        h2h_games = []
        
        for tournament_name, tournament_data in tournaments.items():
            h2h_games.extend(tournament_data["head_to_head"])
        
        if not h2h_games:
            return {"error": "No head-to-head games found"}
        
        v7p3r_wins = 0
        slowmate_wins = 0
        draws = 0
        v7p3r_decisive = 0
        slowmate_decisive = 0
        
        for game in h2h_games:
            white = game["white"]
            result = game["result"]
            
            v7p3r_is_white = self.is_v7p3r_engine(white)
            
            if result == "1-0":
                if v7p3r_is_white:
                    v7p3r_wins += 1
                    if game["result_type"] == "checkmate":
                        v7p3r_decisive += 1
                else:
                    slowmate_wins += 1
                    if game["result_type"] == "checkmate":
                        slowmate_decisive += 1
            elif result == "0-1":
                if v7p3r_is_white:
                    slowmate_wins += 1
                    if game["result_type"] == "checkmate":
                        slowmate_decisive += 1
                else:
                    v7p3r_wins += 1
                    if game["result_type"] == "checkmate":
                        v7p3r_decisive += 1
            elif result == "1/2-1/2":
                draws += 1
        
        total = len(h2h_games)
        
        return {
            "total_games": total,
            "v7p3r_wins": v7p3r_wins,
            "slowmate_wins": slowmate_wins,
            "draws": draws,
            "v7p3r_score_percentage": (v7p3r_wins + 0.5 * draws) / total * 100 if total > 0 else 0,
            "slowmate_score_percentage": (slowmate_wins + 0.5 * draws) / total * 100 if total > 0 else 0,
            "v7p3r_decisive": v7p3r_decisive,
            "slowmate_decisive": slowmate_decisive,
            "draw_rate": draws / total * 100 if total > 0 else 0
        }
    
    def _generate_version_tracking(self, tournaments: Dict) -> Dict[str, Any]:
        """Track performance by engine version"""
        v7p3r_versions = defaultdict(lambda: {"games": 0, "wins": 0, "losses": 0, "draws": 0})
        slowmate_versions = defaultdict(lambda: {"games": 0, "wins": 0, "losses": 0, "draws": 0})
        
        for tournament_name, tournament_data in tournaments.items():
            all_games = tournament_data["games"]
            
            for game in all_games:
                white = game["white"]
                black = game["black"]
                result = game["result"]
                
                # Process V7P3R versions
                if self.is_v7p3r_engine(white):
                    version = game.get("v7p3r_version", "unknown")
                    v7p3r_versions[version]["games"] += 1
                    
                    if result == "1-0":
                        v7p3r_versions[version]["wins"] += 1
                    elif result == "0-1":
                        v7p3r_versions[version]["losses"] += 1
                    elif result == "1/2-1/2":
                        v7p3r_versions[version]["draws"] += 1
                
                elif self.is_v7p3r_engine(black):
                    version = game.get("v7p3r_version", "unknown")
                    v7p3r_versions[version]["games"] += 1
                    
                    if result == "0-1":
                        v7p3r_versions[version]["wins"] += 1
                    elif result == "1-0":
                        v7p3r_versions[version]["losses"] += 1
                    elif result == "1/2-1/2":
                        v7p3r_versions[version]["draws"] += 1
                
                # Process SlowMate versions
                if self.is_slowmate_engine(white):
                    version = game.get("slowmate_version", "unknown")
                    slowmate_versions[version]["games"] += 1
                    
                    if result == "1-0":
                        slowmate_versions[version]["wins"] += 1
                    elif result == "0-1":
                        slowmate_versions[version]["losses"] += 1
                    elif result == "1/2-1/2":
                        slowmate_versions[version]["draws"] += 1
                
                elif self.is_slowmate_engine(black):
                    version = game.get("slowmate_version", "unknown")
                    slowmate_versions[version]["games"] += 1
                    
                    if result == "0-1":
                        slowmate_versions[version]["wins"] += 1
                    elif result == "1-0":
                        slowmate_versions[version]["losses"] += 1
                    elif result == "1/2-1/2":
                        slowmate_versions[version]["draws"] += 1
        
        # Convert to regular dicts and calculate percentages
        v7p3r_final = {}
        for version, stats in v7p3r_versions.items():
            total = stats["games"]
            if total > 0:
                v7p3r_final[version] = {
                    **stats,
                    "win_rate": stats["wins"] / total,
                    "score_percentage": (stats["wins"] + 0.5 * stats["draws"]) / total * 100
                }
        
        slowmate_final = {}
        for version, stats in slowmate_versions.items():
            total = stats["games"]
            if total > 0:
                slowmate_final[version] = {
                    **stats,
                    "win_rate": stats["wins"] / total,
                    "score_percentage": (stats["wins"] + 0.5 * stats["draws"]) / total * 100
                }
        
        return {
            "v7p3r_versions": v7p3r_final,
            "slowmate_versions": slowmate_final
        }
    
    def _generate_advanced_metrics(self, tournaments: Dict) -> Dict[str, Any]:
        """Generate advanced chess-specific metrics"""
        # This would include opening repertoire, endgame performance, tactical ability
        # For now, we'll provide a framework that can be expanded
        
        return {
            "opening_repertoire": {
                "v7p3r": {"analyzed": False, "reason": "Requires detailed game analysis"},
                "slowmate": {"analyzed": False, "reason": "Requires detailed game analysis"}
            },
            "endgame_performance": {
                "v7p3r": {"analyzed": False, "reason": "Requires position evaluation"},
                "slowmate": {"analyzed": False, "reason": "Requires position evaluation"}
            },
            "tactical_ability": {
                "v7p3r": {"analyzed": False, "reason": "Requires puzzle database"},
                "slowmate": {"analyzed": False, "reason": "Requires puzzle database"}
            }
        }
    
    def save_analysis(self, analysis_data: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """Save analysis results to JSON file"""
        if output_file is None:
            output_dir = Path(__file__).parent.parent / "dashboard" / "data"
            output_dir.mkdir(exist_ok=True)
            output_file = str(output_dir / "mvm_analysis.json")
        
        with open(output_file, 'w') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        print(f"💾 Analysis saved to {output_file}")
        return output_file

def main():
    """Run the Man vs Machine analysis"""
    analyzer = ManVsMachineAnalyzer()
    
    print("🚀 Starting Man vs Machine Analysis...")
    results = analyzer.analyze_all_tournaments()
    
    # Save results
    output_file = analyzer.save_analysis(results)
    
    # Print summary
    print("\n📊 Analysis Summary:")
    print("=" * 50)
    
    h2h = results.get("head_to_head_summary", {})
    if "error" not in h2h:
        print(f"🥊 Head-to-Head Games: {h2h.get('total_games', 0)}")
        print(f"🤖 V7P3R Score: {h2h.get('v7p3r_score_percentage', 0):.1f}%")
        print(f"🧠 SlowMate Score: {h2h.get('slowmate_score_percentage', 0):.1f}%")
        print(f"🤝 Draw Rate: {h2h.get('draw_rate', 0):.1f}%")
    
    v7p3r = results.get("v7p3r_summary", {})
    slowmate = results.get("slowmate_summary", {})
    
    print(f"\n🤖 V7P3R Overall: {v7p3r.get('total_games', 0)} games, {v7p3r.get('score_percentage', 0):.1f}% score")
    print(f"🧠 SlowMate Overall: {slowmate.get('total_games', 0)} games, {slowmate.get('score_percentage', 0):.1f}% score")
    
    print(f"\n📁 Results saved to: {output_file}")
    print("🚀 Ready to launch dashboard!")

if __name__ == "__main__":
    main()
