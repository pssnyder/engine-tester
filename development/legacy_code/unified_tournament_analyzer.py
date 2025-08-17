#!/usr/bin/env python3
"""
Unified Tournament Analyzer for Chess Engine Performance Metrics

Processes all PGN files across all tournament directories to create a comprehensive
analysis of engine performance, accounting for opponent strength and game frequency.

Features:
- Cross-tournament aggregate statistics
- Opponent-strength-adjusted scoring
- Unified ranking system across all engines
- Head-to-head performance matrices
- Statistical significance weighting
"""

import os
import json
import re
import datetime
import glob
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
import chess.pgn
import math
from name_mapper import load_name_mapping, normalize_engine_name_with_mapping

# Configuration
RESULTS_DIR = "results"
ENGINE_TEST_REPORT = "engine_test_report_20250808.json"
RESULTS_APPENDIX_FILE = "results_appendix.json"

# Engine strength estimates (will be dynamically calculated)
BASELINE_ENGINES = {
    "Random_Opponent": 0,  # Random moves = 0 ELO baseline
    "stockfish": 2800,  # Stockfish base rating
}

@dataclass
class EngineIdentity:
    """Normalized engine identity for grouping variants"""
    family: str
    version: str
    variant: str = ""
    
    @property
    def canonical_name(self) -> str:
        """Generate canonical display name"""
        if self.variant and self.variant not in ["RELEASE", "STABLE"]:
            return f"{self.family}_v{self.version}_{self.variant}"
        else:
            return f"{self.family}_v{self.version}"
    
    @property
    def sort_key(self) -> tuple:
        """Generate sort key for version ordering"""
        # Split version into parts for proper sorting
        parts = self.version.split('.')
        try:
            version_tuple = tuple(int(p) for p in parts)
        except ValueError:
            # Handle non-numeric version parts
            version_tuple = (0, 0, 0)
        
        # Variant priority (RELEASE > STABLE > BETA > ALPHA > others)
        variant_priority = {
            "RELEASE": 100,
            "STABLE": 90,
            "": 80,  # No variant (assumed release)
            "BETA": 70,
            "ALPHA": 60,
            "DELTA": 50,
            "EXPERIMENTAL": 40
        }
        
        priority = variant_priority.get(self.variant, 30)
        return (version_tuple, priority)

