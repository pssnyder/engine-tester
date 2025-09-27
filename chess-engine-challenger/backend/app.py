#!/usr/bin/env python3
"""
Chess Engine Challenger - Flask Backend
Main application for handling web interface and engine communication
"""

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import os
import sys
import chess
import chess.pgn
from datetime import datetime
import json
import uuid

# Add the V7P3R engine path for imports if needed
sys.path.append(r's:\Maker Stuff\Programming\Chess Engines\V7P3R Chess Engine\v7p3r-chess-engine\src')

from engine_manager import EngineManager
from game_controller import GameController
from database import DatabaseManager
from config import Config

app = Flask(__name__, 
           template_folder='../frontend/templates',
           static_folder='../frontend/static')
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize managers
engine_manager = EngineManager()
db_manager = DatabaseManager()
config = Config()

@app.route('/')
def index():
    """Main game interface"""
    available_engines = engine_manager.get_available_engines()
    time_controls = config.TIME_CONTROLS
    return render_template('index.html', 
                         engines=available_engines,
                         time_controls=time_controls)

@app.route('/api/new_game', methods=['POST'])
def new_game():
    """Start a new game with selected engines and time control"""
    try:
        data = request.json
        white_player = data.get('white_player')
        black_player = data.get('black_player')
        time_control = data.get('time_control', '10|5')
        
        # Create new game session
        game_id = str(uuid.uuid4())
        game_controller = GameController(
            game_id=game_id,
            white_player=white_player,
            black_player=black_player,
            time_control=time_control,
            engine_manager=engine_manager,
            db_manager=db_manager
        )
        
        # Store game controller in session (in production, use Redis or similar)
        session[f'game_{game_id}'] = game_controller
        
        return jsonify({
            'success': True,
            'game_id': game_id,
            'board': game_controller.get_board_fen(),
            'white_time': game_controller.get_time_remaining('white'),
            'black_time': game_controller.get_time_remaining('black')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/make_move', methods=['POST'])
def make_move():
    """Handle move submission"""
    try:
        data = request.json
        game_id = data.get('game_id')
        move = data.get('move')
        
        if f'game_{game_id}' not in session:
            return jsonify({'success': False, 'error': 'Game not found'}), 404
            
        game_controller = session[f'game_{game_id}']
        result = game_controller.make_move(move)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/game_status/<game_id>')
def game_status(game_id):
    """Get current game status"""
    try:
        if f'game_{game_id}' not in session:
            return jsonify({'success': False, 'error': 'Game not found'}), 404
            
        game_controller = session[f'game_{game_id}']
        status = game_controller.get_status()
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print('Client connected')
    emit('connected', {'data': 'Connected to Chess Engine Challenger'})

@socketio.on('join_game')
def handle_join_game(data):
    """Join a specific game room for real-time updates"""
    game_id = data['game_id']
    # Join the game room for real-time updates
    # room = f'game_{game_id}'
    # join_room(room)
    emit('joined_game', {'game_id': game_id})

if __name__ == '__main__':
    # Ensure necessary directories exist
    os.makedirs('../game_records', exist_ok=True)
    os.makedirs('../engines', exist_ok=True)
    
    # Initialize database
    db_manager.initialize()
    
    # Start the application
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)
