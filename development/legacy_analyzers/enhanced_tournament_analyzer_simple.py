#!/usr/bin/env python3
"""
Enhanced Tournament Analyzer with Deep Game Analysis - Simplified Version

This analyzer processes all tournament results and generates comprehensive statistics
including win/loss categorization, blunder analysis, and personality classification.
"""

import json
import os
import re
import chess
import chess.pgn
from io import StringIO
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import glob

class EnhancedTournamentAnalyzer:
    def __init__(self, results_dir: str = "results", dashboard_data_dir: str = "analytics_and_dashboard/dashboard/data"):
        self.results_dir = results_dir
        self.dashboard_data_dir = dashboard_data_dir
        self.name_consolidation = self.load_name_consolidation()
        
        # Initialize analysis containers
        self.games_data = []
        self.engine_stats = {}
        
        # Game termination categorizations
        self.win_loss_categories = {
            # Decisive wins/losses
            'mate': ['checkmate', 'mate', 'mated'],
            'resignation': ['resign', 'resignation', 'resigns'],
            'time': ['time', 'timeout', 'forfeit'],
            'material': ['material', 'insufficient'],
            
            # Draws
            'stalemate': ['stalemate'],
            'repetition': ['repetition', 'threefold'],
            'fifty_move': ['fifty', '50'],
            'agreement': ['agreement', 'draw'],
            
            # Technical issues
            'adjudication': ['adjudication', 'adjudicated'],
            'illegal': ['illegal', 'invalid'],
            'error': ['error', 'crash', 'exception']
        }

    def load_name_consolidation(self) -> Dict:
        """Load the name consolidation mapping"""
        consolidation_path = os.path.join(self.dashboard_data_dir, "name_consolidation.json")
        if os.path.exists(consolidation_path):
            with open(consolidation_path, 'r') as f:
                data = json.load(f)
                return data.get("name_consolidation", {}).get("consolidations", {})
        return {}

    def init_engine_stats(self, engine_name: str) -> Dict:
        """Initialize stats structure for an engine"""
        return {
            'wins': 0, 'losses': 0, 'draws': 0,
            'total_games': 0, 'total_moves': 0,
            'win_types': {},
            'loss_types': {},
            'blunders': 0, 'blunder_games': 0,
            'time_losses': 0, 'material_losses': 0,
            'mate_wins': 0, 'mate_losses': 0,
            'average_game_length': 0.0,
            'personality_traits': {}
        }

    def consolidate_engine_name(self, engine_name: str) -> Tuple[str, bool]:
        """
        Consolidate engine name and return whether to include in metrics
        Returns: (consolidated_name, include_in_metrics)
        """
        if not engine_name:
            return "Unknown", False
            
        # Check direct matches first
        for consolidated_name, config in self.name_consolidation.items():
            if isinstance(config, dict) and 'variants' in config:
                if engine_name in config['variants']:
                    return consolidated_name, config.get('include_in_metrics', True)
            elif isinstance(config, list):  # Legacy format
                if engine_name in config:
                    return consolidated_name, True
        
        # If no match found, return original name
        return engine_name, True

    def categorize_game_result(self, result_reason: str, result: str) -> Tuple[str, str]:
        """
        Categorize how a game ended
        Returns: (category, subcategory)
        """
        if not result_reason:
            result_reason = ""
        
        reason_lower = result_reason.lower()
        
        # Check each category
        for category, keywords in self.win_loss_categories.items():
            if any(keyword in reason_lower for keyword in keywords):
                if result == "1-0":
                    return f"white_{category}", category
                elif result == "0-1":
                    return f"black_{category}", category
                else:  # Draw
                    return f"draw_{category}", category
        
        # Default categorization based on result
        if result == "1-0":
            return "white_other", "other"
        elif result == "0-1":
            return "black_other", "other"
        else:
            return "draw_other", "other"

    def analyze_blunders(self, pgn_content: str) -> Dict[str, Any]:
        """
        Analyze blunders in a game based on material swings
        """
        blunder_data = {
            'total_blunders': 0,
            'white_blunders': 0,
            'black_blunders': 0,
            'blunder_moves': [],
            'material_swings': []
        }
        
        try:
            game = chess.pgn.read_game(StringIO(pgn_content))
            if not game:
                return blunder_data
                
            board = game.board()
            previous_material = self.calculate_material_value(board)
            move_number = 1
            
            for move in game.mainline_moves():
                board.push(move)
                current_material = self.calculate_material_value(board)
                
                # Calculate material swing
                material_change = current_material - previous_material
                
                # Detect blunders (sudden material loss > 3 points without compensation)
                if abs(material_change) >= 300:  # 3 points in centipawns
                    is_white_move = move_number % 2 == 1
                    
                    # Check if this is a blunder (loss without compensation)
                    if (is_white_move and material_change < -300) or \
                       (not is_white_move and material_change > 300):
                        blunder_data['total_blunders'] += 1
                        if is_white_move:
                            blunder_data['white_blunders'] += 1
                        else:
                            blunder_data['black_blunders'] += 1
                        
                        blunder_data['blunder_moves'].append({
                            'move_number': move_number,
                            'move': move.uci(),
                            'material_loss': abs(material_change),
                            'player': 'white' if is_white_move else 'black'
                        })
                
                blunder_data['material_swings'].append({
                    'move_number': move_number,
                    'material_change': material_change,
                    'total_material': current_material
                })
                
                previous_material = current_material
                move_number += 1
                
        except Exception as e:
            print(f"Error analyzing blunders: {e}")
            
        return blunder_data

    def calculate_material_value(self, board: chess.Board) -> int:
        """Calculate total material value in centipawns"""
        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 0
        }
        
        total = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = piece_values[piece.piece_type]
                if piece.color == chess.WHITE:
                    total += value
                else:
                    total -= value
        
        return total

    def analyze_personality_traits(self, game_data: Dict, engine_name: str) -> Dict[str, int]:
        """
        Analyze personality traits based on game behavior
        """
        traits = {}
        
        # Get game info
        result = game_data.get('result', '')
        result_reason = game_data.get('result_reason', '').lower()
        game_length = game_data.get('move_count', 0)
        blunder_data = game_data.get('blunder_analysis', {})
        
        # Determine if this engine won, lost, or drew
        if engine_name == game_data.get('white_player'):
            won = result == "1-0"
            lost = result == "0-1"
        else:
            won = result == "0-1"
            lost = result == "1-0"
        
        # Personality trait analysis
        if 'time' in result_reason:
            traits['slow'] = traits.get('slow', 0) + 1
        
        if 'mate' in result_reason:
            if won:
                traits['decisive'] = traits.get('decisive', 0) + 1
            else:
                traits['gullible'] = traits.get('gullible', 0) + 1
        
        if 'material' in result_reason or 'resign' in result_reason:
            if lost:
                traits['shallow'] = traits.get('shallow', 0) + 1
        
        if 'adjudication' in result_reason or 'illegal' in result_reason or 'error' in result_reason:
            traits['volatile'] = traits.get('volatile', 0) + 1
        
        if result == "1/2-1/2":
            traits['drawish'] = traits.get('drawish', 0) + 1
        
        if game_length > 100:
            traits['conservative'] = traits.get('conservative', 0) + 1
        elif game_length < 30:
            traits['aggressive'] = traits.get('aggressive', 0) + 1
        
        # Blunder-based traits
        total_blunders = blunder_data.get('total_blunders', 0)
        if total_blunders > 2:
            traits['blunderous'] = traits.get('blunderous', 0) + 1
        elif total_blunders == 0:
            traits['solid'] = traits.get('solid', 0) + 1
        
        return traits

    def process_tournament_directory(self, tournament_dir: str) -> List[Dict]:
        """Process all PGN files in a tournament directory"""
        games = []
        pgn_files = glob.glob(os.path.join(tournament_dir, "*.pgn"))
        
        print(f"Processing {len(pgn_files)} PGN files in {tournament_dir}")
        
        for pgn_file in pgn_files:
            try:
                with open(pgn_file, 'r', encoding='utf-8') as f:
                    pgn_content = f.read()
                
                # Parse multiple games in the file
                game_strings = pgn_content.strip().split('\n\n[Event')
                for i, game_str in enumerate(game_strings):
                    if i > 0:  # Add back the [Event header
                        game_str = '[Event' + game_str
                    
                    if game_str.strip():
                        game_data = self.parse_pgn_game(game_str)
                        if game_data:
                            # Add blunder analysis
                            game_data['blunder_analysis'] = self.analyze_blunders(game_str)
                            games.append(game_data)
                            
            except Exception as e:
                print(f"Error processing {pgn_file}: {e}")
        
        return games

    def parse_pgn_game(self, pgn_content: str) -> Optional[Dict]:
        """Parse a single PGN game and extract metadata"""
        try:
            game = chess.pgn.read_game(StringIO(pgn_content))
            if not game:
                return None
            
            # Extract headers
            headers = dict(game.headers)
            
            # Count moves
            move_count = 0
            for _ in game.mainline_moves():
                move_count += 1
            
            # Extract players
            white_player = headers.get('White', 'Unknown')
            black_player = headers.get('Black', 'Unknown')
            
            # Consolidate names
            white_consolidated, white_include = self.consolidate_engine_name(white_player)
            black_consolidated, black_include = self.consolidate_engine_name(black_player)
            
            # Get result and categorize
            result = headers.get('Result', '*')
            result_reason = headers.get('Termination', '')
            category, subcategory = self.categorize_game_result(result_reason, result)
            
            game_data = {
                'white_player': white_player,
                'black_player': black_player,
                'white_consolidated': white_consolidated,
                'black_consolidated': black_consolidated,
                'white_include_metrics': white_include,
                'black_include_metrics': black_include,
                'result': result,
                'result_reason': result_reason,
                'result_category': category,
                'result_subcategory': subcategory,
                'move_count': move_count,
                'date': headers.get('Date', ''),
                'event': headers.get('Event', ''),
                'round': headers.get('Round', ''),
                'fen': headers.get('FEN', ''),
                'headers': headers
            }
            
            return game_data
            
        except Exception as e:
            print(f"Error parsing PGN game: {e}")
            return None

    def update_engine_statistics(self, game_data: Dict):
        """Update statistics for engines in this game"""
        white_engine = game_data['white_consolidated']
        black_engine = game_data['black_consolidated']
        result = game_data['result']
        category = game_data['result_category']
        subcategory = game_data['result_subcategory']
        move_count = game_data['move_count']
        blunder_data = game_data['blunder_analysis']
        
        # Only include in metrics if flagged
        engines_to_update = []
        if game_data['white_include_metrics']:
            engines_to_update.append(('white', white_engine))
        if game_data['black_include_metrics']:
            engines_to_update.append(('black', black_engine))
        
        for color, engine in engines_to_update:
            if engine not in self.engine_stats:
                self.engine_stats[engine] = self.init_engine_stats(engine)
            
            stats = self.engine_stats[engine]
            stats['total_games'] += 1
            stats['total_moves'] += move_count
            
            # Update win/loss/draw counts
            if result == "1-0":
                if color == 'white':
                    stats['wins'] += 1
                    stats['win_types'][subcategory] = stats['win_types'].get(subcategory, 0) + 1
                else:
                    stats['losses'] += 1
                    stats['loss_types'][subcategory] = stats['loss_types'].get(subcategory, 0) + 1
            elif result == "0-1":
                if color == 'black':
                    stats['wins'] += 1
                    stats['win_types'][subcategory] = stats['win_types'].get(subcategory, 0) + 1
                else:
                    stats['losses'] += 1
                    stats['loss_types'][subcategory] = stats['loss_types'].get(subcategory, 0) + 1
            else:
                stats['draws'] += 1
            
            # Update blunder statistics
            if color == 'white':
                stats['blunders'] += blunder_data.get('white_blunders', 0)
            else:
                stats['blunders'] += blunder_data.get('black_blunders', 0)
            
            if blunder_data.get('total_blunders', 0) > 0:
                stats['blunder_games'] += 1
            
            # Update specific loss/win types for personality analysis
            if 'time' in subcategory:
                if (result == "1-0" and color == 'black') or (result == "0-1" and color == 'white'):
                    stats['time_losses'] += 1
            
            if 'material' in subcategory or 'resignation' in subcategory:
                if (result == "1-0" and color == 'black') or (result == "0-1" and color == 'white'):
                    stats['material_losses'] += 1
            
            if 'mate' in subcategory:
                if (result == "1-0" and color == 'white') or (result == "0-1" and color == 'black'):
                    stats['mate_wins'] += 1
                else:
                    stats['mate_losses'] += 1
            
            # Update personality traits
            traits = self.analyze_personality_traits(game_data, engine)
            for trait, count in traits.items():
                stats['personality_traits'][trait] = stats['personality_traits'].get(trait, 0) + count

    def calculate_derived_statistics(self):
        """Calculate derived statistics for all engines"""
        for engine, stats in self.engine_stats.items():
            total_games = stats['total_games']
            if total_games > 0:
                # Calculate percentages
                stats['win_rate'] = stats['wins'] / total_games
                stats['loss_rate'] = stats['losses'] / total_games
                stats['draw_rate'] = stats['draws'] / total_games
                
                # Calculate average game length
                stats['average_game_length'] = stats['total_moves'] / total_games
                
                # Calculate blunder rate
                if stats['total_moves'] > 0:
                    stats['blunder_rate'] = stats['blunders'] / (stats['total_moves'] / 2)  # Per move
                else:
                    stats['blunder_rate'] = 0
                
                # Calculate personality percentages
                stats['personality_percentages'] = {}
                for trait, count in stats['personality_traits'].items():
                    stats['personality_percentages'][trait] = count / total_games
                
                # Determine dominant personality traits
                traits = stats['personality_percentages']
                stats['dominant_traits'] = sorted(traits.items(), key=lambda x: x[1], reverse=True)[:3]

    def generate_summary_statistics(self) -> Dict:
        """Generate overall summary statistics"""
        total_games = len(self.games_data)
        total_engines = len(self.engine_stats)
        
        # Calculate date range
        dates = [game['date'] for game in self.games_data if game['date']]
        date_range = {
            'earliest': min(dates) if dates else '',
            'latest': max(dates) if dates else ''
        }
        
        # Calculate overall statistics
        total_blunders = sum(game['blunder_analysis']['total_blunders'] for game in self.games_data)
        total_moves = sum(game['move_count'] for game in self.games_data)
        
        # Result distribution
        results = {'1-0': 0, '0-1': 0, '1/2-1/2': 0}
        for game in self.games_data:
            result = game['result']
            if result in results:
                results[result] += 1
        
        # Category distribution
        categories = {}
        for game in self.games_data:
            subcategory = game['result_subcategory']
            categories[subcategory] = categories.get(subcategory, 0) + 1
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_games': total_games,
            'total_engines': total_engines,
            'date_range': date_range,
            'total_blunders': total_blunders,
            'total_moves': total_moves,
            'blunder_rate_overall': total_blunders / (total_moves / 2) if total_moves > 0 else 0,
            'result_distribution': results,
            'category_distribution': categories,
            'engines_included_in_metrics': len([e for e, s in self.engine_stats.items() if s['total_games'] > 0])
        }

    def run_analysis(self):
        """Run the complete analysis"""
        print("Starting enhanced tournament analysis...")
        
        # Find all tournament directories
        tournament_dirs = []
        for item in os.listdir(self.results_dir):
            item_path = os.path.join(self.results_dir, item)
            if os.path.isdir(item_path):
                tournament_dirs.append(item_path)
        
        print(f"Found {len(tournament_dirs)} tournament directories")
        
        # Process each tournament
        for tournament_dir in tournament_dirs:
            print(f"Processing {tournament_dir}...")
            games = self.process_tournament_directory(tournament_dir)
            self.games_data.extend(games)
            
            # Update statistics for each game
            for game in games:
                self.update_engine_statistics(game)
        
        print(f"Processed {len(self.games_data)} total games")
        
        # Calculate derived statistics
        self.calculate_derived_statistics()
        
        # Generate outputs
        self.save_analysis_results()

    def save_analysis_results(self):
        """Save all analysis results to dashboard data directory"""
        # Ensure output directory exists
        os.makedirs(self.dashboard_data_dir, exist_ok=True)
        
        # Save enhanced engine statistics
        with open(os.path.join(self.dashboard_data_dir, 'enhanced_engine_stats.json'), 'w') as f:
            json.dump(self.engine_stats, f, indent=2)
        
        # Save game results with enhanced data
        with open(os.path.join(self.dashboard_data_dir, 'enhanced_game_results.json'), 'w') as f:
            json.dump(self.games_data, f, indent=2)
        
        # Save summary statistics
        summary = self.generate_summary_statistics()
        with open(os.path.join(self.dashboard_data_dir, 'enhanced_analysis_summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Generate personality analysis
        personality_analysis = self.generate_personality_analysis()
        with open(os.path.join(self.dashboard_data_dir, 'personality_analysis.json'), 'w') as f:
            json.dump(personality_analysis, f, indent=2)
        
        print(f"Analysis results saved to {self.dashboard_data_dir}")

    def generate_personality_analysis(self) -> Dict:
        """Generate detailed personality analysis for engines"""
        personality_data = {}
        
        for engine, stats in self.engine_stats.items():
            if stats['total_games'] < 5:  # Skip engines with insufficient data
                continue
            
            traits = stats.get('personality_percentages', {})
            dominant = stats.get('dominant_traits', [])
            
            # Classify engine personality
            personality_type = self.classify_personality(traits, stats)
            
            personality_data[engine] = {
                'personality_type': personality_type,
                'dominant_traits': dominant,
                'trait_percentages': traits,
                'statistics': {
                    'games_played': stats['total_games'],
                    'win_rate': stats.get('win_rate', 0),
                    'draw_rate': stats.get('draw_rate', 0),
                    'blunder_rate': stats.get('blunder_rate', 0),
                    'average_game_length': stats.get('average_game_length', 0),
                    'mate_win_rate': stats['mate_wins'] / max(stats['wins'], 1),
                    'time_loss_rate': stats['time_losses'] / max(stats['losses'], 1)
                }
            }
        
        return personality_data

    def classify_personality(self, traits: Dict[str, float], stats: Dict) -> str:
        """Classify engine personality based on dominant traits"""
        if not traits:
            return "Unknown"
        
        # Get the most dominant traits
        sorted_traits = sorted(traits.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_traits:
            return "Balanced"
        
        primary_trait = sorted_traits[0][0]
        primary_value = sorted_traits[0][1]
        
        # Classification logic
        if primary_value > 0.3:  # Strong dominance
            if primary_trait == 'decisive':
                return "Aggressive Attacker"
            elif primary_trait == 'solid':
                return "Solid Defender"
            elif primary_trait == 'drawish':
                return "Cautious Player"
            elif primary_trait == 'slow':
                return "Time Trouble Prone"
            elif primary_trait == 'blunderous':
                return "Error Prone"
            elif primary_trait == 'conservative':
                return "Conservative Player"
            elif primary_trait == 'gullible':
                return "Tactically Weak"
            elif primary_trait == 'shallow':
                return "Positionally Weak"
            elif primary_trait == 'volatile':
                return "Unstable Engine"
        
        # Look at secondary characteristics
        if len(sorted_traits) > 1:
            secondary_trait = sorted_traits[1][0]
            if primary_trait == 'decisive' and secondary_trait == 'solid':
                return "Balanced Attacker"
            elif primary_trait == 'solid' and secondary_trait == 'drawish':
                return "Ultra Solid"
            elif primary_trait == 'conservative' and secondary_trait == 'drawish':
                return "Defensive Specialist"
        
        return "Balanced Player"


def main():
    """Main entry point"""
    analyzer = EnhancedTournamentAnalyzer()
    analyzer.run_analysis()
    print("Enhanced analysis complete!")

if __name__ == "__main__":
    main()
