"""
Chess Engine Challenger - Cloud Functions Backend
Cost-optimized Flask API for UCI engine communication

PERFORMANCE TARGETS:
- Cold start: < 3 seconds
- Warm request: < 500ms  
- Engine move: < 5 seconds total
- Memory usage: < 256MB per function

COST OPTIMIZATION:
- Reuse engine processes between requests
- Minimal memory footprint
- Efficient error handling
- Request batching where possible
"""

import os
import json
import time
from typing import Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from firebase_functions import https_fn, options
from firebase_admin import initialize_app, firestore, storage
import chess
import chess.pgn

from uci_engine_handler import UCIEngineManager, EngineConfig
from security_validator import SecurityValidator, RateLimiter

# Initialize Firebase
initialize_app()
db = firestore.client()
storage_client = storage.bucket()

# Initialize Flask app with CORS
app = Flask(__name__)
CORS(app, origins=['*'])  # Adjust for production

# Global instances for request reuse (cost optimization)
engine_manager = None
security_validator = SecurityValidator()
rate_limiter = RateLimiter()

# Cost optimization: Lazy loading
def get_engine_manager():
    """Get or create engine manager (singleton pattern for cost efficiency)"""
    global engine_manager
    if engine_manager is None:
        engine_manager = UCIEngineManager()
    return engine_manager

# Security middleware
@app.before_request
def security_check():
    """Apply security validation to all requests"""
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', 
                                  request.environ.get('REMOTE_ADDR', 'unknown'))
    
    # Rate limiting
    if not rate_limiter.check_rate_limit(client_ip, request.endpoint or 'default'):
        return jsonify({
            'success': False,
            'error': 'Rate limit exceeded. Please wait before making more requests.'
        }), 429
    
    # Store client info for later use
    g.client_ip = client_ip
    g.request_start_time = time.time()

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY' 
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    
    # Log request timing for cost monitoring
    if hasattr(g, 'request_start_time'):
        duration = time.time() - g.request_start_time
        logging.info(f"Request {request.endpoint} took {duration:.3f}s")
    
    return response

@app.route('/api/engines', methods=['GET'])
def get_available_engines():
    """Get list of available engines"""
    try:
        manager = get_engine_manager()
        engines = manager.get_available_engines()
        
        # Add engine metadata from Firestore (cached)
        engine_data = []
        for engine_name in engines:
            try:
                # Try to get cached stats
                stats_ref = db.collection('engine_stats').document(engine_name)
                stats = stats_ref.get()
                
                if stats.exists:
                    data = stats.to_dict()
                    engine_data.append({
                        'name': engine_name,
                        'elo': data.get('elo', 1300),
                        'games_played': data.get('games_played', 0),
                        'last_updated': data.get('last_updated')
                    })
                else:
                    # Default data for new engines
                    engine_data.append({
                        'name': engine_name,
                        'elo': 1300,
                        'games_played': 0,
                        'last_updated': None
                    })
            except Exception as e:
                logging.warning(f"Could not load stats for {engine_name}: {e}")
                engine_data.append({
                    'name': engine_name,
                    'elo': 1300,
                    'games_played': 0,
                    'last_updated': None
                })
        
        return jsonify({
            'success': True,
            'engines': engine_data
        })
        
    except Exception as e:
        logging.error(f"Error getting engines: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load available engines'
        }), 500

