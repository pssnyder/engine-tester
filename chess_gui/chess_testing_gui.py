#!/usr/bin/env python3
"""
Universal Chess Engine Testing GUI

A comprehensive testing interface that provides:
1. Universal engine support (UCI + direct Python access)
2. Real-time move and evaluation logging
3. Session-based testing with comprehensive data export
4. Visual chess board with highlighting and interaction
5. Performance analysis and metrics collection

This GUI uses an abstraction layer to work with any chess engine while
providing enhanced functionality for engines with direct Python access.
"""

import pygame
import chess
import threading
import time
import json
import os
from typing import Optional, Dict, Any, List
from engine_interface import EngineManager, create_engine_interface
from test_session_logger import TestSessionLogger
from chess_core import ChessCore

# Initialize pygame
pygame.init()

# Display constants
BOARD_WIDTH = 640
CONTROL_PANEL_WIDTH = 400
TOTAL_WIDTH = BOARD_WIDTH + CONTROL_PANEL_WIDTH
WINDOW_HEIGHT = 640
FPS = 60

# Colors
DARK_BG = pygame.Color("#1a1a1a")
LIGHT_BG = pygame.Color("#2a2a2a")
TEXT_COLOR = pygame.Color("#ffffff")
BUTTON_COLOR = pygame.Color("#4a4a4a")
BUTTON_HOVER_COLOR = pygame.Color("#6a6a6a")
ACTIVE_COLOR = pygame.Color("#4ecdc4")

class SearchTestConfig:
    """Configuration for search efficiency tests"""
    def __init__(self):
        self.test_positions = [
            ("Starting Position", chess.STARTING_FEN),
            ("Tactical Puzzle", "r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"),
            ("Endgame Position", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"),
            ("Middle Game", "rnbq1rk1/ppp1ppbp/3p1np1/8/2PPP3/2N2N2/PP2BPPP/R1BQK2R w Q - 0 7"),
            ("Mate in 2", "2bqkbn1/2pppp2/np2N3/r3P1p1/p2N4/5Q2/PPPPKPP1/RNB2B1R w KQkq - 0 1")
        ]
        self.test_depths = [3, 4, 5]
        self.search_variations = [
            ("Base Search", "base"),
            ("Alpha-Beta", "alpha_beta"),
            ("Full (AB + Move Ordering)", "full")
        ]

class Button:
    """Simple button class for the GUI"""
    def __init__(self, x, y, width, height, text, font, callback=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.callback = callback
        self.hovered = False
        self.enabled = True
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos) and self.enabled and self.callback:
                self.callback()
                
    def draw(self, screen):
        color = BUTTON_HOVER_COLOR if self.hovered else BUTTON_COLOR
        if not self.enabled:
            color = pygame.Color("#2a2a2a")
            
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, TEXT_COLOR, self.rect, 2)
        
        text_surface = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

