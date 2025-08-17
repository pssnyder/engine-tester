"""
Tkinter-based Chess Engine Testing GUI
A more reliable GUI implementation using native tkinter widgets
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import chess
import chess.svg
from PIL import Image, ImageTk
import threading
import queue
import time
from pathlib import Path
import json
from typing import Optional, Dict, Any

from chess_core import ChessCore
from universal_engine_manager import UniversalEngineManager

# Import session logger with fallback
try:
    from session_logger import SimpleSessionLogger  # type: ignore
except ImportError:
    # Fallback logger that matches SimpleSessionLogger interface
    class SimpleSessionLogger:
        def __init__(self):
            pass
        def log_move(self, move, player: str, time_taken: float, board_before=None, board_after=None, **additional_data):
            print(f"Move logged: {move} by {player} in {time_taken:.3f}s")
        def start_new_session(self):
            print("New session started")
        def end_session(self):
            print("Session ended")

class TkinterChessGUI:
    """Chess Engine Testing GUI using tkinter"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Universal Chess Engine Testing Suite")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2b2b2b')
        
        # Core components
        self.chess_core = ChessCore()
        self.engine_manager = UniversalEngineManager()
        
        # Session logger with fallback
        try:
            self.session_logger = SimpleSessionLogger()
        except:
            # Simple fallback logger that matches SimpleSessionLogger interface
            class FallbackLogger:
                def log_move(self, move, player: str, time_taken: float, board_before=None, board_after=None, **additional_data): 
                    print(f"Move logged: {move} by {player} in {time_taken:.3f}s")
                def start_new_session(self): 
                    print("New session started")
                def end_session(self): 
                    print("Session ended")
            self.session_logger = FallbackLogger()
        
        # GUI state
        self.selected_square = None
        self.legal_moves = []
        self.last_move = None
        
        # Canvas for chess board
        self.board_size = 480
        self.square_size = self.board_size // 8
        
        # Initialize GUI
        self.setup_gui()
        self.update_display()
        
        # Start engine auto-loading
        self.auto_load_engines()
        
    def setup_gui(self):
        """Set up the GUI layout"""
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - Chess board
        board_frame = tk.Frame(main_frame, bg='#2b2b2b')
        board_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        # Chess board canvas
        self.board_canvas = tk.Canvas(
            board_frame, 
            width=self.board_size, 
            height=self.board_size,
            bg='#3c3c3c',
            highlightthickness=2,
            highlightbackground='#4a9eff'
        )
        self.board_canvas.pack()
        self.board_canvas.bind("<Button-1>", self.on_board_click)
        
        # Right side - Controls and info
        control_frame = tk.Frame(main_frame, bg='#2b2b2b', width=400)
        control_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        control_frame.pack_propagate(False)
        
        # Engine selection section
        engine_frame = tk.LabelFrame(
            control_frame, 
            text="Engine Control", 
            bg='#2b2b2b', 
            fg='#4a9eff',
            font=('Arial', 12, 'bold')
        )
        engine_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Engine dropdown
        tk.Label(engine_frame, text="Select Engine:", bg='#2b2b2b', fg='white').pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.engine_var = tk.StringVar()
        self.engine_dropdown = ttk.Combobox(
            engine_frame, 
            textvariable=self.engine_var,
            state="readonly",
            width=40
        )
        self.engine_dropdown.pack(fill=tk.X, padx=5, pady=5)
        self.engine_dropdown.bind('<<ComboboxSelected>>', self.on_engine_selected)
        
        # Engine control buttons
        button_frame = tk.Frame(engine_frame, bg='#2b2b2b')
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.load_engine_btn = tk.Button(
            button_frame,
            text="Load Engine",
            bg='#4a9eff',
            fg='white',
            font=('Arial', 10, 'bold'),
            command=self.load_selected_engine
        )
        self.load_engine_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.engine_move_btn = tk.Button(
            button_frame,
            text="Engine Move",
            bg='#28a745',
            fg='white',
            font=('Arial', 10, 'bold'),
            command=self.request_engine_move
        )
        self.engine_move_btn.pack(side=tk.LEFT, padx=5)
        
        self.evaluate_btn = tk.Button(
            button_frame,
            text="Evaluate",
            bg='#ffc107',
            fg='black',
            font=('Arial', 10, 'bold'),
            command=self.evaluate_position
        )
        self.evaluate_btn.pack(side=tk.LEFT, padx=5)
        
        # Game control section
        game_frame = tk.LabelFrame(
            control_frame,
            text="Game Control",
            bg='#2b2b2b',
            fg='#4a9eff',
            font=('Arial', 12, 'bold')
        )
        game_frame.pack(fill=tk.X, pady=(0, 10))
        
        game_button_frame = tk.Frame(game_frame, bg='#2b2b2b')
        game_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.new_game_btn = tk.Button(
            game_button_frame,
            text="New Game",
            bg='#17a2b8',
            fg='white',
            font=('Arial', 10, 'bold'),
            command=self.new_game
        )
        self.new_game_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.undo_btn = tk.Button(
            game_button_frame,
            text="Undo Move",
            bg='#6c757d',
            fg='white',
            font=('Arial', 10, 'bold'),
            command=self.undo_move
        )
        self.undo_btn.pack(side=tk.LEFT, padx=5)
        
        self.flip_btn = tk.Button(
            game_button_frame,
            text="Flip Board",
            bg='#6f42c1',
            fg='white',
            font=('Arial', 10, 'bold'),
            command=self.flip_board
        )
        self.flip_btn.pack(side=tk.LEFT, padx=5)
        
        # FEN input section
        fen_frame = tk.LabelFrame(
            control_frame,
            text="Position Setup",
            bg='#2b2b2b',
            fg='#4a9eff',
            font=('Arial', 12, 'bold')
        )
        fen_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(fen_frame, text="FEN:", bg='#2b2b2b', fg='white').pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.fen_entry = tk.Entry(fen_frame, bg='#3c3c3c', fg='white', insertbackground='white')
        self.fen_entry.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        fen_button_frame = tk.Frame(fen_frame, bg='#2b2b2b')
        fen_button_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.load_fen_btn = tk.Button(
            fen_button_frame,
            text="Load FEN",
            bg='#fd7e14',
            fg='white',
            font=('Arial', 10, 'bold'),
            command=self.load_fen
        )
        self.load_fen_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.copy_fen_btn = tk.Button(
            fen_button_frame,
            text="Copy FEN",
            bg='#20c997',
            fg='white',
            font=('Arial', 10, 'bold'),
            command=self.copy_fen
        )
        self.copy_fen_btn.pack(side=tk.LEFT, padx=5)
        
        # Engine info section
        info_frame = tk.LabelFrame(
            control_frame,
            text="Engine Information",
            bg='#2b2b2b',
            fg='#4a9eff',
            font=('Arial', 12, 'bold')
        )
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable text widget for engine info
        info_text_frame = tk.Frame(info_frame, bg='#2b2b2b')
        info_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.info_text = tk.Text(
            info_text_frame,
            bg='#3c3c3c',
            fg='#00ff00',
            font=('Consolas', 9),
            wrap=tk.WORD
        )
        
        info_scrollbar = tk.Scrollbar(info_text_frame, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scrollbar.set)
        
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status bar
        self.status_bar = tk.Label(
            self.root,
            text="Ready - Select an engine to begin",
            bg='#1e1e1e',
            fg='white',
            anchor=tk.W,
            padx=10
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def draw_board(self):
        """Draw the chess board with pieces"""
        self.board_canvas.delete("all")
        
        # Board colors
        light_color = '#f0d9b5'
        dark_color = '#b58863'
        highlight_color = '#ffff00'
        legal_move_color = '#00ff00'
        
        # Draw squares
        for row in range(8):
            for col in range(8):
                x1 = col * self.square_size
                y1 = row * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size
                
                # Determine square color
                is_light = (row + col) % 2 == 0
                color = light_color if is_light else dark_color
                
                # Highlight selected square
                square = chess.square(col, 7-row)
                if square == self.selected_square:
                    color = highlight_color
                elif square in [move.to_square for move in self.legal_moves]:
                    color = legal_move_color
                
                self.board_canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline='black',
                    width=1
                )
                
                # Draw coordinates
                if col == 0:  # File letters
                    file_letter = chr(ord('a') + col)
                    self.board_canvas.create_text(
                        x1 + 5, y2 - 5,
                        text=str(8-row),
                        fill='black' if is_light else 'white',
                        font=('Arial', 8, 'bold')
                    )
                if row == 7:  # Rank numbers
                    self.board_canvas.create_text(
                        x2 - 5, y2 - 5,
                        text=chr(ord('a') + col),
                        fill='black' if is_light else 'white',
                        font=('Arial', 8, 'bold')
                    )
        
        # Draw pieces
        board = self.chess_core.board
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7-row)
                piece = board.piece_at(square)
                
                if piece:
                    x = col * self.square_size + self.square_size // 2
                    y = row * self.square_size + self.square_size // 2
                    
                    # Unicode chess pieces
                    piece_symbols = {
                        'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',
                        'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚'
                    }
                    
                    symbol = piece_symbols.get(piece.symbol(), piece.symbol() or '?')
                    color = 'white' if piece.color == chess.WHITE else 'black'
                    
                    self.board_canvas.create_text(
                        x, y,
                        text=symbol,
                        font=('Arial', 32),
                        fill=color
                    )
        
        # Highlight last move
        if self.last_move:
            for square in [self.last_move.from_square, self.last_move.to_square]:
                col = chess.square_file(square)
                row = 7 - chess.square_rank(square)
                x1 = col * self.square_size
                y1 = row * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size
                
                self.board_canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline='red',
                    width=3,
                    fill=''
                )
    
    def on_board_click(self, event):
        """Handle board clicks"""
        col = event.x // self.square_size
        row = event.y // self.square_size
        
        if 0 <= col < 8 and 0 <= row < 8:
            square = chess.square(col, 7-row)
            
            if self.selected_square is None:
                # Select piece if there's one on this square
                board = self.chess_core.board
                piece = board.piece_at(square)
                
                if piece and piece.color == board.turn:
                    self.selected_square = square
                    self.legal_moves = [move for move in board.legal_moves 
                                      if move.from_square == square]
                    self.update_display()
                    
            else:
                # Try to make a move
                move = None
                for legal_move in self.legal_moves:
                    if legal_move.to_square == square:
                        move = legal_move
                        break
                
                if move:
                    success = self.chess_core.push_move(move)  # Pass the Move object directly
                    if success:
                        self.last_move = move
                        self.session_logger.log_move(
                            move.uci(), 
                            player="Human", 
                            time_taken=0.0,
                            board_after=self.chess_core.board
                        )
                        self.update_info_display(f"Move played: {move}")
                
                # Clear selection
                self.selected_square = None
                self.legal_moves = []
                self.update_display()
    
    def auto_load_engines(self):
        """Auto-load available engines"""
        try:
            # Get available engines
            available = self.engine_manager.get_available_engines()
            engine_names = list(available.keys())
            
            # Update dropdown
            self.engine_dropdown['values'] = engine_names
            
            # Auto-load default engines
            success = self.engine_manager.auto_load_default_engines()
            
            if success:
                current = self.engine_manager.get_current_engine()
                if current:
                    self.engine_var.set(current.name)
                    self.update_info_display(f"Auto-loaded engine: {current.name}")
            
            self.update_status(f"Found {len(engine_names)} engines")
            
        except Exception as e:
            self.update_info_display(f"Error loading engines: {e}")
    
    def load_selected_engine(self):
        """Load the selected engine"""
        engine_name = self.engine_var.get()
        if not engine_name:
            messagebox.showwarning("No Engine", "Please select an engine first")
            return
        
        try:
            success = self.engine_manager.set_current_engine(engine_name)
            if success:
                self.update_info_display(f"Loaded engine: {engine_name}")
                self.update_status(f"Engine loaded: {engine_name}")
            else:
                messagebox.showerror("Engine Error", f"Failed to load engine: {engine_name}")
        except Exception as e:
            messagebox.showerror("Engine Error", f"Error loading engine: {e}")
    
    def on_engine_selected(self, event=None):
        """Handle engine selection from dropdown"""
        self.load_selected_engine()
    
    def request_engine_move(self):
        """Request a move from the current engine"""
        engine = self.engine_manager.get_current_engine()
        if not engine:
            messagebox.showwarning("No Engine", "Please load an engine first")
            return
        
        try:
            self.update_status("Engine thinking...")
            
            # Run engine move in thread to prevent GUI freezing
            def get_move():
                board = self.chess_core.board
                move = engine.get_move(board, time_limit=2.0)
                
                if move:
                    # Execute move on main thread
                    self.root.after(0, lambda: self.execute_engine_move(move))
                else:
                    self.root.after(0, lambda: self.update_status("Engine failed to find a move"))
            
            threading.Thread(target=get_move, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Engine Error", f"Error requesting move: {e}")
            self.update_status("Ready")
    
    def execute_engine_move(self, move_str):
        """Execute the engine's move"""
        try:
            success = self.chess_core.push_move(move_str)
            if success:
                move = chess.Move.from_uci(move_str)
                self.last_move = move
                self.session_logger.log_move(
                    move_str, 
                    player="Engine", 
                    time_taken=0.0,
                    board_after=self.chess_core.board
                )
                self.update_info_display(f"Engine played: {move}")
                self.update_display()
            else:
                self.update_info_display(f"Invalid engine move: {move_str}")
            
            self.update_status("Ready")
            
        except Exception as e:
            self.update_info_display(f"Error executing move: {e}")
            self.update_status("Ready")
    
    def evaluate_position(self):
        """Evaluate the current position"""
        engine = self.engine_manager.get_current_engine()
        if not engine:
            messagebox.showwarning("No Engine", "Please load an engine first")
            return
        
        try:
            self.update_status("Evaluating position...")
            
            def evaluate():
                board = self.chess_core.board
                evaluation = engine.evaluate_position(board, depth=10)
                self.root.after(0, lambda: self.show_evaluation(evaluation))
            
            threading.Thread(target=evaluate, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Engine Error", f"Error evaluating position: {e}")
            self.update_status("Ready")
    
    def show_evaluation(self, evaluation):
        """Show evaluation results"""
        try:
            eval_text = "Position Evaluation:\n"
            for key, value in evaluation.items():
                eval_text += f"{key}: {value}\n"
            
            self.update_info_display(eval_text)
            self.update_status("Ready")
            
        except Exception as e:
            self.update_info_display(f"Error showing evaluation: {e}")
            self.update_status("Ready")
    
    def new_game(self):
        """Start a new game"""
        self.chess_core.new_game()
        self.selected_square = None
        self.legal_moves = []
        self.last_move = None
        self.session_logger.start_new_session()
        self.update_display()
        self.update_info_display("New game started")
        self.update_status("New game - White to move")
    
    def undo_move(self):
        """Undo the last move"""
        if self.chess_core.board.move_stack:
            self.chess_core.board.pop()
            self.selected_square = None
            self.legal_moves = []
            self.last_move = None
            self.update_display()
            self.update_info_display("Move undone")
        else:
            messagebox.showinfo("Undo", "No move to undo")
    
    def flip_board(self):
        """Flip the board view"""
        # For now, just update display
        # TODO: Implement actual board flipping
        self.update_display()
        self.update_info_display("Board flipped")
    
    def load_fen(self):
        """Load position from FEN"""
        fen = self.fen_entry.get().strip()
        if not fen:
            messagebox.showwarning("Invalid FEN", "Please enter a FEN string")
            return
        
        try:
            success = self.chess_core.import_fen(fen)
            if success:
                self.selected_square = None
                self.legal_moves = []
                self.last_move = None
                self.update_display()
                self.update_info_display(f"Position loaded from FEN")
            else:
                messagebox.showerror("Invalid FEN", "Invalid FEN string")
        except Exception as e:
            messagebox.showerror("FEN Error", f"Error loading FEN: {e}")
    
    def copy_fen(self):
        """Copy current FEN to clipboard"""
        fen = self.chess_core.board.fen()
        self.root.clipboard_clear()
        self.root.clipboard_append(fen)
        self.update_info_display(f"FEN copied to clipboard")
    
    def update_display(self):
        """Update the chess board display"""
        self.draw_board()
        
        # Update FEN entry
        current_fen = self.chess_core.board.fen()
        self.fen_entry.delete(0, tk.END)
        self.fen_entry.insert(0, current_fen)
        
        # Update turn indicator
        board = self.chess_core.board
        turn = "White" if board.turn == chess.WHITE else "Black"
        move_num = board.fullmove_number
        
        # Check for game end
        if board.is_checkmate():
            winner = "Black" if board.turn == chess.WHITE else "White"
            self.update_status(f"Checkmate! {winner} wins")
        elif board.is_stalemate():
            self.update_status("Stalemate - Draw")
        elif board.is_insufficient_material():
            self.update_status("Draw - Insufficient material")
        else:
            check_text = " (Check)" if board.is_check() else ""
            self.update_status(f"Move {move_num} - {turn} to move{check_text}")
    
    def update_info_display(self, message):
        """Update the info display"""
        self.info_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.info_text.see(tk.END)
    
    def update_status(self, message):
        """Update status bar"""
        self.status_bar.config(text=message)
    
    def run(self):
        """Run the GUI"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.close()
    
    def close(self):
        """Clean up and close"""
        try:
            if hasattr(self, 'engine_manager'):
                self.engine_manager.stop_all()
            if hasattr(self, 'session_logger'):
                self.session_logger.end_session()
        except:
            pass
        
        if hasattr(self, 'root'):
            self.root.quit()
            self.root.destroy()

def main():
    """Main entry point"""
    try:
        gui = TkinterChessGUI()
        gui.run()
    except Exception as e:
        print(f"Error starting GUI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