def normalize_engine_name(raw_name: str) -> EngineIdentity:
    """Extract normalized engine identity from raw name"""
    # Clean the name
    name = raw_name.strip()
    
    # Handle special cases first
    if "stockfish" in name.lower():
        return EngineIdentity(family="Stockfish", version="1.0", variant="1%")
    
    if "random" in name.lower() and "opponent" in name.lower():
        return EngineIdentity(family="Random_Opponent", version="1.0", variant="")
    
    if "copycat" in name.lower():
        # Extract version if present
        version_match = re.search(r'v?(\d+\.?\d*\.?\d*)', name)
        version = version_match.group(1) if version_match else "1.0"
        return EngineIdentity(family="Copycat", version=version, variant="")
    
    # Standard engine families
    family_patterns = [
        (r'(SlowMate)', 'SlowMate'),
        (r'(Cece)', 'Cece'),
        (r'(Cecilia)', 'Cecilia'),
        (r'(V7P3RAI)', 'V7P3RAI'),
    ]
    
    family = None
    for pattern, family_name in family_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            family = family_name
            break
    
    if not family:
        # Fallback: use first word as family
        family = name.split('_')[0].split(' ')[0]
    
    # Extract version
    version_patterns = [
        r'v(\d+\.\d+\.\d+)',  # v1.2.3
        r'v(\d+\.\d+)',       # v1.2
        r'v(\d+)',            # v1
        r'_(\d+\.\d+\.\d+)',  # _1.2.3
        r'_(\d+\.\d+)',       # _1.2
        r'\s(\d+\.\d+)',      # space 1.2
    ]
    
    version = "1.0"  # Default
    for pattern in version_patterns:
        match = re.search(pattern, name)
        if match:
            version = match.group(1)
            break
    
    # Extract variant/qualifier
    variant_patterns = [
        r'(?:v\d+\.?\d*\.?\d*[_\s]*)([A-Z]+)',  # After version: BETA, RELEASE, etc.
        r'_([A-Z][A-Za-z_]+)(?:_[A-Z][A-Za-z_]*)*$',  # End qualifiers
    ]
    
    variant = ""
    for pattern in variant_patterns:
        match = re.search(pattern, name)
        if match:
            candidate = match.group(1).upper()
            # Filter out known non-variant words
            if candidate not in ['EXE', 'ENGINE', 'CHESS'] and len(candidate) > 1:
                variant = candidate
                break
    
    # Clean up common variant names
    variant_mapping = {
        'RELEASE': 'RELEASE',
        'REL': 'RELEASE', 
        'STABLE': 'STABLE',
        'BETA': 'BETA',
        'ALPHA': 'ALPHA',
        'DELTA': 'DELTA',
        'EXPERIMENTAL': 'EXPERIMENTAL',
        'EXP': 'EXPERIMENTAL',
        'TACTICAL': 'TACTICAL',
        'OPENING': 'OPENING',
        'ENDGAME': 'ENDGAME',
        'MIDDLEGAME': 'MIDDLEGAME',
        'TIME': 'TIME',
        'SEARCH': 'SEARCH',
        'ENHANCED': 'ENHANCED',
        'INTELLIGENCE': 'INTELLIGENCE',
        'MANAGEMENT': 'MANAGEMENT',
        'ENHANCEMENTS': 'ENHANCEMENTS',
        'BASELINE': 'BASELINE',
        'REVISION': 'REVISION',
        'NUCLEAR': 'NUCLEAR',
        'VERSION': 'VERSION',
        'FIX': 'FIX',
        'FIXED': 'FIXED'
    }
    
    # Normalize variant
    if variant in variant_mapping:
        variant = variant_mapping[variant]
    
    return EngineIdentity(family=family, version=version, variant=variant)

@dataclass
class GameRecord:
    """Individual game record with metadata"""
    white: str
    black: str
    result: str  # "1-0", "0-1", "1/2-1/2"
    tournament: str
    date: str
    moves: List[str]
    termination: str
    opening: str = ""
    eco: str = ""
    
    def get_winner(self) -> Optional[str]:
        if self.result == "1-0":
            return self.white
        elif self.result == "0-1":
            return self.black
        return None  # Draw or unknown
    
    def involves_engine(self, engine_name: str) -> bool:
        return engine_name in [self.white, self.black]
    
    def get_opponent(self, engine_name: str) -> Optional[str]:
        if self.white == engine_name:
            return self.black
        elif self.black == engine_name:
            return self.white
        return None

@dataclass
class EnginePerformance:
    """Comprehensive engine performance across all tournaments"""
    name: str
    total_games: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    tournaments: set = field(default_factory=set)
    
    # Opponent tracking
    opponents: Dict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(lambda: {"wins": 0, "losses": 0, "draws": 0}))
    
    # Performance by tournament
    tournament_performance: Dict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(lambda: {"wins": 0, "losses": 0, "draws": 0, "games": 0}))
    
    # Special achievements
    stockfish_results: List[GameRecord] = field(default_factory=list)
    notable_victories: List[GameRecord] = field(default_factory=list)
    
    # Calculated metrics
    estimated_rating: float = 1200.0  # Starting estimate
    performance_rating: float = 1200.0
    reliability_score: float = 0.0  # Based on game count and opponent diversity
    
    def add_game(self, game: GameRecord, playing_white: bool):
        """Add a game result to this engine's performance"""
        self.total_games += 1
        self.tournaments.add(game.tournament)
        
        opponent = game.black if playing_white else game.white
        tournament = game.tournament
        
        # Track stockfish games specially
        if "stockfish" in opponent.lower():
            self.stockfish_results.append(game)
        
        # Update tournament-specific performance
        self.tournament_performance[tournament]["games"] += 1
        
        if game.result == "1-0":  # White wins
            if playing_white:
                self.wins += 1
                self.opponents[opponent]["wins"] += 1
                self.tournament_performance[tournament]["wins"] += 1
            else:
                self.losses += 1
                self.opponents[opponent]["losses"] += 1
                self.tournament_performance[tournament]["losses"] += 1
        elif game.result == "0-1":  # Black wins
            if not playing_white:
                self.wins += 1
                self.opponents[opponent]["wins"] += 1
                self.tournament_performance[tournament]["wins"] += 1
            else:
                self.losses += 1
                self.opponents[opponent]["losses"] += 1
                self.tournament_performance[tournament]["losses"] += 1
        else:  # Draw
            self.draws += 1
            self.opponents[opponent]["draws"] += 1
            self.tournament_performance[tournament]["draws"] += 1
    
    @property
    def win_rate(self) -> float:
        return (self.wins / self.total_games * 100) if self.total_games > 0 else 0.0
    
    @property
    def score(self) -> float:
        return self.wins + 0.5 * self.draws
    
    @property
    def score_percentage(self) -> float:
        return (self.score / self.total_games * 100) if self.total_games > 0 else 0.0

