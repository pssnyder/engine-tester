#!/usr/bin/env python3
"""
Enhanced Blunder Analyzer with Improved Stockfish Integration
Provides more accurate blunder detection and evaluation differentials
"""

import chess
import chess.engine
import chess.pgn
import asyncio
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
import os

@dataclass
class BlunderAnalysis:
    """Detailed analysis of a single blunder"""
    move_number: int
    move_played: str
    move_played_uci: str
    best_move: str
    best_move_uci: str
    evaluation_before: float
    evaluation_after: float
    evaluation_best: float
    centipawn_loss: float
    position_fen: str
    blunder_type: str  # "tactical", "positional", "endgame", "opening"
    severity: str  # "blunder", "mistake", "inaccuracy"
    piece_moved: str
    captured_piece: Optional[str] = None
    gave_check: bool = False
    was_check: bool = False
    
    @property
    def is_blunder(self) -> bool:
        """True if this is classified as a blunder (>300cp loss)"""
        return self.centipawn_loss >= 300
        
    @property
    def is_mistake(self) -> bool:
        """True if this is classified as a mistake (100-300cp loss)"""
        return 100 <= self.centipawn_loss < 300
        
    @property
    def is_inaccuracy(self) -> bool:
        """True if this is classified as an inaccuracy (50-100cp loss)"""
        return 50 <= self.centipawn_loss < 100

@dataclass
class GameBlunderReport:
    """Complete blunder analysis for a single game"""
    game_id: str
    white_player: str
    black_player: str
    result: str
    total_moves: int
    blunders: List[BlunderAnalysis] = field(default_factory=list)
    mistakes: List[BlunderAnalysis] = field(default_factory=list)
    inaccuracies: List[BlunderAnalysis] = field(default_factory=list)
    
    @property
    def total_centipawn_loss(self) -> float:
        """Total centipawn loss in the game"""
        all_errors = self.blunders + self.mistakes + self.inaccuracies
        return sum(error.centipawn_loss for error in all_errors)
    
    @property
    def blunder_rate(self) -> float:
        """Blunders per move"""
        return len(self.blunders) / max(self.total_moves, 1)
    
    @property
    def mistake_rate(self) -> float:
        """Mistakes per move"""
        return len(self.mistakes) / max(self.total_moves, 1)

