# chess_core.py
""" 
Enhanced Chess Core for testing, development, and interaction with our engine.
Combines game management, UCI interface control, live search metrics display, and visual GUI components.
"""
import os
import sys
import chess
import chess.pgn
import datetime
import socket
import time
import subprocess
import threading
import pygame
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, Callable
from io import StringIO
import logging

# Import our engine modules
import chess_ai
import interface

# Visual display constants
WIDTH, HEIGHT = 640, 640
DIMENSION = 8
SQ_SIZE = WIDTH // DIMENSION
MAX_FPS = 60
IMAGES = {}

# Board theme colors (black and grey theme)
BOARD_COLORS = [pygame.Color("#2f2f2f"), pygame.Color("#5f5f5f")]  # Dark grey theme
HIGHLIGHT_COLORS = {
    'selected': pygame.Color("#ffff00"),      # Yellow for selected piece
    'last_move': pygame.Color("#ff6b6b"),     # Light red for last move
    'legal_moves': pygame.Color("#4ecdc4"),   # Teal for legal moves
    'check': pygame.Color("#ff4757")          # Red for check
}

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base = getattr(sys, '_MEIPASS', None)
    if base:
        return os.path.join(base, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class ChessCore:
    def __init__(self, logger_name: str = "chess_core", enable_gui: bool = True):
        """Initialize enhanced chess core for engine testing and development"""
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(logger_name)

        # Initialize core chess state
        self.board = chess.Board()
        self.game = chess.pgn.Game()
        self.game_node = self.game
        self.selected_square = None
        self.last_move = chess.Move.null()
        self.move_history = []
        self.game_start_time = 0
        self.game_start_timestamp = ""
        
        # Game state tracking
        self.current_player = self.board.turn
        
        # Engine interaction
        self.engine_process = None
        self.engine_thread = None
        self.search_metrics = {}
        self.last_search_info = {}
        
        # Testing and metrics
        self.position_test_results = []
        self.efficiency_test_data = {}
        
        # Visual components
        self.enable_gui = enable_gui
        self.screen = None
        self.clock = None
        self.display_needs_update = True
        self.flip_board = False
        self.legal_moves_visible = []
        
        if self.enable_gui:
            self._init_pygame()
            self._load_piece_images()
        
        if self.logger:
            self.logger.info("Enhanced ChessCore initialized for engine testing")

    def _init_pygame(self):
        """Initialize pygame for visual display"""
        try:
            pygame.init()
            self.screen = pygame.display.set_mode((WIDTH + 400, HEIGHT))  # Extra space for controls
            pygame.display.set_caption("Chess Engine Testing GUI")
            self.clock = pygame.time.Clock()
            self.display_needs_update = True
        except Exception as e:
            self.logger.error(f"Failed to initialize pygame: {e}")
            self.enable_gui = False

    def _load_piece_images(self):
        """Load chess piece images"""
        if not self.enable_gui:
            return
            
        pieces = ['wp', 'wN', 'wB', 'wR', 'wQ', 'wK',
                 'bp', 'bN', 'bB', 'bR', 'bQ', 'bK']
        
        for piece in pieces:
            try:
                image_path = resource_path(f"images/{piece}.png")
                if os.path.exists(image_path):
                    IMAGES[piece] = pygame.transform.scale(
                        pygame.image.load(image_path),
                        (SQ_SIZE, SQ_SIZE)
                    )
                else:
                    self.logger.warning(f"Image not found: {image_path}")
            except pygame.error as e:
                self.logger.error(f"Could not load image for {piece}: {e}")

    def _piece_image_key(self, piece):
        """Convert chess piece to image key"""
        if piece is None:
            return None
        color = 'w' if piece.color == chess.WHITE else 'b'
        symbol = piece.symbol()
        # Convert to match our image naming: lowercase for pawns, uppercase for others
        if piece.piece_type == chess.PAWN:
            return f"{color}p"
        else:
            return f"{color}{symbol.upper()}"

    # ================================
    # ======== VISUAL METHODS ========
    
    def chess_to_screen(self, square):
        """Convert chess board square to screen coordinates"""
        file = chess.square_file(square)
        rank = chess.square_rank(square)

        if self.flip_board:
            screen_file = 7 - file
            screen_rank = rank
        else:
            screen_file = file
            screen_rank = 7 - rank

        return (screen_file * SQ_SIZE, screen_rank * SQ_SIZE)

    def screen_to_chess(self, pos):
        """Convert screen coordinates to chess square"""
        x, y = pos
        if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
            return None
            
        file = x // SQ_SIZE
        rank = y // SQ_SIZE

        if self.flip_board:
            chess_file = 7 - file
            chess_rank = rank
        else:
            chess_file = file
            chess_rank = 7 - rank

        if 0 <= chess_file <= 7 and 0 <= chess_rank <= 7:
            return chess.square(chess_file, chess_rank)
        return None

    def draw_board(self):
        """Draw the chess board with dark theme"""
        if not self.enable_gui or self.screen is None:
            return
            
        for r in range(DIMENSION):
            for c in range(DIMENSION):
                # Calculate chess square coordinates
                if self.flip_board:
                    file = 7 - c
                    rank = r
                else:
                    file = c
                    rank = 7 - r

                # Determine color based on chess square
                color = BOARD_COLORS[(file + rank) % 2]
                pygame.draw.rect(
                    self.screen,
                    color,
                    pygame.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE)
                )

    def draw_pieces(self):
        """Draw pieces on the board"""
        if not self.enable_gui or self.screen is None:
            return
            
        for r in range(DIMENSION):
            for c in range(DIMENSION):
                # Calculate chess square based on perspective
                if self.flip_board:
                    file = 7 - c
                    rank = r
                else:
                    file = c
                    rank = 7 - r

                square = chess.square(file, rank)
                piece = self.board.piece_at(square)

                if piece:
                    # Calculate screen position
                    screen_x = c * SQ_SIZE
                    screen_y = r * SQ_SIZE

                    piece_key = self._piece_image_key(piece)
                    if piece_key and piece_key in IMAGES:
                        self.screen.blit(IMAGES[piece_key], (screen_x, screen_y))

    def highlight_square(self, square, color_key):
        """Highlight a specific square with the given color"""
        if not self.enable_gui or self.screen is None or square is None:
            return
            
        screen_x, screen_y = self.chess_to_screen(square)
        s = pygame.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(128)
        s.fill(HIGHLIGHT_COLORS[color_key])
        self.screen.blit(s, (screen_x, screen_y))

    def highlight_last_move(self):
        """Highlight the last move on the board"""
        if not self.enable_gui or not self.board.move_stack:
            return
            
        last_move = self.board.move_stack[-1]
        for square in [last_move.from_square, last_move.to_square]:
            self.highlight_square(square, 'last_move')

    def highlight_selected_piece(self):
        """Highlight the currently selected piece"""
        if self.selected_square is not None:
            self.highlight_square(self.selected_square, 'selected')

    def highlight_legal_moves(self):
        """Highlight legal moves for selected piece"""
        if self.selected_square is not None:
            legal_moves = [move for move in self.board.legal_moves 
                          if move.from_square == self.selected_square]
            for move in legal_moves:
                self.highlight_square(move.to_square, 'legal_moves')

    def highlight_check(self):
        """Highlight the king if in check"""
        if self.board.is_check():
            king_square = self.board.king(self.board.turn)
            if king_square is not None:
                self.highlight_square(king_square, 'check')

    def draw_control_panel(self):
        """Draw the control panel on the right side"""
        if not self.enable_gui or self.screen is None:
            return
            
        # Fill control panel area with dark background
        control_area = pygame.Rect(WIDTH, 0, 400, HEIGHT)
        pygame.draw.rect(self.screen, pygame.Color("#1a1a1a"), control_area)
        
        # Draw border
        pygame.draw.rect(self.screen, pygame.Color("#444444"), control_area, 2)
        
        # TODO: Add text rendering for stats and controls
        # This will be implemented with buttons and text display

    def mark_display_dirty(self):
        """Mark the display as needing an update"""
        self.display_needs_update = True

    def update_display(self):
        """Update the visual display"""
        if not self.enable_gui or self.screen is None:
            return
            
        if self.display_needs_update:
            # Clear screen with dark background
            self.screen.fill(pygame.Color("#000000"))
            
            # Draw board and pieces
            self.draw_board()
            self.draw_pieces()
            
            # Draw highlights
            self.highlight_last_move()
            self.highlight_selected_piece()
            self.highlight_legal_moves()
            self.highlight_check()
            
            # Draw control panel
            self.draw_control_panel()
            
            pygame.display.flip()
            self.display_needs_update = False

    def handle_mouse_click(self, pos):
        """Handle mouse clicks on the board"""
        if not self.enable_gui:
            return False
            
        square = self.screen_to_chess(pos)
        if square is None:
            return False
            
        # If no piece selected, select piece on clicked square
        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                self.mark_display_dirty()
                return True
        else:
            # If same square clicked, deselect
            if square == self.selected_square:
                self.selected_square = None
                self.mark_display_dirty()
                return True
            else:
                # Try to make a move
                move = chess.Move(self.selected_square, square)
                
                # Check for promotion
                piece = self.board.piece_at(self.selected_square)
                if (piece and piece.piece_type == chess.PAWN and 
                    chess.square_rank(square) in [0, 7]):
                    move.promotion = chess.QUEEN  # Auto-promote to queen
                
                if move in self.board.legal_moves:
                    success = self.push_move(move)
                    self.selected_square = None
                    self.mark_display_dirty()
                    return success
                else:
                    # Try selecting new piece
                    piece = self.board.piece_at(square)
                    if piece and piece.color == self.board.turn:
                        self.selected_square = square
                        self.mark_display_dirty()
                        return True
                    else:
                        self.selected_square = None
                        self.mark_display_dirty()
                        return False
        
        return False

    def new_game(self, starting_position: str = "default"):
        """Reset the game state for a new game"""
        self.board = chess.Board()
        if starting_position != "default":
            self.board.set_fen(starting_position)
        self.game = chess.pgn.Game()
        self.game_node = self.game
        self.selected_square = None
        self.last_move = chess.Move.null()
        self.current_player = self.board.turn
        self.move_history = []
        self.game_start_time = time.time()
        self.game_start_timestamp = self.get_timestamp()

        # Reset search metrics
        self.search_metrics = {}
        self.last_search_info = {}
        self.position_test_results = []

        # Set default PGN headers
        self.set_headers()
        
        # Mark display for update
        self.mark_display_dirty()
        
        if self.logger:
            self.logger.info(f"New game started with position: {starting_position}")

    def get_timestamp(self) -> str:
        """Return the current timestamp as a string."""
        return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    def set_headers(self, white_player: str = "ChessAI", black_player: str = "Human", event: str = "Engine Test"):
        """Set PGN headers for the game"""
        self.game.headers["Event"] = event
        self.game.headers["White"] = white_player
        self.game.headers["Black"] = black_player
        self.game.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")
        self.game.headers["Site"] = socket.gethostbyname(socket.gethostname())
        self.game.headers["Round"] = "#"

    def display_live_search_info(self, **info):
        """Display live search information during engine thinking"""
        depth = info.get('depth', '?')
        score = info.get('score', '?')
        nodes = info.get('nodes', '?')
        time_ms = info.get('time_ms', '?')
        nps = info.get('nps', '?')
        pv = info.get('pv', [])
        
        # Store for later analysis
        self.last_search_info = info.copy()
        
        # Format and display
        pv_str = ' '.join(pv[:5]) if pv else "..."  # Show first 5 moves of PV
        time_str = f"{time_ms/1000:.3f}s" if isinstance(time_ms, (int, float)) else str(time_ms)
        
        print(f"Depth {depth:2} | Score: {score:6} | Nodes: {nodes:8} | Time: {time_str:8} | NPS: {nps:8} | PV: {pv_str}")
        
        # Log detailed info for efficiency testing
        if depth not in self.search_metrics:
            self.search_metrics[depth] = []
        self.search_metrics[depth].append({
            'nodes': nodes,
            'time_ms': time_ms,
            'score': score,
            'pv_length': len(pv) if pv else 0
        })

    def engine_move(self, depth: int = 3, time_limit: Optional[float] = None) -> Optional[str]:
        """Get a move from our chess_ai engine with live search display"""
        print(f"\n{'='*60}")
        print(f"Engine thinking (depth {depth})...")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        # Use our chess_ai module directly with info callback
        best_move = chess_ai.search(
            board=self.board.copy(),
            depth=depth,
            time_limit=time_limit,
            info_callback=self.display_live_search_info,
            stop_event=None
        )
        
        total_time = time.time() - start_time
        print(f"{'='*60}")
        print(f"Search completed in {total_time:.3f}s - Best move: {best_move}")
        print(f"{'='*60}\n")
        
        return best_move

    def run_efficiency_test(self, test_positions: list, depths: list = [3, 4, 5]):
        """Run efficiency tests on multiple positions to compare search features"""
        print(f"\n{'='*80}")
        print("EFFICIENCY TESTING - Search Feature Analysis")
        print(f"{'='*80}")
        
        self.efficiency_test_data = {}
        
        for pos_name, fen in test_positions:
            print(f"\nTesting position: {pos_name}")
            print(f"FEN: {fen}")
            print("-" * 60)
            
            # Set up position
            self.board.set_fen(fen)
            
            for depth in depths:
                print(f"\nDepth {depth} analysis:")
                
                # Clear metrics for this test
                self.search_metrics = {}
                
                # Run search
                start_time = time.time()
                best_move = chess_ai.search(
                    board=self.board.copy(),
                    depth=depth,
                    time_limit=None,
                    info_callback=self.display_live_search_info,
                    stop_event=None
                )
                total_time = time.time() - start_time
                
                # Store results
                if pos_name not in self.efficiency_test_data:
                    self.efficiency_test_data[pos_name] = {}
                
                final_info = self.last_search_info
                self.efficiency_test_data[pos_name][depth] = {
                    'total_time': total_time,
                    'best_move': best_move,
                    'final_nodes': final_info.get('nodes', 0),
                    'final_score': final_info.get('score', 0),
                    'depth_metrics': self.search_metrics.copy()
                }
                
                print(f"Final: {best_move} | Total nodes: {final_info.get('nodes', 0)} | Time: {total_time:.3f}s")
        
        self.print_efficiency_summary()

    def print_efficiency_summary(self):
        """Print a summary of efficiency test results"""
        print(f"\n{'='*80}")
        print("EFFICIENCY TEST SUMMARY")
        print(f"{'='*80}")
        
        for pos_name, depth_data in self.efficiency_test_data.items():
            print(f"\nPosition: {pos_name}")
            print(f"{'Depth':<6} {'Move':<8} {'Nodes':<10} {'Time(s)':<8} {'NPS':<10} {'Score':<8}")
            print("-" * 60)
            
            for depth, data in sorted(depth_data.items()):
                move = data['best_move'] or 'none'
                nodes = data['final_nodes']
                time_s = data['total_time']
                nps = int(nodes / max(time_s, 0.001))
                score = data['final_score']
                
                print(f"{depth:<6} {move:<8} {nodes:<10} {time_s:<8.3f} {nps:<10} {score:<8}")

    def play_vs_engine(self, engine_depth: int = 3, human_color: chess.Color = chess.WHITE):
        """Interactive play against the engine"""
        print(f"\n{'='*60}")
        print(f"Playing vs ChessAI (depth {engine_depth})")
        print(f"You are {'White' if human_color == chess.WHITE else 'Black'}")
        print(f"{'='*60}")
        
        self.new_game()
        
        while not self.board.is_game_over():
            print(f"\nPosition after move {self.board.fullmove_number}:")
            print(self.board)
            print(f"{'White' if self.board.turn == chess.WHITE else 'Black'} to move")
            
            if self.board.turn == human_color:
                # Human move
                while True:
                    try:
                        move_str = input("Enter your move (e.g., e2e4) or 'quit': ").strip()
                        if move_str.lower() == 'quit':
                            return
                        
                        move = chess.Move.from_uci(move_str)
                        if move in self.board.legal_moves:
                            self.push_move(move)
                            break
                        else:
                            print("Illegal move. Try again.")
                    except ValueError:
                        print("Invalid move format. Use format like 'e2e4'.")
            else:
                # Engine move
                engine_move = self.engine_move(depth=engine_depth)
                if engine_move:
                    move = chess.Move.from_uci(engine_move)
                    self.push_move(move)
                    print(f"Engine plays: {engine_move}")
                else:
                    print("Engine returned no move!")
                    break
        
        print(f"\nGame over! Result: {self.board.result()}")
        self.save_game_pgn(f"games/vs_engine_{self.get_timestamp()}.pgn")

    def get_board_result(self) -> str:
        """Return the result string for the current board state."""
        # Explicitly handle all draw and win/loss cases, fallback to "*"
        if self.board.is_checkmate():
            # The side to move is checkmated, so the other side wins
            return "1-0" if self.board.turn == chess.BLACK else "0-1"
        # Explicit draw conditions
        if (
            self.board.is_stalemate()
            or self.board.is_insufficient_material()
            or self.board.can_claim_fifty_moves()
            or self.board.can_claim_threefold_repetition()
            or self.board.is_seventyfive_moves()
            or self.board.is_fivefold_repetition()
            or self.board.is_variant_draw()
        ):
            return "1/2-1/2"
        # If the game is over but not by checkmate or above draws, fallback to chess.Board.result()
        if self.board.is_game_over():
            result = self.board.result()
            # Defensive: If result is not a valid string, force draw string
            if result not in ("1-0", "0-1", "1/2-1/2"):
                return "1/2-1/2"
            return result
        return "*"

    def handle_game_end(self) -> bool:
        """Check if the game is over and handle end conditions."""
        if self.board.is_game_over():
            # Ensure the result is set in the PGN headers and game node
            result = self.get_board_result()
            self.game.headers["Result"] = result
            self.game_node = self.game.end()
            if self.logger:
                self.logger.info(f"Game ended with result: {result}")
            return True
        return False

    def push_move(self, move) -> bool:
        """Test and push a move to the board and game node"""
        if not self.board.is_valid():
            if self.logger:
                self.logger.error(f"Invalid board state detected! | FEN: {self.board.fen()}")
            return False
        
        if self.logger:
            self.logger.debug(f"Attempting to push move: {move} | FEN: {self.board.fen()}")

        if isinstance(move, str):
            try:
                move = chess.Move.from_uci(move)
                if self.logger:
                    self.logger.debug(f"Converted UCI string to chess.Move: {move}")
            except ValueError:
                if self.logger:
                    self.logger.error(f"Invalid UCI string received: {move}")
                return False
        
        if not self.board.is_legal(move):
            if self.logger:
                self.logger.error(f"Illegal move blocked: {move}")
            return False
        
        try:
            if self.logger:
                self.logger.debug(f"Pushing move: {move} | FEN: {self.board.fen()}")
            
            self.board.push(move)
            self.game_node = self.game_node.add_variation(move)
            self.last_move = move
            self.move_history.append(move)
            
            if self.logger:
                self.logger.debug(f"Move pushed successfully: {move} | FEN: {self.board.fen()}")
            
            self.current_player = self.board.turn
            
            # If the move ends the game, set the result header and end the game node
            if self.board.is_game_over():
                result = self.get_board_result()
                self.game.headers["Result"] = result
                self.game_node = self.game.end()
            else:
                self.game.headers["Result"] = "*"
                
            # Mark display for update
            self.mark_display_dirty()
                
            return True
        except ValueError as e:
            if self.logger:
                self.logger.error(f"ValueError pushing move {move}: {e}")
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f"Exception pushing move {move}: {e}")
            return False

    def import_fen(self, fen_string: str) -> bool:
        """Import a position from FEN notation"""
        try:
            new_board = chess.Board(fen_string)
            
            if not new_board.is_valid():
                if self.logger:
                    self.logger.error(f"Invalid FEN position: {fen_string}")
                return False

            self.board = new_board
            self.game = chess.pgn.Game()
            self.game.setup(new_board)
            self.game_node = self.game            
            self.selected_square = None
            self.game.headers["FEN"] = fen_string

            if self.logger:
                self.logger.info(f"Successfully imported FEN: {fen_string}")
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Unexpected problem importing FEN: {e}")
            return False

    def save_game_pgn(self, filename: str) -> bool:
        """Save PGN to local file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                # Get PGN text
                buf = StringIO()
                exporter = chess.pgn.FileExporter(buf)
                self.game.accept(exporter)
                pgn_content = buf.getvalue()
                f.write(pgn_content)
                f.flush()  # Ensure content is written to disk
            
            if self.logger:
                self.logger.debug(f"PGN saved to {filename}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to save PGN to {filename}: {e}")
            return False

    def get_pgn_text(self) -> str:
        """Get the PGN text for the current game"""
        buf = StringIO()
        exporter = chess.pgn.FileExporter(buf)
        self.game.accept(exporter)
        return buf.getvalue()

    def get_game_info(self) -> dict:
        """Get current game information"""
        return {
            'move_count': len(self.move_history),
            'current_player': 'white' if self.current_player == chess.WHITE else 'black',
            'game_over': self.board.is_game_over(),
            'result': self.get_board_result(),
            'fen': self.board.fen(),
            'game_duration': time.time() - self.game_start_time if self.game_start_time > 0 else 0
        }

    def run_test_suite(self):
        """Run a comprehensive test suite for the engine"""
        print(f"\n{'='*80}")
        print("CHESS ENGINE TEST SUITE")
        print(f"{'='*80}")
        
        # Standard test positions for efficiency testing
        test_positions = [
            ("Starting Position", chess.STARTING_FEN),
            ("Tactical Position", "r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"),
            ("Endgame Position", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"),
            ("Middle Game", "rnbq1rk1/ppp1ppbp/3p1np1/8/2PPP3/2N2N2/PP2BPPP/R1BQKR2 w Q - 0 7")
        ]
        
        # Run efficiency tests
        self.run_efficiency_test(test_positions, depths=[3, 4, 5])
        
        print(f"\n{'='*80}")
        print("Test suite completed!")
        print(f"{'='*80}")


# Simple test runner when called directly
if __name__ == "__main__":
    core = ChessCore()
    
    print("ChessCore Test Interface")
    print("Commands:")
    print("  test - Run efficiency test suite")
    print("  play - Play against engine")
    print("  move <uci> - Make a move")
    print("  fen <fen> - Load position")
    print("  engine <depth> - Get engine move")
    print("  quit - Exit")
    
    while True:
        try:
            cmd = input("\n> ").strip().split()
            if not cmd:
                continue
                
            if cmd[0] == "quit":
                break
            elif cmd[0] == "test":
                core.run_test_suite()
            elif cmd[0] == "play":
                core.play_vs_engine()
            elif cmd[0] == "move" and len(cmd) > 1:
                try:
                    move = chess.Move.from_uci(cmd[1])
                    if core.push_move(move):
                        print(f"Played: {cmd[1]}")
                        print(core.board)
                    else:
                        print("Invalid move")
                except:
                    print("Invalid move format")
            elif cmd[0] == "fen" and len(cmd) > 1:
                fen = " ".join(cmd[1:])
                if core.import_fen(fen):
                    print("Position loaded")
                    print(core.board)
                else:
                    print("Invalid FEN")
            elif cmd[0] == "engine":
                depth = int(cmd[1]) if len(cmd) > 1 else 3
                move = core.engine_move(depth)
                print(f"Engine suggests: {move}")
            else:
                print("Unknown command")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("Goodbye!")

    def get_board_result(self) -> str:
        """Return the result string for the current board state."""
        # Explicitly handle all draw and win/loss cases, fallback to "*"
        if self.board.is_checkmate():
            # The side to move is checkmated, so the other side wins
            return "1-0" if self.board.turn == chess.BLACK else "0-1"
        # Explicit draw conditions
        if (
            self.board.is_stalemate()
            or self.board.is_insufficient_material()
            or self.board.can_claim_fifty_moves()
            or self.board.can_claim_threefold_repetition()
            or self.board.is_seventyfive_moves()
            or self.board.is_fivefold_repetition()
            or self.board.is_variant_draw()
        ):
            return "1/2-1/2"
        # If the game is over but not by checkmate or above draws, fallback to chess.Board.result()
        if self.board.is_game_over():
            result = self.board.result()
            # Defensive: If result is not a valid string, force draw string
            if result not in ("1-0", "0-1", "1/2-1/2"):
                return "1/2-1/2"
            return result
        return "*"

    def handle_game_end(self) -> bool:
        """Check if the game is over and handle end conditions."""
        if self.board.is_game_over():
            # Ensure the result is set in the PGN headers and game node
            result = self.get_board_result()
            self.game.headers["Result"] = result
            self.game_node = self.game.end()
            if self.logger:
                self.logger.info(f"Game ended with result: {result}")
            return True
        return False

    def push_move(self, move) -> bool:
        """Test and push a move to the board and game node"""
        if not self.board.is_valid():
            if self.logger:
                self.logger.error(f"Invalid board state detected! | FEN: {self.board.fen()}")
            return False
        
        if self.logger:
            self.logger.debug(f"Attempting to push move: {move} | FEN: {self.board.fen()}")

        if isinstance(move, str):
            try:
                move = chess.Move.from_uci(move)
                if self.logger:
                    self.logger.debug(f"Converted UCI string to chess.Move: {move}")
            except ValueError:
                if self.logger:
                    self.logger.error(f"Invalid UCI string received: {move}")
                return False
        
        if not self.board.is_legal(move):
            if self.logger:
                self.logger.error(f"Illegal move blocked: {move}")
            return False
        
        try:
            if self.logger:
                self.logger.debug(f"Pushing move: {move} | FEN: {self.board.fen()}")
            
            self.board.push(move)
            self.game_node = self.game_node.add_variation(move)
            self.last_move = move
            self.move_history.append(move)
            
            if self.logger:
                self.logger.debug(f"Move pushed successfully: {move} | FEN: {self.board.fen()}")
            
            self.current_player = self.board.turn
            
            # If the move ends the game, set the result header and end the game node
            if self.board.is_game_over():
                result = self.get_board_result()
                self.game.headers["Result"] = result
                self.game_node = self.game.end()
            else:
                self.game.headers["Result"] = "*"
                
            # Update active_game.pgn after each move for real-time monitoring
            self.quick_save_pgn("active_game.pgn")
            
            return True
        except ValueError as e:
            if self.logger:
                self.logger.error(f"ValueError pushing move {move}: {e}")
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f"Exception pushing move {move}: {e}")
            return False

    def import_fen(self, fen_string: str) -> bool:
        """Import a position from FEN notation"""
        try:
            new_board = chess.Board(fen_string)
            
            if not new_board.is_valid():
                if self.logger:
                    self.logger.error(f"Invalid FEN position: {fen_string}")
                return False

            self.board = new_board
            self.game = chess.pgn.Game()
            self.game.setup(new_board)
            self.game_node = self.game            
            self.selected_square = None
            self.game.headers["FEN"] = fen_string

            if self.logger:
                self.logger.info(f"Successfully imported FEN: {fen_string}")
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Unexpected problem importing FEN: {e}")
            return False

    def quick_save_pgn(self, filename: str) -> bool:
        """Save PGN to local file."""
        try:            
            with open(filename, 'w', encoding='utf-8') as f:
                # Get PGN text
                buf = StringIO()
                exporter = chess.pgn.FileExporter(buf)
                self.game.accept(exporter)
                pgn_content = buf.getvalue()
                f.write(pgn_content)
                f.flush()  # Ensure content is written to disk
            
            if self.logger:
                self.logger.debug(f"PGN saved to {filename}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to save PGN to {filename}: {e}")
            return False

    def quick_save_pgn_to_file(self, filename: str):
        """Quick save the current game to a PGN file"""
        # Inject or update Result header so the PGN shows the game outcome
        if self.board.is_game_over():
            self.game.headers["Result"] = self.get_board_result()
            self.game_node = self.game.end()
        else:
            self.game.headers["Result"] = "*"
        
        with open(filename, "w") as f:
            exporter = chess.pgn.FileExporter(f)
            self.game.accept(exporter)

    def get_pgn_text(self) -> str:
        """Get the PGN text for the current game"""
        buf = StringIO()
        exporter = chess.pgn.FileExporter(buf)
        self.game.accept(exporter)
        return buf.getvalue()

    def save_local_game_files(self, game_id: str, additional_data: Optional[dict] = None) -> bool:
        """Save both PGN and JSON config files locally for metrics processing."""
        try:
            import json
            
            # Ensure games directory exists
            os.makedirs("games", exist_ok=True)
            
            # Save PGN file
            pgn_path = f"games/{game_id}.pgn"
            pgn_text = self.get_pgn_text()
            with open(pgn_path, 'w', encoding='utf-8') as f:
                f.write(pgn_text)
            
            # Save JSON config file for metrics processing
            json_path = f"games/{game_id}.json"
            config_data = {
                'game_id': game_id,
                'timestamp': self.game_start_timestamp,
                'total_moves': len(self.move_history),
                'game_duration': time.time() - self.game_start_time,
                'final_result': self.get_board_result(),
                'final_fen': self.board.fen()
            }
            
            # Add any additional data provided
            if additional_data:
                config_data.update(additional_data)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
            
            if self.logger:
                self.logger.info(f"Saved local files: {pgn_path}, {json_path}")
            return True
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to save local game files for {game_id}: {e}")
            return False

    def _format_time_for_display(self, move_time: float) -> str:
        """
        Format move time for display with appropriate units.
        
        Args:
            move_time: Time in seconds (stored with high precision)
            
        Returns:
            Formatted time string with appropriate units (s or ms)
        """
        if move_time <= 0:
            return "0.000s"
        
        # If time is less than 0.1 seconds (100ms), display in milliseconds
        if move_time < 0.1:
            time_ms = move_time * 1000
            if time_ms < 1.0:
                # For very fast moves (sub-millisecond), show microseconds with higher precision
                return f"{time_ms:.3f}ms"
            else:
                # For sub-100ms moves, show milliseconds with 1 decimal place
                return f"{time_ms:.1f}ms"
        else:
            # For moves 100ms and above, display in seconds
            if move_time < 1.0:
                # Sub-second but >= 100ms: show 3 decimal places
                return f"{move_time:.3f}s"
            elif move_time < 10.0:
                # 1-10 seconds: show 2 decimal places
                return f"{move_time:.2f}s"
            else:
                # 10+ seconds: show 1 decimal place
                return f"{move_time:.1f}s"

    def get_game_info(self) -> dict:
        """Get current game information"""
        return {
            'move_count': len(self.move_history),
            'current_player': 'white' if self.current_player == chess.WHITE else 'black',
            'game_over': self.board.is_game_over(),
            'result': self.get_board_result(),
            'fen': self.board.fen(),
            'game_duration': time.time() - self.game_start_time if self.game_start_time > 0 else 0
        }