class UnifiedTournamentAnalyzer:
    """Analyze all tournaments together for comprehensive engine ranking"""
    
    def __init__(self, results_dir: str = RESULTS_DIR):
        self.results_dir = results_dir
        self.games: List[GameRecord] = []
        # Normalized games (canonical names) for downstream temporal filtering / dashboard
        self.normalized_games: List[GameRecord] = []
        self.engines: Dict[str, EnginePerformance] = {}  # Using canonical names as keys
        self.tournaments: Dict[str, Dict] = {}
        self.engine_ratings: Dict[str, float] = {}
        self.manual_name_mapping: Dict[str, str] = {}  # Manual mapping from file
        self.rating_overrides: Dict[str, float] = {}  # Manual rating overrides

        # Load manual name mapping and rating overrides
        self.manual_name_mapping, self.rating_overrides = load_name_mapping()
        print(f"📋 Loaded manual name mapping with {len(self.manual_name_mapping)} variants")
        if self.rating_overrides:
            print(f"📊 Loaded {len(self.rating_overrides)} rating overrides: {', '.join(self.rating_overrides.keys())}")
        
    def get_canonical_name(self, raw_name: str) -> str:
        """Get canonical name for a raw engine name using manual mapping"""
        return normalize_engine_name_with_mapping(raw_name, self.manual_name_mapping)
        
    def find_all_pgn_files(self) -> List[Tuple[str, str]]:
        """Find all PGN files in tournament directories"""
        pgn_files = []
        
        # Look in tournament subdirectories
        tournament_dirs = glob.glob(os.path.join(self.results_dir, "*"))
        for dir_path in tournament_dirs:
            if os.path.isdir(dir_path):
                tournament_name = os.path.basename(dir_path)
                pgn_files_in_dir = glob.glob(os.path.join(dir_path, "*.pgn"))
                for pgn_file in pgn_files_in_dir:
                    pgn_files.append((pgn_file, tournament_name))
        
        # Also check root results directory
        root_pgns = glob.glob(os.path.join(self.results_dir, "*.pgn"))
        for pgn_file in root_pgns:
            pgn_files.append((pgn_file, "root_tournament"))
            
        return pgn_files
    
    def parse_pgn_file(self, filepath: str, tournament_name: str) -> List[GameRecord]:
        """Parse a PGN file and return game records"""
        games = []
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                game_count = 0
                while True:
                    try:
                        game = chess.pgn.read_game(f)
                        if game is None:
                            break
                        
                        game_count += 1
                        if game_count % 100 == 0:
                            print(f"  Processed {game_count} games from {os.path.basename(filepath)}...")
                        
                        # Extract game info
                        headers = game.headers
                        white = headers.get("White", "Unknown")
                        black = headers.get("Black", "Unknown")
                        result = headers.get("Result", "*")
                        date = headers.get("Date", "????.??.??")
                        termination = headers.get("Termination", "normal")
                        opening = headers.get("Opening", "")
                        eco = headers.get("ECO", "")
                        
                        # Extract moves (simplified - just get move count for performance)
                        moves = []
                        try:
                            # Only extract moves if we need them for analysis
                            # For now, just count the moves to avoid performance issues
                            node = game
                            move_count = 0
                            while node.variations and move_count < 200:  # Limit moves to avoid infinite loops
                                next_node = node.variation(0)
                                move_count += 1
                                node = next_node
                            
                            # Store a simplified move list for now
                            moves = [f"move_{i}" for i in range(move_count)]
                        except Exception as move_error:
                            print(f"  Warning: Error extracting moves from game {game_count}: {move_error}")
                            moves = []
                        
                        # Skip incomplete games
                        if result in ["1-0", "0-1", "1/2-1/2"]:
                            game_record = GameRecord(
                                white=white,
                                black=black,
                                result=result,
                                tournament=tournament_name,
                                date=date,
                                moves=moves,
                                termination=termination,
                                opening=opening,
                                eco=eco
                            )
                            games.append(game_record)
                    
                    except Exception as game_error:
                        print(f"  Warning: Error parsing game {game_count} in {filepath}: {game_error}")
                        continue
                        
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
        
        print(f"  Loaded {len(games)} valid games from {os.path.basename(filepath)}")
        return games
    
    def load_all_games(self):
        """Load all games from all PGN files"""
        pgn_files = self.find_all_pgn_files()
        print(f"Found {len(pgn_files)} PGN files to process")
        
        for pgn_file, tournament_name in pgn_files:
            print(f"Processing {os.path.basename(pgn_file)} from {tournament_name}...")
            games = self.parse_pgn_file(pgn_file, tournament_name)
            self.games.extend(games)
            
            # Track tournament metadata
            if tournament_name not in self.tournaments:
                self.tournaments[tournament_name] = {
                    "games": len(games),
                    "file": pgn_file,
                    "engines": set()
                }
            else:
                self.tournaments[tournament_name]["games"] += len(games)
        
        print(f"Loaded {len(self.games)} total games from {len(self.tournaments)} tournaments")
    
    def process_all_games(self):
        """Process all games and build engine performance data"""
        for game in self.games:
            # Get canonical names for both engines
            canonical_white = self.get_canonical_name(game.white)
            canonical_black = self.get_canonical_name(game.black)
            
            # Ensure engines exist with canonical names
            for canonical_name in [canonical_white, canonical_black]:
                if canonical_name not in self.engines:
                    self.engines[canonical_name] = EnginePerformance(name=canonical_name)
                
                # Track which tournaments each engine participated in
                self.tournaments[game.tournament]["engines"].add(canonical_name)
            
            # Create a normalized game record for processing
            normalized_game = GameRecord(
                white=canonical_white,
                black=canonical_black,
                result=game.result,
                tournament=game.tournament,
                date=game.date,
                moves=game.moves,
                termination=game.termination,
                opening=game.opening,
                eco=game.eco
            )
            # Store normalized game for later date / range filtering in dashboard
            self.normalized_games.append(normalized_game)
            
            # Add game to both engines' records using canonical names
            self.engines[canonical_white].add_game(normalized_game, playing_white=True)
            self.engines[canonical_black].add_game(normalized_game, playing_white=False)
    
    def calculate_reliability_scores(self):
        """Calculate reliability scores based on game count and opponent diversity"""
        for engine in self.engines.values():
            # Base reliability on number of games (logarithmic scale)
            game_factor = min(1.0, math.log(max(1, engine.total_games)) / math.log(100))
            
            # Factor in opponent diversity
            unique_opponents = len(engine.opponents)
            opponent_factor = min(1.0, unique_opponents / 10.0)  # Cap at 10 opponents
            
            # Factor in tournament diversity
            tournament_factor = min(1.0, len(engine.tournaments) / 5.0)  # Cap at 5 tournaments
            
            # Combined reliability score
            engine.reliability_score = (game_factor * 0.5 + opponent_factor * 0.3 + tournament_factor * 0.2)
    
    def estimate_engine_ratings(self):
        """Estimate engine ratings using manual overrides and iterative ELO-like calculation"""
        # Start with baseline ratings using canonical names
        for canonical_name in self.engines:
            # First check for manual rating override
            if canonical_name in self.rating_overrides:
                self.engine_ratings[canonical_name] = self.rating_overrides[canonical_name]
                print(f"🎯 Using manual rating override for '{canonical_name}': {self.rating_overrides[canonical_name]} ELO")
                continue
                
            # Otherwise calculate baseline using identity parsing
            identity = normalize_engine_name(canonical_name)
            
            # Check if this is a baseline engine
            baseline_rating = None
            if identity.family.lower() == "stockfish":
                # Adjust for strength percentage if specified
                if identity.variant and "%" in identity.variant:
                    strength_match = re.search(r'(\d+)', identity.variant)
                    if strength_match:
                        strength_pct = int(strength_match.group(1))
                        # Rough approximation: each 1% = ~28 ELO reduction from max
                        baseline_rating = 2800 - (100 - strength_pct) * 28
                        baseline_rating = max(800, baseline_rating)
                    else:
                        baseline_rating = 2800
                else:
                    baseline_rating = 2800
            elif identity.family.lower() == "random_opponent":
                baseline_rating = 600  # Random moves baseline
            else:
                baseline_rating = 1200  # Default starting rating
                
            self.engine_ratings[canonical_name] = baseline_rating
        
        # Iterative rating adjustment based on results
        for iteration in range(10):
            new_ratings = self.engine_ratings.copy()
            
            for engine_name, engine in self.engines.items():
                # Skip engines with manual rating overrides - they are fixed
                if engine_name in self.rating_overrides:
                    continue
                    
                if engine.total_games < 5:  # Skip engines with too few games
                    continue
                
                rating_adjustments = []
                
                for opponent, results in engine.opponents.items():
                    if opponent not in self.engine_ratings:
                        continue
                    
                    total_games = results["wins"] + results["losses"] + results["draws"]
                    if total_games == 0:
                        continue
                    
                    # Calculate expected score based on rating difference
                    rating_diff = self.engine_ratings[opponent] - self.engine_ratings[engine_name]
                    expected_score = 1 / (1 + 10 ** (rating_diff / 400))
                    
                    # Calculate actual score
                    actual_score = (results["wins"] + 0.5 * results["draws"]) / total_games
                    
                    # Calculate rating adjustment (K-factor based on reliability)
                    k_factor = 32 * (1 - engine.reliability_score * 0.5)  # Lower K for more reliable engines
                    adjustment = k_factor * (actual_score - expected_score)
                    
                    rating_adjustments.append(adjustment)
                
                if rating_adjustments:
                    avg_adjustment = sum(rating_adjustments) / len(rating_adjustments)
                    new_ratings[engine_name] = max(600, min(3000, self.engine_ratings[engine_name] + avg_adjustment))
            
            self.engine_ratings = new_ratings
        
        # Update engine performance objects with calculated ratings
        for engine_name, rating in self.engine_ratings.items():
            if engine_name in self.engines:
                self.engines[engine_name].estimated_rating = rating
    
    def calculate_performance_ratings(self):
        """Calculate performance ratings based on opponent strength"""
        for engine_name, engine in self.engines.items():
            if engine.total_games < 3:
                engine.performance_rating = engine.estimated_rating
                continue
            
            total_opponent_rating = 0
            total_games = 0
            
            for opponent, results in engine.opponents.items():
                if opponent in self.engine_ratings:
                    games = results["wins"] + results["losses"] + results["draws"]
                    score = (results["wins"] + 0.5 * results["draws"]) / games
                    
                    # Performance rating calculation
                    opponent_rating = self.engine_ratings[opponent]
                    
                    if score == 1.0:
                        performance_vs_opponent = opponent_rating + 400
                    elif score == 0.0:
                        performance_vs_opponent = opponent_rating - 400
                    else:
                        performance_vs_opponent = opponent_rating + 400 * math.log10(score / (1 - score))
                    
                    total_opponent_rating += performance_vs_opponent * games
                    total_games += games
            
            if total_games > 0:
                engine.performance_rating = total_opponent_rating / total_games
            else:
                engine.performance_rating = engine.estimated_rating
    
    def get_unified_rankings(self) -> List[EnginePerformance]:
        """Get engines ranked by estimated rating"""
        return sorted(
            [e for e in self.engines.values() if e.total_games >= 3],
            key=lambda e: e.estimated_rating,
            reverse=True
        )
    
    def get_stockfish_achievers(self) -> List[EnginePerformance]:
        """Get engines that have notable results against Stockfish"""
        achievers = []
        for engine in self.engines.values():
            if engine.stockfish_results:
                # Count draws and wins against Stockfish
                stockfish_wins = sum(1 for game in engine.stockfish_results if game.get_winner() == engine.name)
                stockfish_draws = sum(1 for game in engine.stockfish_results if game.get_winner() is None)
                
                if stockfish_wins > 0 or stockfish_draws > 0:
                    achievers.append(engine)
        
        return sorted(achievers, key=lambda e: len(e.stockfish_results), reverse=True)
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        
        # Load consolidation info from the manual mapping file
        try:
            with open(os.path.join(self.results_dir, "name_consolidation.json"), 'r') as f:
                mapping_data = json.load(f)
            consolidations = mapping_data.get('name_consolidation', {}).get('consolidations', {})
            
            consolidation_summary = {
                "consolidated_engines": len(consolidations),
                "total_raw_names": sum(len(variants) for variants in consolidations.values()),
                "consolidated_groups": consolidations
            }
        except Exception as e:
            print(f"Warning: Could not load consolidation info: {e}")
            consolidation_summary = {
                "consolidated_engines": 0,
                "total_raw_names": 0,
                "consolidated_groups": {}
            }

        # Derive date range and compact game list (only essential fields) for dashboard filters
        compact_games = []
        min_date = None
        max_date = None
        for g in self.normalized_games:
            # Expect dates like YYYY.MM.DD; skip if unknown
            raw_date = g.date
            if raw_date and re.match(r"\d{4}\.\d{2}\.\d{2}", raw_date):
                iso_date = raw_date.replace('.', '-')
                try:
                    # Validate date
                    datetime.date.fromisoformat(iso_date)
                except ValueError:
                    continue
                compact_games.append({
                    "white": g.white,
                    "black": g.black,
                    "result": g.result,
                    "date": iso_date,
                    "tournament": g.tournament
                })
                if not min_date or iso_date < min_date:
                    min_date = iso_date
                if not max_date or iso_date > max_date:
                    max_date = iso_date

        return {
            "analysis_date": datetime.datetime.now().isoformat(),
            "consolidation_summary": consolidation_summary,
            "date_range": {"min": min_date, "max": max_date},
            "games": compact_games,
            "summary": {
                "total_games": len(self.games),
                "total_engines": len(self.engines),
                "total_tournaments": len(self.tournaments),
                "engines_with_sufficient_data": len([e for e in self.engines.values() if e.total_games >= 3])
            },
            "tournaments": {
                name: {
                    "games": data["games"],
                    "engines": list(data["engines"]),
                    "file": os.path.basename(data["file"])
                }
                for name, data in self.tournaments.items()
            },
            "unified_rankings": [
                {
                    "rank": i + 1,
                    "name": engine.name,
                    "estimated_rating": round(engine.estimated_rating, 1),
                    "performance_rating": round(engine.performance_rating, 1),
                    "games": engine.total_games,
                    "score": engine.score,
                    "win_rate": round(engine.win_rate, 2),
                    "score_percentage": round(engine.score_percentage, 2),
                    "tournaments": len(engine.tournaments),
                    "opponents": len(engine.opponents),
                    "reliability_score": round(engine.reliability_score, 3),
                    "stockfish_games": len(engine.stockfish_results) if hasattr(engine, 'stockfish_results') else 0
                }
                for i, engine in enumerate(self.get_unified_rankings())
            ],
            "stockfish_achievers": [
                {
                    "name": engine.name,
                    "stockfish_games": len(engine.stockfish_results),
                    "wins_vs_stockfish": sum(1 for game in engine.stockfish_results if game.get_winner() == engine.name),
                    "draws_vs_stockfish": sum(1 for game in engine.stockfish_results if game.get_winner() is None),
                    "losses_vs_stockfish": sum(1 for game in engine.stockfish_results if game.get_winner() and game.get_winner() != engine.name),
                    "estimated_rating": round(engine.estimated_rating, 1)
                }
                for engine in self.get_stockfish_achievers()
            ],
            "engine_details": {
                engine.name: {
                    "performance": {
                        "total_games": engine.total_games,
                        "wins": engine.wins,
                        "losses": engine.losses,
                        "draws": engine.draws,
                        "score": engine.score,
                        "win_rate": round(engine.win_rate, 2),
                        "estimated_rating": round(engine.estimated_rating, 1),
                        "performance_rating": round(engine.performance_rating, 1),
                        "reliability_score": round(engine.reliability_score, 3)
                    },
                    "tournaments": list(engine.tournaments),
                    "opponents": {
                        opp: {"wins": results["wins"], "losses": results["losses"], "draws": results["draws"]}
                        for opp, results in engine.opponents.items()
                    },
                    "tournament_breakdown": {
                        tourn: {"wins": results["wins"], "losses": results["losses"], "draws": results["draws"], "games": results["games"]}
                        for tourn, results in engine.tournament_performance.items()
                    }
                }
                for engine in self.engines.values()
                if engine.total_games >= 3
            }
        }
    
    def save_report(self, output_path: str):
        """Save comprehensive report to JSON file"""
        report = self.generate_comprehensive_report()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"Comprehensive analysis saved to {output_path}")