@app.route('/api/new_game', methods=['POST'])
def create_new_game():
    """Create a new game session"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate input
        is_valid, error_msg = security_validator.validate_game_creation(data)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        white_player = data['white_player']
        black_player = data['black_player']
        time_control = data['time_control']
        
        # Parse time control
        try:
            base_time, increment = map(int, time_control.split('|'))
            base_time_ms = base_time * 60 * 1000  # Convert to milliseconds
            increment_ms = increment * 1000
        except:
            return jsonify({'success': False, 'error': 'Invalid time control format'}), 400
        
        # Generate game ID and initialize board
        import uuid
        game_id = str(uuid.uuid4())
        board = chess.Board()
        
        # Create game session data
        game_session = {
            'game_id': game_id,
            'white_player': white_player,
            'black_player': black_player,
            'time_control': time_control,
            'base_time_ms': base_time_ms,
            'increment_ms': increment_ms,
            'white_time_left': base_time_ms,
            'black_time_left': base_time_ms,
            'board_fen': board.fen(),
            'move_count': 0,
            'game_status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'moves': [],
            'pgn_moves': []
        }
        
        # Store in Firestore (temporary collection for active games)
        db.collection('active_games').document(game_id).set(game_session)
        
        return jsonify({
            'success': True,
            'game_id': game_id,
            'board_fen': board.fen(),
            'white_time_left': base_time_ms,
            'black_time_left': base_time_ms,
            'to_move': 'white'
        })
        
    except Exception as e:
        logging.error(f"Error creating game: {e}")
        return jsonify({'success': False, 'error': 'Failed to create game'}), 500

@app.route('/api/make_move', methods=['POST'])
def make_move():
    """Process a move in an active game"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate input
        is_valid, error_msg = security_validator.validate_move_input(data)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        game_id = data['game_id']
        move = data['move']
        move_time_ms = data.get('move_time_ms', 0)
        
        # Get game session
        game_ref = db.collection('active_games').document(game_id)
        game_doc = game_ref.get()
        
        if not game_doc.exists:
            return jsonify({'success': False, 'error': 'Game not found'}), 404
        
        game_data = game_doc.to_dict()
        
        # Validate game is still active
        if game_data.get('game_status') != 'active':
            return jsonify({'success': False, 'error': 'Game is not active'}), 400
        
        # Create chess board from current position
        board = chess.Board(game_data['board_fen'])
        
        # Validate and make move
        try:
            chess_move = chess.Move.from_uci(move)
            if chess_move not in board.legal_moves:
                return jsonify({'success': False, 'error': 'Illegal move'}), 400
            
            board.push(chess_move)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Invalid move format: {move}'}), 400
        
        # Update time
        is_white_turn = len(game_data['moves']) % 2 == 0
        if is_white_turn:
            new_white_time = max(0, game_data['white_time_left'] - move_time_ms + game_data['increment_ms'])
            new_black_time = game_data['black_time_left']
        else:
            new_white_time = game_data['white_time_left'] 
            new_black_time = max(0, game_data['black_time_left'] - move_time_ms + game_data['increment_ms'])
        
        # Check for game end conditions
        game_result = None
        if board.is_checkmate():
            game_result = '1-0' if board.turn == chess.BLACK else '0-1'
        elif board.is_stalemate() or board.is_insufficient_material():
            game_result = '1/2-1/2'
        elif new_white_time <= 0:
            game_result = '0-1'  # White loses on time
        elif new_black_time <= 0:
            game_result = '1-0'  # Black loses on time
        
        # Update game data
        updated_moves = game_data['moves'] + [move]
        updated_pgn_moves = game_data['pgn_moves'] + [{
            'move': move,
            'time_ms': move_time_ms,
            'timestamp': datetime.utcnow().isoformat()
        }]
        
        update_data = {
            'board_fen': board.fen(),
            'moves': updated_moves,
            'pgn_moves': updated_pgn_moves,
            'move_count': len(updated_moves),
            'white_time_left': new_white_time,
            'black_time_left': new_black_time,
            'last_move_at': datetime.utcnow().isoformat()
        }
        
        if game_result:
            update_data['game_status'] = 'completed'
            update_data['result'] = game_result
            update_data['completed_at'] = datetime.utcnow().isoformat()
            
            # Save completed game to permanent collection
            completed_game_data = {**game_data, **update_data}
            completed_game_data['pgn'] = generate_pgn(completed_game_data)
            
            db.collection('games').document(game_id).set(completed_game_data)
            
            # Update engine ELO ratings
            update_engine_ratings(completed_game_data)
            
            # Clean up active game
            game_ref.delete()
        else:
            # Update active game
            game_ref.update(update_data)
        
        response_data = {
            'success': True,
            'board_fen': board.fen(),
            'white_time_left': new_white_time,
            'black_time_left': new_black_time,
            'to_move': 'white' if board.turn == chess.WHITE else 'black',
            'move_count': len(updated_moves)
        }
        
        if game_result:
            response_data['game_completed'] = True
            response_data['result'] = game_result
        
        return jsonify(response_data)
        
    except Exception as e:
        logging.error(f"Error making move: {e}")
        return jsonify({'success': False, 'error': 'Failed to process move'}), 500

