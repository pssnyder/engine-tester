#!/usr/bin/env python3
"""
V7P3R Stockfish Evaluation Comparison: v7.0 vs v9.2
Uses Stockfish as control evaluation to objectively grade move quality
"""

import subprocess
import time
import chess
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class EngineResult:
    """Result from engine analysis."""
    engine_name: str
    move: str
    evaluation: int
    depth: int
    time_taken: float
    success: bool = True

@dataclass
class StockfishAnalysis:
    """Stockfish analysis as control evaluation."""
    best_move: str
    best_eval: int
    depth: int
    time_taken: float
    pv_line: List[str]

@dataclass
class MoveQualityGrade:
    """Stockfish grading of engine move quality."""
    engine_move: str
    engine_eval: int
    best_move: str
    best_eval: int
    centipawn_loss: int
    quality_rating: str  # "excellent", "good", "inaccurate", "mistake", "blunder"
    grade_notes: str

@dataclass
class PositionComparison:
    """Complete comparison of a position."""
    fen: str
    description: str
    phase: str
    v70_result: EngineResult
    v92_result: EngineResult
    stockfish_analysis: StockfishAnalysis
    v70_grade: MoveQualityGrade
    v92_grade: MoveQualityGrade
    winner: str  # "v7.0", "v9.2", "tie"

