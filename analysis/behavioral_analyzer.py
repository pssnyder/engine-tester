#!/usr/bin/env python3
"""
Engine Behavioral Pattern Analyzer

Analyzes chess engines for:
- Playing style categorization (aggressive, positional, tactical)
- Move pattern signatures
- Opening preferences and repertoire analysis
- Decisiveness and tactical complexity metrics
- Piece usage preferences and territorial patterns
"""

import os
import json
import chess
import chess.pgn
import chess.engine
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set, Optional, Any
import re
from pathlib import Path
import statistics

class EngineBehavioralAnalyzer:
    def __init__(self, results_dir='results'):
        self.results_dir = results_dir
        self.engine_profiles = {}
        self.move_patterns = defaultdict(lambda: defaultdict(int))
        self.opening_book = self.load_opening_database()
        
    def load_opening_database(self):
        """Load basic opening patterns for recognition"""
        return {
            'e4': 'King\'s Pawn Game',
            'd4': 'Queen\'s Pawn Game', 
            'Nf3': 'Réti Opening',
            'c4': 'English Opening',
            'f4': 'King\'s Indian Attack',
            'b3': 'Larsen\'s Opening',
            'g3': 'Benko\'s Opening',
            'Nc3': 'Dunst Opening',
            'e4 e5': 'King\'s Pawn Game',
            'e4 c5': 'Sicilian Defense',
            'e4 e6': 'French Defense',
            'e4 c6': 'Caro-Kann Defense',
            'd4 d5': 'Queen\'s Gambit',
            'd4 Nf6': 'Indian Defense',
            'd4 f5': 'Dutch Defense',
            'Nf3 d5': 'Réti Opening',
            'Nf3 Nf6': 'King\'s Indian Attack',
            'c4 e5': 'English Opening',
            'f4 d5': 'King\'s Indian Attack',
        }
    
    def analyze_engine_behavior(self, pgn_files: List[str]) -> Dict[str, Any]:
        """Main analysis function for all PGN files"""
        print("🔍 Starting comprehensive behavioral analysis...")
        
        all_games = []
        for pgn_file in pgn_files:
            games = self.load_games_from_pgn(pgn_file)
            all_games.extend(games)
            print(f"  📁 Loaded {len(games)} games from {os.path.basename(pgn_file)}")
        
        print(f"  📊 Total games for analysis: {len(all_games)}")
        
        # Analyze each engine's behavior
        engine_stats = defaultdict(lambda: {
            'game_count': 0,
            'moves': [],
            'openings': defaultdict(int),
            'outcomes': defaultdict(int),
            'pieces_moved': defaultdict(int),
            'squares_used': defaultdict(lambda: defaultdict(int)),
            'move_times': [],
            'game_lengths': [],
            'captures': 0,
            'checks': 0,
            'castling': {'kingside': 0, 'queenside': 0},
            'piece_activity': defaultdict(lambda: defaultdict(int)),
            'positional_features': defaultdict(int)
        })
        
        for game in all_games:
            self.analyze_single_game(game, engine_stats)
        
        # Calculate behavioral profiles
        behavioral_profiles = {}
        for engine, stats in engine_stats.items():
            if stats['game_count'] >= 5:  # Only analyze engines with sufficient data
                behavioral_profiles[engine] = self.calculate_behavioral_profile(engine, stats)
        
        # Generate engine categorization
        engine_categories = self.categorize_engines(behavioral_profiles)
        
        # Create comparative analysis
        comparative_analysis = self.generate_comparative_analysis(behavioral_profiles)
        
        return {
            'behavioral_profiles': behavioral_profiles,
            'engine_categories': engine_categories,
            'comparative_analysis': comparative_analysis,
            'move_pattern_signatures': dict(self.move_patterns),
            'analysis_metadata': {
                'total_games': len(all_games),
                'engines_analyzed': len(behavioral_profiles),
                'analysis_date': pd.Timestamp.now().isoformat()
            }
        }
    
    def load_games_from_pgn(self, pgn_file: str) -> List[chess.pgn.Game]:
        """Load games from a PGN file"""
        games = []
        try:
            with open(pgn_file, 'r') as f:
                while True:
                    game = chess.pgn.read_game(f)
                    if game is None:
                        break
                    games.append(game)
        except Exception as e:
            print(f"  ⚠️ Error loading {pgn_file}: {e}")
        return games
    
    def analyze_single_game(self, game: chess.pgn.Game, engine_stats: Dict):
        """Analyze a single game for behavioral patterns"""
        white_player = game.headers.get('White', 'Unknown')
        black_player = game.headers.get('Black', 'Unknown')
        result = game.headers.get('Result', '*')
        
        # Normalize engine names
        white_player = self.normalize_engine_name(white_player)
        black_player = self.normalize_engine_name(black_player)
        
        board = game.board()
        moves = list(game.mainline_moves())
        
        if len(moves) < 4:  # Skip very short games
            return
        
        # Analyze opening
        opening = self.identify_opening(moves[:6])
        
        # Track game statistics
        engine_stats[white_player]['game_count'] += 1
        engine_stats[black_player]['game_count'] += 1
        
        for i, (move, player) in enumerate(zip(moves, [white_player, black_player] * len(moves))):
            if i >= len(moves):
                break
                
            engine_stats[player]['moves'].append(str(move))
            
            # Track piece moved
            piece = board.piece_at(move.from_square)
            if piece:
                piece_symbol = piece.symbol().upper()
                engine_stats[player]['pieces_moved'][piece_symbol] += 1
                
                # Track square usage
                from_square = chess.square_name(move.from_square)
                to_square = chess.square_name(move.to_square)
                engine_stats[player]['squares_used'][piece_symbol][from_square] += 1
                engine_stats[player]['squares_used'][piece_symbol][to_square] += 1
            
            # Track captures and checks
            if board.is_capture(move):
                engine_stats[player]['captures'] += 1
            
            board.push(move)
            
            if board.is_check():
                engine_stats[player]['checks'] += 1
            
            # Track castling
            if move in [chess.Move.from_uci('e1g1'), chess.Move.from_uci('e8g8')]:
                engine_stats[player]['castling']['kingside'] += 1
            elif move in [chess.Move.from_uci('e1c1'), chess.Move.from_uci('e8c8')]:
                engine_stats[player]['castling']['queenside'] += 1
        
        # Record opening and outcome
        engine_stats[white_player]['openings'][opening] += 1
        engine_stats[black_player]['openings'][opening] += 1
        engine_stats[white_player]['game_lengths'].append(len(moves))
        engine_stats[black_player]['game_lengths'].append(len(moves))
        
        # Record outcomes
        if result == '1-0':
            engine_stats[white_player]['outcomes']['win'] += 1
            engine_stats[black_player]['outcomes']['loss'] += 1
        elif result == '0-1':
            engine_stats[white_player]['outcomes']['loss'] += 1
            engine_stats[black_player]['outcomes']['win'] += 1
        else:
            engine_stats[white_player]['outcomes']['draw'] += 1
            engine_stats[black_player]['outcomes']['draw'] += 1
    
    def normalize_engine_name(self, name: str) -> str:
        """Normalize engine names for consistency"""
        # Remove common suffixes and normalize
        name = re.sub(r'_v?\d+\.\d+.*', '', name)
        name = re.sub(r'_uci$', '', name)
        name = re.sub(r'_BETA$', '', name)
        name = re.sub(r'_ENHANCED.*$', '', name)
        name = re.sub(r'_FIXED$', '', name)
        return name.strip()
    
    def identify_opening(self, moves: List[chess.Move]) -> str:
        """Identify opening from first few moves"""
        move_sequence = ' '.join([str(move) for move in moves[:4]])
        
        # Check for known opening patterns
        for pattern, opening_name in self.opening_book.items():
            if move_sequence.startswith(pattern.replace(' ', '')):
                return opening_name
        
        # Basic categorization by first move
        if moves:
            first_move = str(moves[0])
            if first_move in self.opening_book:
                return self.opening_book[first_move]
        
        return 'Unknown Opening'
    
    def calculate_behavioral_profile(self, engine: str, stats: Dict) -> Dict[str, Any]:
        """Calculate comprehensive behavioral profile for an engine"""
        total_moves = len(stats['moves'])
        total_games = stats['game_count']
        
        if total_moves == 0 or total_games == 0:
            return {}
        
        # Calculate aggression metrics
        capture_rate = stats['captures'] / total_moves if total_moves > 0 else 0
        check_rate = stats['checks'] / total_moves if total_moves > 0 else 0
        aggression_score = (capture_rate * 0.6 + check_rate * 0.4) * 100
        
        # Calculate decisiveness
        total_outcomes = sum(stats['outcomes'].values())
        if total_outcomes > 0:
            win_rate = stats['outcomes']['win'] / total_outcomes
            draw_rate = stats['outcomes']['draw'] / total_outcomes
            decisiveness_score = (win_rate * 0.7 + (1 - draw_rate) * 0.3) * 100
        else:
            decisiveness_score = 0
        
        # Calculate piece preference diversity
        piece_counts = stats['pieces_moved']
        total_piece_moves = sum(piece_counts.values())
        piece_diversity = len([p for p, count in piece_counts.items() if count > total_piece_moves * 0.05])
        
        # Calculate average game length and style inference
        avg_game_length = statistics.mean(stats['game_lengths']) if stats['game_lengths'] else 0
        
        # Determine playing style
        style_factors = {
            'tactical': aggression_score * 0.4 + check_rate * 60,
            'positional': (100 - aggression_score) * 0.6 + avg_game_length * 0.02,
            'aggressive': aggression_score * 0.8 + capture_rate * 80,
            'defensive': (100 - aggression_score) * 0.7 + draw_rate * 50
        }
        
        primary_style = max(style_factors.items(), key=lambda x: x[1])[0]
        
        # Calculate opening repertoire diversity
        opening_counts = stats['openings']
        total_opening_games = sum(opening_counts.values())
        opening_diversity = len(opening_counts) if opening_counts else 0
        
        # Find signature moves (most common moves)
        move_counter = Counter(stats['moves'])
        signature_moves = dict(move_counter.most_common(10))
        
        # Find favorite pieces
        favorite_pieces = dict(sorted(piece_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        
        return {
            'engine_name': engine,
            'total_games': total_games,
            'total_moves': total_moves,
            'behavioral_scores': {
                'aggression': round(aggression_score, 2),
                'decisiveness': round(decisiveness_score, 2),
                'piece_diversity': piece_diversity,
                'opening_diversity': opening_diversity
            },
            'playing_style': {
                'primary_style': primary_style,
                'style_scores': {k: round(v, 2) for k, v in style_factors.items()}
            },
            'performance_metrics': {
                'win_rate': round(win_rate * 100, 2) if total_outcomes > 0 else 0,
                'draw_rate': round(draw_rate * 100, 2) if total_outcomes > 0 else 0,
                'avg_game_length': round(avg_game_length, 1),
                'capture_rate': round(capture_rate * 100, 2),
                'check_rate': round(check_rate * 100, 2)
            },
            'signature_patterns': {
                'favorite_moves': signature_moves,
                'favorite_pieces': favorite_pieces,
                'preferred_openings': dict(sorted(opening_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
                'castling_preference': stats['castling']
            },
            'territorial_analysis': self.analyze_territorial_preferences(stats['squares_used'])
        }
    
    def analyze_territorial_preferences(self, squares_used: Dict) -> Dict:
        """Analyze which squares each piece type prefers"""
        territorial_prefs = {}
        
        for piece, square_counts in squares_used.items():
            if not square_counts:
                continue
                
            total_squares = sum(square_counts.values())
            # Get top 8 squares for each piece
            top_squares = dict(sorted(square_counts.items(), key=lambda x: x[1], reverse=True)[:8])
            
            # Calculate preference percentages
            square_prefs = {square: round((count / total_squares) * 100, 1) 
                          for square, count in top_squares.items()}
            
            territorial_prefs[piece] = square_prefs
        
        return territorial_prefs
    
    def categorize_engines(self, profiles: Dict) -> Dict[str, List[str]]:
        """Categorize engines into behavioral groups"""
        categories = {
            'aggressive_fighters': [],
            'positional_masters': [],
            'tactical_wizards': [],
            'defensive_specialists': [],
            'balanced_players': [],
            'developing_engines': []
        }
        
        for engine, profile in profiles.items():
            if not profile or 'behavioral_scores' not in profile:
                continue
                
            scores = profile['behavioral_scores']
            style = profile['playing_style']
            
            aggression = scores.get('aggression', 0)
            decisiveness = scores.get('decisiveness', 0)
            primary_style = style.get('primary_style', 'balanced')
            
            # Categorize based on behavioral metrics
            if primary_style == 'aggressive' and aggression > 15:
                categories['aggressive_fighters'].append(engine)
            elif primary_style == 'positional' and decisiveness > 60:
                categories['positional_masters'].append(engine)
            elif primary_style == 'tactical' and scores.get('piece_diversity', 0) > 5:
                categories['tactical_wizards'].append(engine)
            elif primary_style == 'defensive' and profile['performance_metrics'].get('draw_rate', 0) > 20:
                categories['defensive_specialists'].append(engine)
            elif profile['total_games'] < 50:
                categories['developing_engines'].append(engine)
            else:
                categories['balanced_players'].append(engine)
        
        return categories
    
    def generate_comparative_analysis(self, profiles: Dict) -> Dict:
        """Generate comparative analysis between engines"""
        if not profiles:
            return {}
        
        # Extract metrics for comparison
        metrics_data = {}
        for engine, profile in profiles.items():
            if not profile or 'behavioral_scores' not in profile:
                continue
                
            metrics_data[engine] = {
                'aggression': profile['behavioral_scores'].get('aggression', 0),
                'decisiveness': profile['behavioral_scores'].get('decisiveness', 0),
                'win_rate': profile['performance_metrics'].get('win_rate', 0),
                'avg_game_length': profile['performance_metrics'].get('avg_game_length', 0),
                'capture_rate': profile['performance_metrics'].get('capture_rate', 0),
                'piece_diversity': profile['behavioral_scores'].get('piece_diversity', 0)
            }
        
        if not metrics_data:
            return {}
        
        # Calculate averages and rankings
        df = pd.DataFrame(metrics_data).T
        
        rankings = {}
        for metric in df.columns:
            rankings[f'top_{metric}'] = df[metric].nlargest(5).to_dict()
            rankings[f'avg_{metric}'] = df[metric].mean()
        
        # Find correlations
        correlations = df.corr().to_dict()
        
        # Identify engine relationships
        relationships = self.find_engine_relationships(profiles)
        
        return {
            'rankings': rankings,
            'correlations': correlations,
            'relationships': relationships,
            'summary_stats': {
                'total_engines': len(metrics_data),
                'most_aggressive': df['aggression'].idxmax() if not df.empty else None,
                'most_decisive': df['decisiveness'].idxmax() if not df.empty else None,
                'highest_win_rate': df['win_rate'].idxmax() if not df.empty else None
            }
        }
    
    def find_engine_relationships(self, profiles: Dict) -> Dict:
        """Find relationships and similarities between engines"""
        relationships = {
            'similar_styles': {},
            'engine_families': {},
            'performance_clusters': {}
        }
        
        # Group by engine families (based on name patterns)
        families = defaultdict(list)
        for engine in profiles.keys():
            base_name = re.sub(r'[_\s]*v?\d+\.?\d*.*$', '', engine)
            families[base_name].append(engine)
        
        relationships['engine_families'] = dict(families)
        
        # Find style similarities
        style_groups = defaultdict(list)
        for engine, profile in profiles.items():
            if 'playing_style' in profile:
                primary_style = profile['playing_style'].get('primary_style', 'unknown')
                style_groups[primary_style].append(engine)
        
        relationships['similar_styles'] = dict(style_groups)
        
        return relationships

def main():
    """Run the behavioral analysis"""
    analyzer = EngineBehavioralAnalyzer()
    
    # Find all PGN files in results directory
    results_dir = 'results'
    pgn_files = []
    
    for root, dirs, files in os.walk(results_dir):
        for file in files:
            if file.endswith('.pgn'):
                pgn_files.append(os.path.join(root, file))
    
    if not pgn_files:
        print("❌ No PGN files found in results directory")
        return
    
    print(f"🎯 Found {len(pgn_files)} PGN files for analysis")
    
    # Run analysis
    analysis_results = analyzer.analyze_engine_behavior(pgn_files)
    
    # Save results
    output_file = os.path.join(results_dir, 'behavioral_analysis.json')
    with open(output_file, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    print(f"✅ Behavioral analysis complete! Results saved to {output_file}")
    print(f"📊 Analyzed {analysis_results['analysis_metadata']['engines_analyzed']} engines")
    print(f"🎮 Processed {analysis_results['analysis_metadata']['total_games']} games")

if __name__ == "__main__":
    main()