def main():
    print("🏁 Starting Unified Tournament Analysis...")
    
    analyzer = UnifiedTournamentAnalyzer()
    
    # Load and process all games
    analyzer.load_all_games()
    analyzer.process_all_games()
    
    # Calculate advanced metrics
    print("📊 Calculating reliability scores...")
    analyzer.calculate_reliability_scores()
    
    print("🎯 Estimating engine ratings...")
    analyzer.estimate_engine_ratings()
    
    print("⚡ Calculating performance ratings...")
    analyzer.calculate_performance_ratings()
    
    # Generate and save report
    output_file = os.path.join(analyzer.results_dir, "unified_tournament_analysis.json")
    analyzer.save_report(output_file)
    
    # Display consolidation summary
    report = analyzer.generate_comprehensive_report()
    consolidation_info = report["consolidation_summary"]
    
    print(f"\n📝 ENGINE NAME CONSOLIDATION:")
    print("=" * 60)
    print(f"Consolidated {consolidation_info['consolidated_engines']} engine groups from {consolidation_info['total_raw_names']} raw names")
    
    for canonical_name, raw_names in consolidation_info["consolidated_groups"].items():
        print(f"\n{canonical_name}:")
        for raw_name in raw_names:
            print(f"  ← {raw_name}")
    
    # Display summary
    rankings = analyzer.get_unified_rankings()
    stockfish_achievers = analyzer.get_stockfish_achievers()
    
    print(f"\n🏆 TOP ENGINE RANKINGS (Estimated Rating):")
    print("=" * 60)
    for i, engine in enumerate(rankings[:10], 1):
        print(f"{i:2d}. {engine.name:<30} {engine.estimated_rating:4.0f} ELO "
              f"({engine.total_games:3d} games, {engine.win_rate:5.1f}% wins)")
    
    print(f"\n⚔️  STOCKFISH ACHIEVERS:")
    print("=" * 60)
    for engine in stockfish_achievers:
        wins = sum(1 for game in engine.stockfish_results if game.get_winner() == engine.name)
        draws = sum(1 for game in engine.stockfish_results if game.get_winner() is None)
        total = len(engine.stockfish_results)
        print(f"{engine.name:<30} {wins}W-{draws}D-{total-wins-draws}L vs Stockfish "
              f"(Rating: {engine.estimated_rating:.0f})")

if __name__ == "__main__":
    main()