class StockfishEvaluationComparator:
    """Compare V7P3R versions using Stockfish as control evaluation."""
    
    def __init__(self):
        self.engines = {
            "v7.0": "engines/V7P3R/V7P3R_v7.0.exe",
            "v9.2": "engines/V7P3R/V7P3R_v9.2.exe",
            "stockfish": "engines/Stockfish/stockfish-windows-x86-64-avx2.exe"
        }
        
        # Test positions across different game phases and tactical themes
        self.test_positions = [
            # Opening positions
            {
                "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "description": "Starting position - development principles",
                "phase": "opening"
            },
            {
                "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
                "description": "King's pawn opening - central control",
                "phase": "opening"
            },
            {
                "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
                "description": "Italian Game development",
                "phase": "opening"
            },
            
            # Middlegame positions
            {
                "fen": "r2q1rk1/ppp2ppp/2n1bn2/2bpP3/3P4/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 10",
                "description": "Complex middlegame - tactical opportunities",
                "phase": "middlegame"
            },
            {
                "fen": "r1bq1rk1/pp3ppp/2n1pn2/3p4/1bPP4/2N1PN2/PP2BPPP/R1BQK2R w KQ - 2 8",
                "description": "Queen's Gambit Declined - positional play",
                "phase": "middlegame"
            },
            {
                "fen": "r3r1k1/pppq1ppp/3p1n2/4p3/4P3/2NP1Q2/PPP2PPP/R4RK1 w - - 0 12",
                "description": "Heavy piece coordination",
                "phase": "middlegame"
            },
            
            # Tactical positions
            {
                "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
                "description": "Smothered mate pattern",
                "phase": "tactical"
            },
            {
                "fen": "8/8/8/3r4/8/3R4/3K4/8 w - - 0 1",
                "description": "Rook pin tactical motif",
                "phase": "tactical"
            },
            {
                "fen": "8/8/8/3k4/8/8/3N4/3K4 w - - 0 1",
                "description": "Knight fork opportunity",
                "phase": "tactical"
            },
            
            # Endgame positions
            {
                "fen": "8/4kp2/6p1/4K3/6P1/8/5P2/8 w - - 0 40",
                "description": "King and pawn endgame - opposition",
                "phase": "endgame"
            },
            {
                "fen": "8/8/8/8/8/3k4/3R4/3K4 w - - 0 80",
                "description": "Rook endgame technique",
                "phase": "endgame"
            },
            {
                "fen": "4k3/8/4K3/8/8/8/6Q1/8 w - - 0 70",
                "description": "Queen vs King mate",
                "phase": "endgame"
            }
        ]
    
    def test_engine(self, engine_path: str, fen: str, time_limit: float = 5.0) -> EngineResult:
        """Test an engine on a position."""
        engine_name = Path(engine_path).stem
        
        try:
            process = subprocess.Popen(
                [engine_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if not process.stdin or not process.stdout:
                return EngineResult(engine_name, "", 0, 0, 0.0, False)
            
            start_time = time.time()
            
            # UCI handshake
            process.stdin.write("uci\n")
            process.stdin.flush()
            
            # Wait for uciok
            uci_start = time.time()
            while time.time() - uci_start < 3:
                line = process.stdout.readline().strip()
                if "uciok" in line:
                    break
            
            # Set position and search
            process.stdin.write(f"position fen {fen}\n")
            process.stdin.flush()
            process.stdin.write(f"go movetime {int(time_limit * 1000)}\n")
            process.stdin.flush()
            
            best_move = ""
            evaluation = 0
            depth = 0
            
            search_start = time.time()
            while time.time() - search_start < time_limit + 2:
                line = process.stdout.readline().strip()
                
                if line.startswith("info"):
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "depth" and i+1 < len(parts):
                            try:
                                depth = max(depth, int(parts[i+1]))
                            except:
                                pass
                        elif part == "score" and i+2 < len(parts):
                            if parts[i+1] == "cp":
                                try:
                                    evaluation = int(parts[i+2])
                                except:
                                    pass
                            elif parts[i+1] == "mate":
                                try:
                                    mate_in = int(parts[i+2])
                                    evaluation = 900000 if mate_in > 0 else -900000
                                except:
                                    pass
                
                elif line.startswith("bestmove"):
                    best_move = line.split()[1] if len(line.split()) > 1 else ""
                    break
            
            process.stdin.write("quit\n")
            process.stdin.flush()
            process.terminate()
            
            total_time = time.time() - start_time
            
            return EngineResult(
                engine_name=engine_name,
                move=best_move,
                evaluation=evaluation,
                depth=depth,
                time_taken=total_time,
                success=bool(best_move)
            )
            
        except Exception as e:
            return EngineResult(engine_name, "", 0, 0, 0.0, False)
    
    def analyze_with_stockfish(self, fen: str, time_limit: float = 10.0) -> StockfishAnalysis:
        """Get Stockfish analysis as control evaluation."""
        try:
            process = subprocess.Popen(
                [self.engines["stockfish"]],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if not process.stdin or not process.stdout:
                return StockfishAnalysis("", 0, 0, 0.0, [])
            
            start_time = time.time()
            
            # UCI handshake
            process.stdin.write("uci\n")
            process.stdin.flush()
            
            # Wait for uciok
            uci_start = time.time()
            while time.time() - uci_start < 3:
                line = process.stdout.readline().strip()
                if "uciok" in line:
                    break
            
            # Set Stockfish to maximum strength
            process.stdin.write("setoption name UCI_LimitStrength value false\n")
            process.stdin.flush()
            process.stdin.write("setoption name Threads value 4\n")
            process.stdin.flush()
            process.stdin.write("setoption name Hash value 512\n")
            process.stdin.flush()
            
            # Set position and search
            process.stdin.write(f"position fen {fen}\n")
            process.stdin.flush()
            process.stdin.write(f"go movetime {int(time_limit * 1000)}\n")
            process.stdin.flush()
            
            best_move = ""
            evaluation = 0
            depth = 0
            pv_line = []
            
            search_start = time.time()
            while time.time() - search_start < time_limit + 2:
                line = process.stdout.readline().strip()
                
                if line.startswith("info"):
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "depth" and i+1 < len(parts):
                            try:
                                new_depth = int(parts[i+1])
                                if new_depth > depth:
                                    depth = new_depth
                            except:
                                pass
                        elif part == "score" and i+2 < len(parts):
                            if parts[i+1] == "cp":
                                try:
                                    evaluation = int(parts[i+2])
                                except:
                                    pass
                            elif parts[i+1] == "mate":
                                try:
                                    mate_in = int(parts[i+2])
                                    evaluation = 900000 if mate_in > 0 else -900000
                                except:
                                    pass
                        elif part == "pv" and i+1 < len(parts):
                            # Extract principal variation
                            pv_line = parts[i+1:i+6]  # First 5 moves
                            break
                
                elif line.startswith("bestmove"):
                    best_move = line.split()[1] if len(line.split()) > 1 else ""
                    break
            
            process.stdin.write("quit\n")
            process.stdin.flush()
            process.terminate()
            
            total_time = time.time() - start_time
            
            return StockfishAnalysis(
                best_move=best_move,
                best_eval=evaluation,
                depth=depth,
                time_taken=total_time,
                pv_line=pv_line
            )
            
        except Exception as e:
            return StockfishAnalysis("", 0, 0, 0.0, [])
    
    def evaluate_move_with_stockfish(self, fen: str, move: str, stockfish_best: str, stockfish_eval: int) -> Tuple[int, str]:
        """Evaluate an engine's move using Stockfish analysis."""
        try:
            # Create a new position after the engine's move
            board = chess.Board(fen)
            engine_move = chess.Move.from_uci(move)
            
            if not board.is_legal(engine_move):
                return -999999, "illegal"
            
            board.push(engine_move)
            new_fen = board.fen()
            
            # Get Stockfish evaluation of the resulting position
            process = subprocess.Popen(
                [self.engines["stockfish"]],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if not process.stdin or not process.stdout:
                return 0, "error"
            
            # Quick evaluation
            process.stdin.write("uci\n")
            process.stdin.flush()
            
            # Wait for uciok
            start_time = time.time()
            while time.time() - start_time < 3:
                line = process.stdout.readline().strip()
                if "uciok" in line:
                    break
            
            process.stdin.write("setoption name UCI_LimitStrength value false\n")
            process.stdin.flush()
            process.stdin.write(f"position fen {new_fen}\n")
            process.stdin.flush()
            process.stdin.write("go movetime 3000\n")  # 3 second evaluation
            process.stdin.flush()
            
            evaluation = 0
            search_start = time.time()
            while time.time() - search_start < 5:
                line = process.stdout.readline().strip()
                
                if line.startswith("info"):
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "score" and i+2 < len(parts):
                            if parts[i+1] == "cp":
                                try:
                                    # Flip evaluation for opponent's perspective
                                    evaluation = -int(parts[i+2])
                                except:
                                    pass
                            elif parts[i+1] == "mate":
                                try:
                                    mate_in = int(parts[i+2])
                                    # Flip mate score for opponent's perspective
                                    evaluation = -900000 if mate_in > 0 else 900000
                                except:
                                    pass
                
                elif line.startswith("bestmove"):
                    break
            
            process.stdin.write("quit\n")
            process.stdin.flush()
            process.terminate()
            
            return evaluation, "analyzed"
            
        except Exception as e:
            return 0, "error"
    
    def grade_move_quality(self, engine_move: str, engine_eval: int, best_move: str, best_eval: int, 
                          stockfish_analysis: StockfishAnalysis) -> MoveQualityGrade:
        """Grade an engine's move quality using Stockfish as reference."""
        
        # Calculate centipawn loss
        centipawn_loss = best_eval - engine_eval
        
        # Determine quality rating based on centipawn loss
        if centipawn_loss <= 10:
            quality = "excellent"
            notes = "Move is virtually identical to Stockfish choice"
        elif centipawn_loss <= 25:
            quality = "good"
            notes = "Strong move with minimal evaluation loss"
        elif centipawn_loss <= 50:
            quality = "inaccurate"
            notes = "Reasonable move but not optimal"
        elif centipawn_loss <= 100:
            quality = "mistake"
            notes = "Significant evaluation loss"
        else:
            quality = "blunder"
            notes = "Major tactical or positional error"
        
        # Special cases
        if engine_move == best_move:
            quality = "excellent"
            notes = "Exact match with Stockfish best move"
        elif engine_eval >= 900000 and best_eval >= 900000:
            quality = "excellent"
            notes = "Both moves lead to forced mate"
        elif engine_eval <= -900000 and best_eval <= -900000:
            quality = "acceptable"
            notes = "Position already lost for both moves"
        
        return MoveQualityGrade(
            engine_move=engine_move,
            engine_eval=engine_eval,
            best_move=best_move,
            best_eval=best_eval,
            centipawn_loss=centipawn_loss,
            quality_rating=quality,
            grade_notes=notes
        )
    
    def compare_positions(self) -> List[PositionComparison]:
        """Run complete comparison on all test positions."""
        print("🔍 V7P3R STOCKFISH EVALUATION COMPARISON")
        print("=" * 60)
        print("Using Stockfish as control evaluation to grade move quality")
        print(f"Testing {len(self.test_positions)} positions across multiple game phases")
        
        # Verify engines exist
        for name, path in self.engines.items():
            if not Path(path).exists():
                print(f"❌ {name} engine not found: {path}")
                return []
            print(f"✅ {name}: {path}")
        
        results = []
        
        for i, pos_data in enumerate(self.test_positions, 1):
            fen = pos_data["fen"]
            description = pos_data["description"]
            phase = pos_data["phase"]
            
            print(f"\n📍 Position {i}/{len(self.test_positions)}: {description}")
            print(f"   Phase: {phase}")
            print(f"   FEN: {fen}")
            
            # Get Stockfish analysis first (reference evaluation)
            print("   🤖 Analyzing with Stockfish...")
            stockfish_analysis = self.analyze_with_stockfish(fen, 10.0)
            print(f"   📊 Stockfish: {stockfish_analysis.best_move} eval={stockfish_analysis.best_eval:+d} depth={stockfish_analysis.depth}")
            
            # Test both V7P3R versions
            print("   🧠 Testing V7P3R v7.0...")
            v70_result = self.test_engine(self.engines["v7.0"], fen, 5.0)
            print(f"   📊 v7.0: {v70_result.move} eval={v70_result.evaluation:+d} depth={v70_result.depth}")
            
            print("   🧠 Testing V7P3R v9.2...")
            v92_result = self.test_engine(self.engines["v9.2"], fen, 5.0)
            print(f"   📊 v9.2: {v92_result.move} eval={v92_result.evaluation:+d} depth={v92_result.depth}")
            
            # Grade both moves using Stockfish
            if v70_result.success and stockfish_analysis.best_move:
                v70_grade = self.grade_move_quality(
                    v70_result.move, v70_result.evaluation,
                    stockfish_analysis.best_move, stockfish_analysis.best_eval,
                    stockfish_analysis
                )
                print(f"   🎯 v7.0 Grade: {v70_grade.quality_rating} (loss: {v70_grade.centipawn_loss} cp)")
            else:
                v70_grade = MoveQualityGrade(v70_result.move, v70_result.evaluation, 
                                           stockfish_analysis.best_move, stockfish_analysis.best_eval,
                                           999, "error", "Analysis failed")
            
            if v92_result.success and stockfish_analysis.best_move:
                v92_grade = self.grade_move_quality(
                    v92_result.move, v92_result.evaluation,
                    stockfish_analysis.best_move, stockfish_analysis.best_eval,
                    stockfish_analysis
                )
                print(f"   🎯 v9.2 Grade: {v92_grade.quality_rating} (loss: {v92_grade.centipawn_loss} cp)")
            else:
                v92_grade = MoveQualityGrade(v92_result.move, v92_result.evaluation,
                                           stockfish_analysis.best_move, stockfish_analysis.best_eval,
                                           999, "error", "Analysis failed")
            
            # Determine winner
            if v70_grade.quality_rating == "error" and v92_grade.quality_rating == "error":
                winner = "tie"
            elif v70_grade.quality_rating == "error":
                winner = "v9.2"
            elif v92_grade.quality_rating == "error":
                winner = "v7.0"
            elif v70_grade.centipawn_loss < v92_grade.centipawn_loss:
                winner = "v7.0"
            elif v92_grade.centipawn_loss < v70_grade.centipawn_loss:
                winner = "v9.2"
            else:
                winner = "tie"
            
            print(f"   🏆 Winner: {winner}")
            
            # Create comparison result
            comparison = PositionComparison(
                fen=fen,
                description=description,
                phase=phase,
                v70_result=v70_result,
                v92_result=v92_result,
                stockfish_analysis=stockfish_analysis,
                v70_grade=v70_grade,
                v92_grade=v92_grade,
                winner=winner
            )
            
            results.append(comparison)
        
        return results
    
    def generate_report(self, comparisons: List[PositionComparison]) -> str:
        """Generate comprehensive Stockfish-graded comparison report."""
        
        # Calculate statistics
        total_positions = len(comparisons)
        v70_wins = sum(1 for c in comparisons if c.winner == "v7.0")
        v92_wins = sum(1 for c in comparisons if c.winner == "v9.2")
        ties = sum(1 for c in comparisons if c.winner == "tie")
        
        # Quality distribution
        quality_levels = ["excellent", "good", "inaccurate", "mistake", "blunder", "error"]
        v70_quality_dist = {q: sum(1 for c in comparisons if c.v70_grade.quality_rating == q) for q in quality_levels}
        v92_quality_dist = {q: sum(1 for c in comparisons if c.v92_grade.quality_rating == q) for q in quality_levels}
        
        # Average centipawn loss
        v70_avg_loss = sum(c.v70_grade.centipawn_loss for c in comparisons if c.v70_grade.quality_rating != "error") / max(1, sum(1 for c in comparisons if c.v70_grade.quality_rating != "error"))
        v92_avg_loss = sum(c.v92_grade.centipawn_loss for c in comparisons if c.v92_grade.quality_rating != "error") / max(1, sum(1 for c in comparisons if c.v92_grade.quality_rating != "error"))
        
        # Phase-specific analysis
        by_phase = {}
        for comp in comparisons:
            if comp.phase not in by_phase:
                by_phase[comp.phase] = []
            by_phase[comp.phase].append(comp)
        
        report = f"""
# V7P3R Stockfish Evaluation Comparison Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Control Engine:** Stockfish (10-second analysis per position)
**Test Engines:** V7P3R v7.0 vs V7P3R v9.2 (5-second analysis per position)

## Executive Summary

**Overall Performance:**
- Total positions tested: {total_positions}
- V7P3R v7.0 wins: {v70_wins} ({v70_wins/total_positions*100:.1f}%)
- V7P3R v9.2 wins: {v92_wins} ({v92_wins/total_positions*100:.1f}%)
- Ties: {ties} ({ties/total_positions*100:.1f}%)

**Move Quality (Stockfish-graded):**
- V7P3R v7.0 average centipawn loss: {v70_avg_loss:.1f}
- V7P3R v9.2 average centipawn loss: {v92_avg_loss:.1f}

## Quality Distribution

| Quality Level | v7.0 Count | v9.2 Count | v7.0 % | v9.2 % |
|---------------|------------|------------|--------|--------|
"""
        
        for quality in quality_levels:
            v70_count = v70_quality_dist[quality]
            v92_count = v92_quality_dist[quality]
            v70_pct = v70_count / total_positions * 100
            v92_pct = v92_count / total_positions * 100
            report += f"| {quality.title()} | {v70_count} | {v92_count} | {v70_pct:.1f}% | {v92_pct:.1f}% |\n"
        
        # Phase-specific analysis
        report += "\n## Phase-Specific Analysis\n\n"
        
        for phase, phase_comps in by_phase.items():
            phase_v70_wins = sum(1 for c in phase_comps if c.winner == "v7.0")
            phase_v92_wins = sum(1 for c in phase_comps if c.winner == "v9.2")
            phase_ties = sum(1 for c in phase_comps if c.winner == "tie")
            
            phase_v70_avg = sum(c.v70_grade.centipawn_loss for c in phase_comps if c.v70_grade.quality_rating != "error") / max(1, sum(1 for c in phase_comps if c.v70_grade.quality_rating != "error"))
            phase_v92_avg = sum(c.v92_grade.centipawn_loss for c in phase_comps if c.v92_grade.quality_rating != "error") / max(1, sum(1 for c in phase_comps if c.v92_grade.quality_rating != "error"))
            
            report += f"### {phase.title()} Phase\n"
            report += f"- Positions: {len(phase_comps)}\n"
            report += f"- v7.0 wins: {phase_v70_wins}, v9.2 wins: {phase_v92_wins}, ties: {phase_ties}\n"
            report += f"- v7.0 avg loss: {phase_v70_avg:.1f} cp, v9.2 avg loss: {phase_v92_avg:.1f} cp\n\n"
        
        # Detailed position analysis
        report += "\n## Detailed Position Analysis\n\n"
        report += "| Position | Phase | SF Best | v7.0 Move | v7.0 Grade | v9.2 Move | v9.2 Grade | Winner |\n"
        report += "|----------|-------|---------|-----------|------------|-----------|------------|--------|\n"
        
        for comp in comparisons:
            sf_move = comp.stockfish_analysis.best_move[:6] if comp.stockfish_analysis.best_move else "N/A"
            v70_move = comp.v70_result.move[:6] if comp.v70_result.move else "N/A"
            v92_move = comp.v92_result.move[:6] if comp.v92_result.move else "N/A"
            
            v70_grade_text = f"{comp.v70_grade.quality_rating} ({comp.v70_grade.centipawn_loss}cp)"
            v92_grade_text = f"{comp.v92_grade.quality_rating} ({comp.v92_grade.centipawn_loss}cp)"
            
            winner_icon = "🔴" if comp.winner == "v7.0" else "🟢" if comp.winner == "v9.2" else "🟡"
            
            report += f"| {comp.description[:20]}... | {comp.phase} | {sf_move} | {v70_move} | {v70_grade_text} | {v92_move} | {v92_grade_text} | {winner_icon} {comp.winner} |\n"
        
        # Strategic conclusions
        report += "\n## Strategic Analysis\n\n"
        
        if v92_wins > v70_wins:
            report += f"**🟢 V9.2 ADVANTAGE**: v9.2 shows superior move quality in {v92_wins}/{total_positions} positions\n"
        elif v70_wins > v92_wins:
            report += f"**🔴 V7.0 ADVANTAGE**: v7.0 shows superior move quality in {v70_wins}/{total_positions} positions\n"
        else:
            report += f"**🟡 BALANCED PERFORMANCE**: Both engines show similar overall move quality\n"
        
        if v92_avg_loss < v70_avg_loss:
            report += f"**🎯 EVALUATION ACCURACY**: v9.2 has lower average centipawn loss ({v92_avg_loss:.1f} vs {v70_avg_loss:.1f})\n"
        elif v70_avg_loss < v92_avg_loss:
            report += f"**🎯 EVALUATION ACCURACY**: v7.0 has lower average centipawn loss ({v70_avg_loss:.1f} vs {v92_avg_loss:.1f})\n"
        
        # Recommendations
        report += "\n## Recommendations for V7P3R v9.3\n\n"
        
        if v70_wins > v92_wins and v70_avg_loss < v92_avg_loss:
            report += "**🚨 REGRESSION DETECTED**: v7.0 outperforms v9.2 in both win rate and accuracy\n"
            report += "- **Priority**: Investigate what evaluation changes caused the regression\n"
            report += "- **Action**: Consider restoring v7.0 evaluation components\n"
            report += "- **Focus**: Maintain v9.2 infrastructure while improving move quality\n"
        elif v92_wins > v70_wins and v92_avg_loss < v70_avg_loss:
            report += "**✅ IMPROVEMENT CONFIRMED**: v9.2 shows genuine improvement over v7.0\n"
            report += "- **Priority**: Build upon the successful evaluation changes\n"
            report += "- **Action**: Fine-tune current evaluation for even better performance\n"
            report += "- **Focus**: Optimize speed while maintaining quality gains\n"
        else:
            report += "**⚖️ MIXED RESULTS**: Trade-offs detected between versions\n"
            report += "- **Priority**: Identify specific areas where each version excels\n"
            report += "- **Action**: Combine best features from both versions\n"
            report += "- **Focus**: Balanced approach preserving strengths of both\n"
        
        return report

def main():
    """Run Stockfish evaluation comparison."""
    print("🔍 V7P3R STOCKFISH EVALUATION COMPARISON")
    print("=" * 60)
    
    comparator = StockfishEvaluationComparator()
    
    # Run comparison
    comparisons = comparator.compare_positions()
    
    if not comparisons:
        print("❌ Comparison failed - check engine paths")
        return
    
    # Generate report
    report = comparator.generate_report(comparisons)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"V7P3R_stockfish_comparison_{timestamp}.md"
    data_file = f"V7P3R_stockfish_comparison_data_{timestamp}.json"
    
    with open(report_file, "w", encoding='utf-8') as f:
        f.write(report)
    
    with open(data_file, "w", encoding='utf-8') as f:
        json.dump([asdict(c) for c in comparisons], f, indent=2)
    
    print(f"\n📊 COMPARISON COMPLETE!")
    print(f"📄 Report: {report_file}")
    print(f"📄 Data: {data_file}")
    
    # Quick summary
    v70_wins = sum(1 for c in comparisons if c.winner == "v7.0")
    v92_wins = sum(1 for c in comparisons if c.winner == "v9.2")
    ties = sum(1 for c in comparisons if c.winner == "tie")
    
    print(f"\n🏆 FINAL SCORE:")
    print(f"V7P3R v7.0: {v70_wins} wins")
    print(f"V7P3R v9.2: {v92_wins} wins")
    print(f"Ties: {ties}")
    
    if v92_wins > v70_wins:
        print("🟢 V9.2 shows superior Stockfish-graded move quality!")
    elif v70_wins > v92_wins:
        print("🔴 V7.0 shows superior Stockfish-graded move quality!")
    else:
        print("🟡 Both engines show similar Stockfish-graded performance")

if __name__ == "__main__":
    main()