@app.route('/api/engine_move', methods=['POST'])
def get_engine_move():
    """Get best move from specified engine"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        engine_name = data.get('engine_name')
        fen = data.get('fen')
        time_limit_ms = data.get('time_limit_ms', 1000)
        
        # Validate inputs
        if not engine_name or not fen:
            return jsonify({'success': False, 'error': 'Missing engine_name or fen'}), 400
        
        if not security_validator.validate_fen_position(fen):
            return jsonify({'success': False, 'error': 'Invalid FEN position'}), 400
        
        # Get engine manager and request move
        manager = get_engine_manager()
        result = manager.get_engine_move(
            engine_name=engine_name,
            fen=fen,
            time_limit_ms=min(time_limit_ms, 30000),  # Max 30 seconds
            client_id=g.client_ip
        )
        
        if result is None:
            return jsonify({
                'success': False,
                'error': f'Engine {engine_name} failed to provide a move'
            }), 500
        
        move, evaluation, time_taken = result
        
        return jsonify({
            'success': True,
            'move': move,
            'evaluation': evaluation,
            'time_taken': time_taken,
            'engine': engine_name
        })
        
    except Exception as e:
        logging.error(f"Error getting engine move: {e}")
        return jsonify({'success': False, 'error': 'Engine move failed'}), 500

def generate_pgn(game_data: Dict[str, Any]) -> str:
    """Generate PGN string from game data"""
    try:
        game = chess.pgn.Game()
        
        # Set headers
        game.headers["Event"] = "Chess Engine Challenger"
        game.headers["Site"] = "chess.labs.rapidtechconsultants.com"
        game.headers["Date"] = game_data.get('created_at', '????.??.??')[:10].replace('-', '.')
        game.headers["White"] = game_data['white_player']
        game.headers["Black"] = game_data['black_player'] 
        game.headers["Result"] = game_data.get('result', '*')
        game.headers["TimeControl"] = game_data['time_control']
        
        # Add moves with timing
        board = chess.Board()
        node = game
        
        for i, move_data in enumerate(game_data.get('pgn_moves', [])):
            move = chess.Move.from_uci(move_data['move'])
            node = node.add_variation(move)
            
            # Add timing comment
            time_s = move_data.get('time_ms', 0) / 1000.0
            node.comment = f"{time_s:.1f}s"
            
            board.push(move)
        
        return str(game)
        
    except Exception as e:
        logging.error(f"Error generating PGN: {e}")
        return f"[Error generating PGN: {str(e)}]"

def update_engine_ratings(game_data: Dict[str, Any]) -> None:
    """Update ELO ratings for engines after game completion"""
    try:
        white_player = game_data['white_player']
        black_player = game_data['black_player']
        result = game_data['result']
        
        # Only update for engine vs engine or engine vs human games
        engines = ['V7P3R', 'C0BR4', 'SlowMate']
        
        if white_player in engines or black_player in engines:
            # Calculate ELO changes (simplified K=32 system)
            white_score = 1 if result == '1-0' else (0.5 if result == '1/2-1/2' else 0)
            black_score = 1 - white_score
            
            # Update ratings in batch
            batch = db.batch()
            
            for player, score in [(white_player, white_score), (black_player, black_score)]:
                if player in engines:
                    stats_ref = db.collection('engine_stats').document(player)
                    stats_doc = stats_ref.get()
                    
                    if stats_doc.exists:
                        current_stats = stats_doc.to_dict()
                        current_elo = current_stats.get('elo', 1300)
                        games_played = current_stats.get('games_played', 0)
                    else:
                        current_elo = 1300
                        games_played = 0
                    
                    # Simple ELO calculation (assumes opponent rating of 1300 for humans)
                    opponent_elo = 1300  # Default for humans
                    if (player == white_player and black_player in engines) or \
                       (player == black_player and white_player in engines):
                        # Engine vs engine - get opponent rating
                        opponent = black_player if player == white_player else white_player
                        opponent_stats = db.collection('engine_stats').document(opponent).get()
                        if opponent_stats.exists:
                            opponent_elo = opponent_stats.to_dict().get('elo', 1300)
                    
                    # Calculate new ELO
                    expected_score = 1 / (1 + 10 ** ((opponent_elo - current_elo) / 400))
                    k_factor = 32
                    new_elo = current_elo + k_factor * (score - expected_score)
                    
                    # Update stats
                    new_stats = {
                        'elo': round(new_elo),
                        'games_played': games_played + 1,
                        'last_updated': datetime.utcnow().isoformat(),
                        'wins': current_stats.get('wins', 0) + (1 if score == 1 else 0),
                        'draws': current_stats.get('draws', 0) + (1 if score == 0.5 else 0),
                        'losses': current_stats.get('losses', 0) + (1 if score == 0 else 0)
                    }
                    
                    batch.set(stats_ref, new_stats, merge=True)
            
            batch.commit()
            
    except Exception as e:
        logging.error(f"Error updating engine ratings: {e}")

# Export the Flask app as a Cloud Function
@https_fn.on_request(
    cors=options.CorsOptions(
        cors_origins=['*'],
        cors_methods=['GET', 'POST', 'OPTIONS']
    ),
    memory=options.MemoryOption.MB_256,
    timeout_sec=60
)
def api(req: https_fn.Request) -> https_fn.Response:
    """Main Cloud Function entry point"""
    with app.request_context(req.environ):
        return app.full_dispatch_request()