class EnhancedBlunderAnalyzer:
    """Enhanced analyzer with improved Stockfish integration"""
    
    def __init__(self, stockfish_path: str, analysis_depth: int = 20, analysis_time: float = 1.0):
        self.stockfish_path = stockfish_path
        self.analysis_depth = analysis_depth
        self.analysis_time = analysis_time
        self.engine = None
        
        # Ensure Stockfish exists
        if not os.path.exists(stockfish_path):
            raise FileNotFoundError(f"Stockfish not found at {stockfish_path}")
    
    async def start_engine(self) -> bool:
        """Start the Stockfish engine"""
        try:
            transport, self.engine = await chess.engine.popen_uci(self.stockfish_path)
            return True
        except Exception as e:
            print(f"Error starting Stockfish: {e}")
            return False
    
    async def stop_engine(self):
        """Stop the Stockfish engine"""
        if self.engine:
            await self.engine.quit()
            self.engine = None
    
    async def analyze_position(self, board: chess.Board, depth: Optional[int] = None, 
                             time_limit: Optional[float] = None) -> Dict[str, Any]:
        """Analyze a position with Stockfish"""
        if not self.engine:
            raise RuntimeError("Engine not started")
        
        depth = depth or self.analysis_depth
        time_limit = time_limit or self.analysis_time
        
        try:
            info = await self.engine.analyse(
                board, 
                chess.engine.Limit(depth=depth, time=time_limit)
            )
            
            # Extract evaluation
            score = info.get("score", chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE))
            
            if score.is_mate():
                mate_in = score.relative.mate()
                if mate_in is not None:
                    # Convert mate to centipawns (mate in N = 10000 - N*100)
                    if mate_in > 0:
                        evaluation = 10000 - mate_in * 100
                    else:
                        evaluation = -10000 - mate_in * 100
                else:
                    evaluation = 0.0
            else:
                evaluation = score.relative.score(mate_score=10000) or 0.0
            
            # Get best move and principal variation
            best_move = None
            pv = info.get("pv", [])
            if pv:
                best_move = pv[0]
            
            return {
                "evaluation": evaluation,
                "best_move": best_move,
                "best_move_san": board.san(best_move) if best_move else None,
                "pv": pv,
                "depth": info.get("depth", 0),
                "nodes": info.get("nodes", 0),
                "time": info.get("time", 0),
                "nps": info.get("nps", 0)
            }
            
        except Exception as e:
            print(f"Error analyzing position: {e}")
            return {
                "evaluation": 0.0,
                "best_move": None,
                "best_move_san": None,
                "pv": [],
                "depth": 0,
                "nodes": 0,
                "time": 0,
                "nps": 0
            }
    
    def classify_blunder_type(self, board: chess.Board, move: chess.Move) -> str:
        """Classify the type of position where the blunder occurred"""
        piece_count = len(board.piece_map())
        
        # Determine game phase
        if board.fullmove_number <= 15:
            return "opening"
        elif piece_count <= 12:
            return "endgame"
        elif board.is_check() or move.promotion or board.is_capture(move):
            return "tactical"
        else:
            return "positional"
    
    def classify_severity(self, centipawn_loss: float) -> str:
        """Classify the severity of the error"""
        if centipawn_loss >= 300:
            return "blunder"
        elif centipawn_loss >= 100:
            return "mistake"
        elif centipawn_loss >= 50:
            return "inaccuracy"
        else:
            return "acceptable"
    
    async def analyze_game_moves(self, game: chess.pgn.Game, 
                                engine_color: chess.Color,
                                move_sample_rate: float = 1.0) -> GameBlunderReport:
        """Analyze all moves in a game for blunders"""
        
        if not self.engine:
            raise RuntimeError("Engine not started")
        
        white_player = game.headers.get("White", "Unknown")
        black_player = game.headers.get("Black", "Unknown")
        result = game.headers.get("Result", "*")
        
        board = game.board()
        node = game
        
        blunders = []
        mistakes = []
        inaccuracies = []
        move_number = 0
        
        print(f"Analyzing game: {white_player} vs {black_player}")
        
        # Iterate through all moves
        for move_node in game.mainline():
            move_number += 1
            move = move_node.move
            
            # Only analyze moves by the target engine color
            if board.turn != engine_color:
                board.push(move)
                continue
            
            # Sample moves based on sample rate
            import random
            if random.random() > move_sample_rate:
                board.push(move)
                continue
            
            print(f"  Analyzing move {move_number}: {board.san(move)}")
            
            # Analyze position before the move
            position_before = board.copy()
            analysis_before = await self.analyze_position(position_before)
            eval_before = analysis_before["evaluation"]
            best_move = analysis_before["best_move"]
            best_move_san = analysis_before["best_move_san"]
            
            # Make the actual move
            board.push(move)
            
            # Analyze position after the move
            analysis_after = await self.analyze_position(board)
            eval_after = -analysis_after["evaluation"]  # Flip perspective
            
            # Calculate what the evaluation would be after the best move
            if best_move:
                best_board = position_before.copy()
                best_board.push(best_move)
                analysis_best = await self.analyze_position(best_board)
                eval_best = -analysis_best["evaluation"]  # Flip perspective
            else:
                eval_best = eval_before
            
            # Calculate centipawn loss
            centipawn_loss = eval_best - eval_after
            
            # Only record significant errors (>= 50cp loss)
            if centipawn_loss >= 50:
                # Get move details
                piece_moved = position_before.piece_at(move.from_square)
                captured_piece = position_before.piece_at(move.to_square)
                
                blunder_analysis = BlunderAnalysis(
                    move_number=move_number,
                    move_played=board.san(move_node.move),
                    move_played_uci=move.uci(),
                    best_move=best_move_san or "unknown",
                    best_move_uci=best_move.uci() if best_move else "unknown",
                    evaluation_before=eval_before,
                    evaluation_after=eval_after,
                    evaluation_best=eval_best,
                    centipawn_loss=centipawn_loss,
                    position_fen=position_before.fen(),
                    blunder_type=self.classify_blunder_type(position_before, move),
                    severity=self.classify_severity(centipawn_loss),
                    piece_moved=str(piece_moved) if piece_moved else "unknown",
                    captured_piece=str(captured_piece) if captured_piece else None,
                    gave_check=board.is_check(),
                    was_check=position_before.is_check()
                )
                
                # Categorize by severity
                if blunder_analysis.is_blunder:
                    blunders.append(blunder_analysis)
                    print(f"    🔴 BLUNDER: {centipawn_loss:.0f}cp loss")
                elif blunder_analysis.is_mistake:
                    mistakes.append(blunder_analysis)
                    print(f"    🟡 MISTAKE: {centipawn_loss:.0f}cp loss")
                elif blunder_analysis.is_inaccuracy:
                    inaccuracies.append(blunder_analysis)
                    print(f"    🟠 INACCURACY: {centipawn_loss:.0f}cp loss")
        
        return GameBlunderReport(
            game_id=f"{white_player}_vs_{black_player}",
            white_player=white_player,
            black_player=black_player,
            result=result,
            total_moves=move_number,
            blunders=blunders,
            mistakes=mistakes,
            inaccuracies=inaccuracies
        )
    
    def save_report(self, report: GameBlunderReport, output_path: str):
        """Save blunder report to JSON"""
        report_data = {
            "game_info": {
                "game_id": report.game_id,
                "white_player": report.white_player,
                "black_player": report.black_player,
                "result": report.result,
                "total_moves": report.total_moves
            },
            "summary": {
                "total_centipawn_loss": report.total_centipawn_loss,
                "blunder_count": len(report.blunders),
                "mistake_count": len(report.mistakes),
                "inaccuracy_count": len(report.inaccuracies),
                "blunder_rate": report.blunder_rate,
                "mistake_rate": report.mistake_rate
            },
            "blunders": [
                {
                    "move_number": b.move_number,
                    "move_played": b.move_played,
                    "move_played_uci": b.move_played_uci,
                    "best_move": b.best_move,
                    "best_move_uci": b.best_move_uci,
                    "evaluation_before": b.evaluation_before,
                    "evaluation_after": b.evaluation_after,
                    "evaluation_best": b.evaluation_best,
                    "centipawn_loss": b.centipawn_loss,
                    "position_fen": b.position_fen,
                    "blunder_type": b.blunder_type,
                    "severity": b.severity,
                    "piece_moved": b.piece_moved,
                    "captured_piece": b.captured_piece,
                    "gave_check": b.gave_check,
                    "was_check": b.was_check
                }
                for b in report.blunders
            ],
            "mistakes": [
                {
                    "move_number": m.move_number,
                    "move_played": m.move_played,
                    "move_played_uci": m.move_played_uci,
                    "best_move": m.best_move,
                    "best_move_uci": m.best_move_uci,
                    "evaluation_before": m.evaluation_before,
                    "evaluation_after": m.evaluation_after,
                    "evaluation_best": m.evaluation_best,
                    "centipawn_loss": m.centipawn_loss,
                    "position_fen": m.position_fen,
                    "blunder_type": m.blunder_type,
                    "severity": m.severity,
                    "piece_moved": m.piece_moved,
                    "captured_piece": m.captured_piece,
                    "gave_check": m.gave_check,
                    "was_check": m.was_check
                }
                for m in report.mistakes
            ],
            "inaccuracies": [
                {
                    "move_number": i.move_number,
                    "move_played": i.move_played,
                    "move_played_uci": i.move_played_uci,
                    "best_move": i.best_move,
                    "best_move_uci": i.best_move_uci,
                    "evaluation_before": i.evaluation_before,
                    "evaluation_after": i.evaluation_after,
                    "evaluation_best": i.evaluation_best,
                    "centipawn_loss": i.centipawn_loss,
                    "position_fen": i.position_fen,
                    "blunder_type": i.blunder_type,
                    "severity": i.severity,
                    "piece_moved": i.piece_moved,
                    "captured_piece": i.captured_piece,
                    "gave_check": i.gave_check,
                    "was_check": i.was_check
                }
                for i in report.inaccuracies
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"Blunder report saved to {output_path}")

async def main():
    """Example usage"""
    stockfish_path = "../../engines/Stockfish/stockfish-windows-x86-64-avx2.exe"
    
    analyzer = EnhancedBlunderAnalyzer(stockfish_path, analysis_depth=15, analysis_time=0.5)
    
    await analyzer.start_engine()
    
    try:
        # Example: analyze a PGN file
        pgn_path = "../../results/Engine Battle 20250820/Engine Battle 20250820.pgn"
        
        if os.path.exists(pgn_path):
            with open(pgn_path) as f:
                game = chess.pgn.read_game(f)
                if game:
                    # Analyze white's moves
                    report = await analyzer.analyze_game_moves(game, chess.WHITE, move_sample_rate=0.3)
                    analyzer.save_report(report, "blunder_analysis_example.json")
        
    finally:
        await analyzer.stop_engine()

if __name__ == "__main__":
    asyncio.run(main())