class ChessEngineTestingGUI:
    """Universal chess engine testing GUI"""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((TOTAL_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Universal Chess Engine Testing Suite")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Initialize chess core without GUI (we handle display)
        self.chess_core = ChessCore(enable_gui=False)
        
        # Initialize engine manager and session logger
        self.engine_manager = EngineManager()
        self.session_logger = TestSessionLogger()
        
        # Initialize fonts
        self.font_small = pygame.font.Font(None, 18)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 32)
        
        # Load piece images
        self.piece_images = {}
        self._load_piece_images()
        
        # Test configuration
        self.test_config = SearchTestConfig()
        self.current_test_position = 0
        self.current_test_depth = 0
        
        # Test state
        self.testing_active = False
        self.auto_eval_enabled = True  # Auto-evaluate positions after moves
        
        # GUI state
        self.selected_square = None
        self.flip_board = False
        self.last_evaluation = {}
        
        # Setup engines
        self._setup_engines()
        
        # Create buttons
        self.create_buttons()
        
        print("Universal Chess Engine Testing GUI initialized")
        print(f"Available engines: {', '.join(self.engine_manager.list_engines())}")
        
    def _setup_engines(self):
        """Setup available engines"""
        # Add chess-ai engine (direct Python access)
        chess_ai_engine = create_engine_interface("chess-ai")
        if chess_ai_engine:
            self.engine_manager.add_engine(chess_ai_engine)
            self.session_logger.add_note("chess-ai engine loaded with direct Python access")
        
        # Could add UCI engines here in the future:
        # stockfish_engine = create_engine_interface("uci", name="Stockfish", path="stockfish.exe")
        # self.engine_manager.add_engine(stockfish_engine)
        
    def _load_piece_images(self):
        """Load chess piece images"""
        pieces = ['wp', 'wN', 'wB', 'wR', 'wQ', 'wK',
                 'bp', 'bN', 'bB', 'bR', 'bQ', 'bK']
        
        sq_size = BOARD_WIDTH // 8
        
        for piece in pieces:
            try:
                image_path = f"images/{piece}.png"
                if os.path.exists(image_path):
                    self.piece_images[piece] = pygame.transform.scale(
                        pygame.image.load(image_path),
                        (sq_size, sq_size)
                    )
                else:
                    print(f"Warning: Image not found: {image_path}")
            except pygame.error as e:
                print(f"Could not load image for {piece}: {e}")
        
    def create_buttons(self):
        """Create control buttons"""
        button_width = 180
        button_height = 30
        start_x = BOARD_WIDTH + 20
        start_y = 50
        spacing = 40
        
        self.buttons = []
        
        # Engine control buttons
        self.buttons.append(Button(start_x, start_y, button_width, button_height, 
                                 "Engine Move", self.font_medium, self.make_engine_move))
        
        self.buttons.append(Button(start_x, start_y + spacing, button_width, button_height, 
                                 "Evaluate Position", self.font_medium, self.evaluate_current_position))
        
        self.buttons.append(Button(start_x, start_y + spacing * 2, button_width, button_height, 
                                 "Load Test Position", self.font_medium, self.cycle_test_position))
        
        self.buttons.append(Button(start_x, start_y + spacing * 3, button_width, button_height, 
                                 "Reset to Start", self.font_medium, self.reset_to_start))
        
        self.buttons.append(Button(start_x, start_y + spacing * 4, button_width, button_height, 
                                 "Flip Board", self.font_medium, self.flip_board_view))
        
        # Test control buttons  
        self.buttons.append(Button(start_x, start_y + spacing * 6, button_width, button_height, 
                                 "Run Test Suite", self.font_medium, self.run_test_suite))
        
        self.buttons.append(Button(start_x, start_y + spacing * 7, button_width, button_height, 
                                 "Toggle Auto-Eval", self.font_medium, self.toggle_auto_eval))
        
        # Session management
        self.buttons.append(Button(start_x, start_y + spacing * 9, button_width, button_height, 
                                 "Export Session", self.font_medium, self.export_session))
        
        self.buttons.append(Button(start_x, start_y + spacing * 10, button_width, button_height, 
                                 "New Session", self.font_medium, self.start_new_session))
    
    def cycle_test_position(self):
        """Cycle through test positions"""
        self.current_test_position = (self.current_test_position + 1) % len(self.test_config.test_positions)
        position_name, fen = self.test_config.test_positions[self.current_test_position]
        self.chess_core.import_fen(fen)
        self.session_logger.add_note(f"Loaded test position: {position_name}")
        
        # Auto-evaluate new position
        if self.auto_eval_enabled:
            threading.Thread(target=self._auto_evaluate_position, daemon=True).start()
        
        print(f"Loaded test position: {position_name}")
    
    def reset_to_start(self):
        """Reset to starting position"""
        self.chess_core.new_game()
        self.selected_square = None
        self.session_logger.add_note("Reset to starting position")
        
        # Auto-evaluate starting position
        if self.auto_eval_enabled:
            threading.Thread(target=self._auto_evaluate_position, daemon=True).start()
        
    def flip_board_view(self):
        """Flip the board view"""
        self.flip_board = not self.flip_board
        
    def toggle_auto_eval(self):
        """Toggle automatic position evaluation"""
        self.auto_eval_enabled = not self.auto_eval_enabled
        status = "enabled" if self.auto_eval_enabled else "disabled"
        self.session_logger.add_note(f"Auto-evaluation {status}")
        print(f"Auto-evaluation {status}")
        
    def start_new_session(self):
        """Start a new test session"""
        # Export current session first if it has data
        if self.session_logger.moves or self.session_logger.evaluations:
            self.export_session()
        
        # Start new session
        self.session_logger = TestSessionLogger()
        self.reset_to_start()
        print("Started new test session")
    
    def make_engine_move(self):
        """Make a single engine move"""
        if not self.testing_active:
            threading.Thread(target=self._engine_move_worker, daemon=True).start()
    
    def _engine_move_worker(self):
        """Worker thread for engine moves"""
        self.testing_active = True
        try:
            current_engine = self.engine_manager.get_current_engine()
            if not current_engine:
                print("No engine available")
                return
            
            start_time = time.time()
            board_before = self.chess_core.board.copy()
            
            # Set up info callback for real-time metrics
            search_info = []
            def capture_info(**info):
                search_info.append(info.copy())
                # Print live search info
                depth = info.get('depth', '?')
                score = info.get('score', '?')
                nodes = info.get('nodes', '?')
                time_ms = info.get('time_ms', '?')
                nps = info.get('nps', '?')
                pv = info.get('pv', [])
                
                pv_str = ' '.join(pv[:3]) if pv else "..."
                time_str = f"{time_ms/1000:.3f}s" if isinstance(time_ms, (int, float)) else str(time_ms)
                print(f"  Depth {depth:2} | Score: {score:6} | Nodes: {nodes:8} | Time: {time_str:8} | NPS: {nps:8} | PV: {pv_str}")
            
            current_engine.set_info_callback(capture_info)
            
            # Get engine move
            best_move_uci = current_engine.get_move(
                board=board_before,
                depth=self.test_config.test_depths[self.current_test_depth],
                time_limit=2.0
            )
            
            move_time = time.time() - start_time
            
            if best_move_uci:
                move = chess.Move.from_uci(best_move_uci)
                if move in board_before.legal_moves:
                    # Make the move
                    self.chess_core.push_move(move)
                    
                    # Log the move
                    self.session_logger.log_move(
                        move=move,
                        player=current_engine.name,
                        time_taken=move_time,
                        board_before=board_before,
                        board_after=self.chess_core.board
                    )
                    
                    print(f"\\nEngine played: {best_move_uci}")
                    
                    # Auto-evaluate new position if enabled
                    if self.auto_eval_enabled:
                        threading.Thread(target=self._auto_evaluate_position, daemon=True).start()
                        
                else:
                    print(f"Engine returned illegal move: {best_move_uci}")
            else:
                print("Engine returned no move")
                
        except Exception as e:
            print(f"Error in engine move: {e}")
        finally:
            self.testing_active = False
    
    def evaluate_current_position(self):
        """Evaluate the current position"""
        if not self.testing_active:
            threading.Thread(target=self._evaluate_position_worker, daemon=True).start()
            
    def _evaluate_position_worker(self):
        """Worker thread for position evaluation"""
        self.testing_active = True
        try:
            current_engine = self.engine_manager.get_current_engine()
            if not current_engine:
                print("No engine available for evaluation")
                return
                
            eval_data = current_engine.evaluate_position(
                board=self.chess_core.board.copy(),
                depth=3  # Quick evaluation
            )
            
            if eval_data:
                self.last_evaluation = eval_data
                self.session_logger.log_evaluation(
                    board=self.chess_core.board,
                    evaluator=current_engine.name,
                    eval_data=eval_data
                )
            
        except Exception as e:
            print(f"Error evaluating position: {e}")
        finally:
            self.testing_active = False
            
    def _auto_evaluate_position(self):
        """Automatically evaluate position (used after moves)"""
        if self.testing_active:
            return  # Don't interfere with other operations
            
        try:
            current_engine = self.engine_manager.get_current_engine()
            if current_engine:
                eval_data = current_engine.evaluate_position(
                    board=self.chess_core.board.copy(),
                    depth=2  # Quick auto-evaluation
                )
                
                if eval_data:
                    self.last_evaluation = eval_data
                    self.session_logger.log_evaluation(
                        board=self.chess_core.board,
                        evaluator=f"{current_engine.name}-auto",
                        eval_data=eval_data
                    )
        except Exception as e:
            print(f"Error in auto-evaluation: {e}")
    
    def run_test_suite(self):
        """Run a comprehensive test suite"""
        if not self.testing_active:
            threading.Thread(target=self._test_suite_worker, daemon=True).start()
    
    def _test_suite_worker(self):
        """Worker thread for test suite"""
        self.testing_active = True
        try:
            current_engine = self.engine_manager.get_current_engine()
            if not current_engine:
                print("No engine available for testing")
                return
                
            print("\\n" + "=" * 80)
            print(f"STARTING TEST SUITE WITH {current_engine.name.upper()}")
            print("=" * 80)
            
            suite_start_time = time.time()
            
            for i, (position_name, fen) in enumerate(self.test_config.test_positions):
                print(f"\\nTesting position {i+1}/{len(self.test_config.test_positions)}: {position_name}")
                print(f"FEN: {fen}")
                print("-" * 60)
                
                # Load position
                self.chess_core.import_fen(fen)
                
                for depth in self.test_config.test_depths:
                    print(f"\\nDepth {depth} analysis:")
                    
                    test_start_time = time.time()
                    
                    # Get detailed metrics if available (chess-ai specific)
                    if hasattr(current_engine, 'get_detailed_metrics'):
                        detailed_data = current_engine.get_detailed_metrics(
                            board=self.chess_core.board.copy(),
                            depth=depth
                        )
                        
                        # Log the test action
                        test_duration = time.time() - test_start_time
                        self.session_logger.log_test_action(
                            action_type="position_analysis",
                            parameters={
                                "position": position_name,
                                "fen": fen,
                                "depth": depth,
                                "engine": current_engine.name
                            },
                            result=detailed_data,
                            duration=test_duration
                        )
                        
                        # Print results
                        if detailed_data:
                            final_metrics = detailed_data.get("final_metrics", {})
                            best_move = detailed_data.get("best_move", "none")
                            total_time = detailed_data.get("total_time", 0)
                            nodes = final_metrics.get("nodes", 0)
                            score = final_metrics.get("score", 0)
                            nps = int(nodes / max(total_time, 0.001))
                            
                            print(f"Result: {best_move} | Nodes: {nodes} | Time: {total_time:.3f}s | NPS: {nps} | Score: {score:+.2f}")
                    else:
                        # Standard evaluation for non-chess-ai engines
                        eval_data = current_engine.evaluate_position(
                            board=self.chess_core.board.copy(),
                            depth=depth
                        )
                        
                        test_duration = time.time() - test_start_time
                        self.session_logger.log_test_action(
                            action_type="position_evaluation",
                            parameters={
                                "position": position_name,
                                "fen": fen,
                                "depth": depth,
                                "engine": current_engine.name
                            },
                            result=eval_data,
                            duration=test_duration
                        )
                        
                        if eval_data:
                            score = eval_data.get("score", 0)
                            nodes = eval_data.get("nodes", 0)
                            time_ms = eval_data.get("time_ms", 0)
                            print(f"Evaluation: {score:+.2f} | Nodes: {nodes} | Time: {time_ms/1000:.3f}s")
            
            suite_duration = time.time() - suite_start_time
            print("\\n" + "=" * 80)
            print(f"TEST SUITE COMPLETED IN {suite_duration:.1f} SECONDS")
            print("=" * 80)
            
            # Log the complete test suite
            self.session_logger.log_test_action(
                action_type="full_test_suite",
                parameters={
                    "engine": current_engine.name,
                    "positions": len(self.test_config.test_positions),
                    "depths": self.test_config.test_depths
                },
                result={"total_duration": suite_duration},
                duration=suite_duration
            )
            
        except Exception as e:
            print(f"Error in test suite: {e}")
        finally:
            self.testing_active = False
    
    def export_session(self):
        """Export the current test session"""
        try:
            filepath = self.session_logger.export_session()
            if filepath:
                print(f"\\nTest session exported to: {filepath}")
                
                # Also export performance analysis
                performance = self.session_logger.analyze_performance()
                if performance:
                    perf_file = filepath.replace(".json", "_performance.json")
                    with open(perf_file, 'w') as f:
                        json.dump(performance, f, indent=2)
                    print(f"Performance analysis exported to: {perf_file}")
                    
        except Exception as e:
            print(f"Error exporting session: {e}")
    
    def draw_board(self):
        """Draw the chess board"""
        board_colors = [pygame.Color("#2f2f2f"), pygame.Color("#5f5f5f")]
        sq_size = BOARD_WIDTH // 8
        
        for row in range(8):
            for col in range(8):
                # Calculate chess square coordinates
                if self.flip_board:
                    file = 7 - col
                    rank = row
                else:
                    file = col
                    rank = 7 - row

                # Determine color
                color = board_colors[(file + rank) % 2]
                rect = pygame.Rect(col * sq_size, row * sq_size, sq_size, sq_size)
                pygame.draw.rect(self.screen, color, rect)
    
    def draw_pieces(self):
        """Draw pieces on the board"""
        sq_size = BOARD_WIDTH // 8
        
        for row in range(8):
            for col in range(8):
                # Calculate chess square
                if self.flip_board:
                    file = 7 - col
                    rank = row
                else:
                    file = col
                    rank = 7 - row

                square = chess.square(file, rank)
                piece = self.chess_core.board.piece_at(square)

                if piece:
                    piece_key = self.chess_core._piece_image_key(piece)
                    if piece_key and piece_key in self.piece_images:
                        self.screen.blit(self.piece_images[piece_key], 
                                       (col * sq_size, row * sq_size))
    
    def draw_highlights(self):
        """Draw square highlights"""
        sq_size = BOARD_WIDTH // 8
        
        # Highlight last move
        if self.chess_core.board.move_stack:
            last_move = self.chess_core.board.move_stack[-1]
            for square in [last_move.from_square, last_move.to_square]:
                screen_x, screen_y = self.chess_square_to_screen(square)
                s = pygame.Surface((sq_size, sq_size))
                s.set_alpha(128)
                s.fill(pygame.Color("#ff6b6b"))
                self.screen.blit(s, (screen_x, screen_y))
        
        # Highlight selected square
        if self.selected_square is not None:
            screen_x, screen_y = self.chess_square_to_screen(self.selected_square)
            s = pygame.Surface((sq_size, sq_size))
            s.set_alpha(128)
            s.fill(pygame.Color("#ffff00"))
            self.screen.blit(s, (screen_x, screen_y))
            
            # Highlight legal moves
            legal_moves = [move for move in self.chess_core.board.legal_moves 
                          if move.from_square == self.selected_square]
            for move in legal_moves:
                screen_x, screen_y = self.chess_square_to_screen(move.to_square)
                s = pygame.Surface((sq_size, sq_size))
                s.set_alpha(100)
                s.fill(pygame.Color("#4ecdc4"))
                self.screen.blit(s, (screen_x, screen_y))
        
        # Highlight check
        if self.chess_core.board.is_check():
            king_square = self.chess_core.board.king(self.chess_core.board.turn)
            if king_square is not None:
                screen_x, screen_y = self.chess_square_to_screen(king_square)
                s = pygame.Surface((sq_size, sq_size))
                s.set_alpha(128)
                s.fill(pygame.Color("#ff4757"))
                self.screen.blit(s, (screen_x, screen_y))
    
    def chess_square_to_screen(self, square):
        """Convert chess square to screen coordinates"""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        sq_size = BOARD_WIDTH // 8

        if self.flip_board:
            screen_file = 7 - file
            screen_rank = rank
        else:
            screen_file = file
            screen_rank = 7 - rank

        return (screen_file * sq_size, screen_rank * sq_size)
    
    def screen_to_chess_square(self, pos):
        """Convert screen coordinates to chess square"""
        x, y = pos
        if x < 0 or x >= BOARD_WIDTH or y < 0 or y >= WINDOW_HEIGHT:
            return None
            
        sq_size = BOARD_WIDTH // 8
        file = x // sq_size
        rank = y // sq_size

        if self.flip_board:
            chess_file = 7 - file
            chess_rank = rank
        else:
            chess_file = file
            chess_rank = 7 - rank

        if 0 <= chess_file <= 7 and 0 <= chess_rank <= 7:
            return chess.square(chess_file, chess_rank)
        return None
    
    def draw_control_panel(self):
        """Draw the control panel"""
        # Fill background
        panel_rect = pygame.Rect(BOARD_WIDTH, 0, CONTROL_PANEL_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, DARK_BG, panel_rect)
        pygame.draw.rect(self.screen, TEXT_COLOR, panel_rect, 2)
        
        # Title
        title_text = self.font_large.render("Engine Testing", True, TEXT_COLOR)
        self.screen.blit(title_text, (BOARD_WIDTH + 20, 10))
        
        # Draw buttons first (they have fixed positions)
        for button in self.buttons:
            button.enabled = not self.testing_active or button.text in ["Export Session", "Flip Board", "Toggle Auto-Eval"]
            button.draw(self.screen)
        
        # Dynamic content starts after buttons
        info_start_y = 450  # Start after all buttons
        
        # Current position info
        position_name, _ = self.test_config.test_positions[self.current_test_position]
        depth = self.test_config.test_depths[self.current_test_depth]
        
        info_texts = [
            f"Position: {position_name}",
            f"Test Depth: {depth}",
            f"Turn: {'White' if self.chess_core.board.turn else 'Black'}",
            f"Move: {self.chess_core.board.fullmove_number}",
        ]
        
        for i, text in enumerate(info_texts):
            rendered = self.font_small.render(text, True, TEXT_COLOR)
            self.screen.blit(rendered, (BOARD_WIDTH + 20, info_start_y + i * 22))
        
        # Test status
        status_y = info_start_y + 100
        status_text = "TESTING..." if self.testing_active else "READY"
        status_color = ACTIVE_COLOR if self.testing_active else TEXT_COLOR
        status_rendered = self.font_medium.render(f"Status: {status_text}", True, status_color)
        self.screen.blit(status_rendered, (BOARD_WIDTH + 20, status_y))
        
        # Recent evaluation metrics
        metrics_y = status_y + 40
        if self.last_evaluation:
            metrics_texts = [
                f"Last Eval: {self.last_evaluation.get('score', '?'):+.2f}",
                f"Depth: {self.last_evaluation.get('depth', '?')}",
                f"Nodes: {self.last_evaluation.get('nodes', '?')}",
                f"Auto-Eval: {'ON' if self.auto_eval_enabled else 'OFF'}"
            ]
            
            for i, text in enumerate(metrics_texts):
                rendered = self.font_small.render(text, True, TEXT_COLOR)
                self.screen.blit(rendered, (BOARD_WIDTH + 20, metrics_y + i * 18))
        
        # Session info
        session_y = metrics_y + 90
        session_summary = self.session_logger.get_session_summary()
        session_texts = [
            f"Session: {session_summary.get('total_moves', 0)} moves",
            f"Evaluations: {session_summary.get('total_evaluations', 0)}",
            f"Tests: {session_summary.get('total_test_actions', 0)}",
            f"Engine: {self.engine_manager.current_engine or 'None'}"
        ]
        
        for i, text in enumerate(session_texts):
            rendered = self.font_small.render(text, True, TEXT_COLOR)
            self.screen.blit(rendered, (BOARD_WIDTH + 20, session_y + i * 18))
    
    def handle_mouse_click(self, pos):
        """Handle mouse clicks on the board"""
        square = self.screen_to_chess_square(pos)
        if square is None:
            return
            
        # If testing is active, don't allow manual moves
        if self.testing_active:
            return
            
        # Handle piece selection and moves
        if self.selected_square is None:
            # Select piece if it belongs to current player
            piece = self.chess_core.board.piece_at(square)
            if piece and piece.color == self.chess_core.board.turn:
                self.selected_square = square
        else:
            # Try to make a move or reselect
            if square == self.selected_square:
                self.selected_square = None
            else:
                move = chess.Move(self.selected_square, square)
                
                # Handle pawn promotion
                piece = self.chess_core.board.piece_at(self.selected_square)
                if (piece and piece.piece_type == chess.PAWN and 
                    chess.square_rank(square) in [0, 7]):
                    move.promotion = chess.QUEEN
                
                if move in self.chess_core.board.legal_moves:
                    board_before = self.chess_core.board.copy()
                    move_start_time = time.time()
                    
                    self.chess_core.push_move(move)
                    move_time = time.time() - move_start_time
                    
                    # Log the human move
                    self.session_logger.log_move(
                        move=move,
                        player="human",
                        time_taken=move_time,
                        board_before=board_before,
                        board_after=self.chess_core.board
                    )
                    
                    self.selected_square = None
                    print(f"Human played: {move.uci()}")
                    
                    # Auto-evaluate new position if enabled
                    if self.auto_eval_enabled:
                        threading.Thread(target=self._auto_evaluate_position, daemon=True).start()
                        
                else:
                    # Try selecting new piece
                    piece = self.chess_core.board.piece_at(square)
                    if piece and piece.color == self.chess_core.board.turn:
                        self.selected_square = square
                    else:
                        self.selected_square = None
    
    def run(self):
        """Main game loop"""
        print("Universal Chess Engine Testing GUI Started")
        print("Features:")
        print("  - Click pieces to make moves")
        print("  - Use 'Engine Move' to let the engine play")
        print("  - All moves and evaluations are logged automatically")
        print("  - Export session data for analysis")
        print("  - Keyboard shortcuts: F=flip board, R=reset, Space=engine move")
        
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.pos[0] < BOARD_WIDTH:
                        self.handle_mouse_click(event.pos)
                    else:
                        # Handle button clicks
                        for button in self.buttons:
                            button.handle_event(event)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f:
                        self.flip_board_view()
                    elif event.key == pygame.K_r:
                        self.reset_to_start()
                    elif event.key == pygame.K_SPACE and not self.testing_active:
                        self.make_engine_move()
                    elif event.key == pygame.K_e and not self.testing_active:
                        self.evaluate_current_position()
                
                # Handle button hover events
                for button in self.buttons:
                    button.handle_event(event)
            
            # Draw everything
            self.screen.fill(DARK_BG)
            self.draw_board()
            self.draw_pieces()
            self.draw_highlights()
            self.draw_control_panel()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        # Cleanup on exit
        print("\\nShutting down...")
        
        # Export final session if it has data
        if self.session_logger.moves or self.session_logger.evaluations:
            print("Exporting final session...")
            self.export_session()
            
        # Stop all engines
        self.engine_manager.stop_all()
        
        pygame.quit()
        print("Universal Chess Engine Testing GUI closed")

if __name__ == "__main__":
    # Create and run the testing GUI
    gui = ChessEngineTestingGUI()
    gui.run()
