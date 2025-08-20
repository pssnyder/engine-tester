#!/usr/bin/env python3
"""
Rapid analyzer for Cece v2.0 and v2.2 to identify key patterns and issues.
Focuses on move patterns, piece usage, and strategic problems.
"""
import os
import re
import collections
from pathlib import Path

def analyze_pgn_simple(pgn_file):
    """Simple PGN analysis focusing on move patterns without full chess parsing."""
    results = {
        'v2.0': {'games': 0, 'moves': [], 'first_moves': [], 'piece_moves': collections.Counter()},
        'v2.2': {'games': 0, 'moves': [], 'first_moves': [], 'piece_moves': collections.Counter()}
    }
    
    current_game = None
    current_moves = []
    move_number = 0
    cece_color = None
    
    with open(pgn_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            
            # Check for Cece version in headers
            if line.startswith('[White "') or line.startswith('[Black "'):
                if 'Cece_v2.0' in line or 'Cece v2.0' in line:
                    current_game = 'v2.0'
                    cece_color = 'white' if line.startswith('[White') else 'black'
                elif 'Cece_v2.2' in line or 'Cece v2.2' in line:
                    current_game = 'v2.2'
                    cece_color = 'white' if line.startswith('[White') else 'black'
            
            # Process moves
            elif current_game and line and not line.startswith('[') and not line.startswith('*') and not line.startswith('1-0') and not line.startswith('0-1') and not line.startswith('1/2'):
                # Extract moves from the line
                move_pattern = r'\d+\.\s*([^\s]+)(?:\s+([^\s]+))?'
                moves = re.findall(move_pattern, line)
                
                for white_move, black_move in moves:
                    move_number += 1
                    
                    # Determine if this is Cece's move
                    if cece_color == 'white':
                        cece_move = white_move
                    elif cece_color == 'black' and black_move:
                        cece_move = black_move
                    else:
                        continue
                    
                    if cece_move and not cece_move.startswith('{'):
                        # Clean move notation
                        clean_move = re.sub(r'[+#?!]*$', '', cece_move)
                        current_moves.append(clean_move)
                        
                        # Track first few moves
                        if move_number <= 10:
                            results[current_game]['first_moves'].append(clean_move)
                        
                        # Identify piece type
                        piece = identify_piece(clean_move)
                        results[current_game]['piece_moves'][piece] += 1
            
            # End of game
            elif line.startswith('1-0') or line.startswith('0-1') or line.startswith('1/2'):
                if current_game and current_moves:
                    results[current_game]['games'] += 1
                    results[current_game]['moves'].extend(current_moves)
                
                # Reset for next game
                current_game = None
                current_moves = []
                move_number = 0
                cece_color = None
    
    return results

def identify_piece(move):
    """Identify which piece made the move."""
    if move.startswith('O-O'):
        return 'Castle'
    elif move[0] in 'KQRBN':
        return move[0]
    else:
        return 'Pawn'

def analyze_move_patterns(moves):
    """Analyze common move patterns."""
    move_counter = collections.Counter(moves)
    
    # Count specific problematic patterns
    rook_moves = [m for m in moves if m.startswith('R')]
    king_moves = [m for m in moves if m.startswith('K')]
    knight_moves = [m for m in moves if m.startswith('N')]
    
    # Count early rook moves (problematic)
    early_moves = moves[:20] if len(moves) >= 20 else moves
    early_rook_moves = len([m for m in early_moves if m.startswith('R')])
    early_king_moves = len([m for m in early_moves if m.startswith('K')])
    
    return {
        'most_common': move_counter.most_common(20),
        'rook_move_count': len(rook_moves),
        'king_move_count': len(king_moves),
        'knight_move_count': len(knight_moves),
        'early_rook_moves': early_rook_moves,
        'early_king_moves': early_king_moves,
        'castle_count': len([m for m in moves if 'O-O' in m])
    }

def main():
    results_dir = Path("s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester/results")
    
    # Find all PGN files in Engine Battle directories
    pgn_files = []
    for engine_battle_dir in results_dir.glob("Engine Battle *"):
        if engine_battle_dir.is_dir():
            pgn_files.extend(engine_battle_dir.glob("*.pgn"))
    
    print(f"Found {len(pgn_files)} PGN files to analyze")
    
    # Aggregate results
    aggregate = {
        'v2.0': {'games': 0, 'moves': [], 'first_moves': [], 'piece_moves': collections.Counter()},
        'v2.2': {'games': 0, 'moves': [], 'first_moves': [], 'piece_moves': collections.Counter()}
    }
    
    for pgn_file in pgn_files:
        print(f"Processing {pgn_file.name}...")
        try:
            file_results = analyze_pgn_simple(pgn_file)
            
            for version in ['v2.0', 'v2.2']:
                aggregate[version]['games'] += file_results[version]['games']
                aggregate[version]['moves'].extend(file_results[version]['moves'])
                aggregate[version]['first_moves'].extend(file_results[version]['first_moves'])
                aggregate[version]['piece_moves'].update(file_results[version]['piece_moves'])
        
        except Exception as e:
            print(f"Error processing {pgn_file}: {e}")
            continue
    
    # Analyze and report
    for version in ['v2.0', 'v2.2']:
        data = aggregate[version]
        print(f"\n{'='*50}")
        print(f"CECE {version.upper()} ANALYSIS")
        print(f"{'='*50}")
        print(f"Total games analyzed: {data['games']}")
        print(f"Total moves analyzed: {len(data['moves'])}")
        
        if data['moves']:
            patterns = analyze_move_patterns(data['moves'])
            
            print(f"\nMOST COMMON MOVES:")
            for move, count in patterns['most_common']:
                percentage = (count / len(data['moves'])) * 100
                print(f"  {move}: {count} times ({percentage:.1f}%)")
            
            print(f"\nPIECE MOVEMENT STATISTICS:")
            total_piece_moves = sum(data['piece_moves'].values())
            for piece, count in data['piece_moves'].most_common():
                percentage = (count / total_piece_moves) * 100
                print(f"  {piece}: {count} times ({percentage:.1f}%)")
            
            print(f"\nPROBLEMATIC PATTERNS:")
            print(f"  Early rook moves (first 20): {patterns['early_rook_moves']}")
            print(f"  Early king moves (first 20): {patterns['early_king_moves']}")
            print(f"  Total rook moves: {patterns['rook_move_count']}")
            print(f"  Total king moves: {patterns['king_move_count']}")
            print(f"  Castling occurrences: {patterns['castle_count']}")
            
            # Calculate ratios
            if data['games'] > 0:
                print(f"  Avg rook moves per game: {patterns['rook_move_count'] / data['games']:.1f}")
                print(f"  Avg king moves per game: {patterns['king_move_count'] / data['games']:.1f}")
                print(f"  Castle rate: {patterns['castle_count'] / data['games'] * 100:.1f}%")
            
            print(f"\nMOST COMMON OPENING MOVES:")
            first_move_counter = collections.Counter(data['first_moves'])
            for move, count in first_move_counter.most_common(10):
                percentage = (count / len(data['first_moves'])) * 100 if data['first_moves'] else 0
                print(f"  {move}: {count} times ({percentage:.1f}%)")

if __name__ == "__main__":
    main()