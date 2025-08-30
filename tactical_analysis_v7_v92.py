#!/usr/bin/env python3
"""
V7P3R Tactical Analysis: v9.2 vs v7.0 Puzzle Challenge
Comprehensive themed puzzle testing to identify tactical strengths/weaknesses
"""

import os
import sys
import json
import subprocess
import time
import chess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics

@dataclass
class PuzzleResult:
    """Result for a single puzzle test."""
    puzzle_id: str
    rating: int
    themes: List[str]
    fen: str
    solution: str
    engine_move: str
    correct: bool
    evaluation: int
    depth: int
    time_taken: float
    notes: str = ""

@dataclass
class ThemeAnalysis:
    """Analysis for a specific tactical theme."""
    theme: str
    total_puzzles: int
    solved_puzzles: int
    success_rate: float
    avg_time: float
    avg_rating: float
    difficult_puzzles: List[str]  # Failed puzzle IDs
    
class TacticalPuzzleTester:
    """Test engines on themed tactical puzzles."""
    
    def __init__(self):
        self.puzzle_sets = {
            # Basic tactical patterns
            "pin": [
                ("8/8/8/3r4/8/3R4/3K4/8 w - - 0 1", "d3d5", 1200, "Pin the rook"),
                ("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4", "c4f7", 1400, "Pin to king"),
                ("rnbqkb1r/ppp2ppp/3p1n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 4", "c4f7", 1300, "Absolute pin"),
            ],
            
            "fork": [
                ("8/8/8/3k4/8/8/3N4/3K4 w - - 0 1", "d2c4", 1000, "Knight fork"),
                ("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP1NPPP/R1BQK2R w KQkq - 6 5", "f3e5", 1300, "Knight fork attack"),
                ("8/8/8/8/3k4/8/2N5/2K5 w - - 0 1", "c2e3", 1100, "Simple knight fork"),
            ],
            
            "skewer": [
                ("8/8/8/3kr3/8/8/3R4/3K4 w - - 0 1", "d2d5", 1200, "Back rank skewer"),
                ("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "a1a8", 1400, "Rook skewer"),
                ("8/8/8/2qk4/8/8/2Q5/2K5 w - - 0 1", "c2c5", 1300, "Queen skewer"),
            ],
            
            "discovery": [
                ("rnbqkb1r/pppp1ppp/4pn2/8/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 2 3", "d4d5", 1400, "Discovery attack"),
                ("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P4/PPP1NPPP/RNBQK2R w KQkq - 4 4", "e2f4", 1500, "Discovery check"),
            ],
            
            "mate_in_1": [
                ("rnbqkb1r/pppp1ppp/4pn2/8/3PP3/8/PPP1NPPP/RNBQKB1R w KQkq - 2 3", "f1c4", 800, "Back rank mate threat"),
                ("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4", "h5f7", 1000, "Smothered mate"),
                ("8/8/8/8/8/8/6k1/5Q1K w - - 0 1", "f1f7", 600, "Simple mate"),
            ],
            
            "mate_in_2": [
                ("r1bqkb1r/pppp1Q1p/2n2np1/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 5", "f7f8", 1400, "Queen sacrifice mate"),
                ("6k1/6p1/6K1/8/8/8/6Q1/8 w - - 0 1", "g2g7", 1200, "Queen mate in 2"),
            ],
            
            "sacrifice": [
                ("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4", "h5f7", 1600, "Queen sacrifice"),
                ("rnbqkb1r/ppp2ppp/3p1n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 4", "f3e5", 1500, "Knight sacrifice"),
            ],
            
            "deflection": [
                ("8/8/8/3r1k2/8/3R4/8/3K4 w - - 0 1", "d3d5", 1300, "Deflection tactic"),
                ("r2qk2r/ppp2ppp/2n1bn2/2bpp3/2B1P3/3P1N2/PPP1NPPP/R1BQK2R w KQkq - 6 6", "c4f7", 1400, "Deflection attack"),
            ],
            
            "clearance": [
                ("rnbqk1nr/pppp1ppp/4p3/2b5/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 2 3", "c4f7", 1500, "Line clearance"),
            ],
            
            "zugzwang": [
                ("8/8/3k4/3p4/3K4/8/8/8 w - - 0 1", "d4c5", 1800, "King zugzwang"),
            ]
        }
    
    def test_engine(self, engine_path: str, fen: str, time_limit: float = 3.0) -> Tuple[str, int, int, float]:
        """Test engine on a single position."""
        try:
            process = subprocess.Popen(
                [engine_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            if not process.stdin or not process.stdout:
                return "", 0, 0, 0.0
            
            start_time = time.time()
            
            # UCI handshake
            process.stdin.write("uci\n")
            process.stdin.flush()
            
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
                        elif part == "score" and i+1 < len(parts):
                            if parts[i+1] == "cp" and i+2 < len(parts):
                                try:
                                    evaluation = int(parts[i+2])
                                except:
                                    pass
                            elif parts[i+1] == "mate" and i+2 < len(parts):
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
            return best_move, evaluation, depth, total_time
            
        except Exception as e:
            return "", 0, 0, 0.0
    
    def run_themed_analysis(self, engine_path: str, engine_name: str) -> Tuple[Dict[str, ThemeAnalysis], List[PuzzleResult]]:
        """Run complete themed puzzle analysis for an engine."""
        print(f"\n🧩 Running themed puzzle analysis for {engine_name}")
        print("=" * 60)
        
        theme_results = {}
        all_results = []
        
        for theme, puzzles in self.puzzle_sets.items():
            print(f"\n🎯 Testing {theme} puzzles ({len(puzzles)} puzzles)...")
            
            theme_successes = 0
            theme_times = []
            theme_ratings = []
            failed_puzzles = []
            
            for i, (fen, solution, rating, description) in enumerate(puzzles, 1):
                print(f"  Puzzle {i}/{len(puzzles)}: {description}")
                
                best_move, evaluation, depth, time_taken = self.test_engine(engine_path, fen, 3.0)
                correct = best_move == solution
                
                if correct:
                    theme_successes += 1
                    print(f"    ✅ Correct: {best_move} (eval: {evaluation:+d}, depth: {depth})")
                else:
                    failed_puzzles.append(f"{i}: {description}")
                    print(f"    ❌ Wrong: {best_move} (expected: {solution})")
                
                theme_times.append(time_taken)
                theme_ratings.append(rating)
                
                # Store detailed result
                result = PuzzleResult(
                    puzzle_id=f"{theme}_{i}",
                    rating=rating,
                    themes=[theme],
                    fen=fen,
                    solution=solution,
                    engine_move=best_move,
                    correct=correct,
                    evaluation=evaluation,
                    depth=depth,
                    time_taken=time_taken,
                    notes=description
                )
                all_results.append(result)
            
            # Calculate theme statistics
            success_rate = (theme_successes / len(puzzles)) * 100
            avg_time = statistics.mean(theme_times) if theme_times else 0
            avg_rating = statistics.mean(theme_ratings) if theme_ratings else 0
            
            theme_analysis = ThemeAnalysis(
                theme=theme,
                total_puzzles=len(puzzles),
                solved_puzzles=theme_successes,
                success_rate=success_rate,
                avg_time=avg_time,
                avg_rating=avg_rating,
                difficult_puzzles=failed_puzzles
            )
            
            theme_results[theme] = theme_analysis
            
            print(f"    📊 {theme}: {theme_successes}/{len(puzzles)} ({success_rate:.1f}%)")
        
        return theme_results, all_results
    
    def generate_analysis_report(self, engine_name: str, theme_results: Dict[str, ThemeAnalysis], 
                               all_results: List[PuzzleResult]) -> str:
        """Generate comprehensive analysis report."""
        
        report = f"""
# V7P3R Tactical Analysis Report: {engine_name}
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
Total puzzles tested: {len(all_results)}
Overall success rate: {(sum(r.correct for r in all_results) / len(all_results) * 100):.1f}%
Average time per puzzle: {statistics.mean([r.time_taken for r in all_results]):.2f}s
Average puzzle rating: {statistics.mean([r.rating for r in all_results]):.0f}

## Themed Performance Analysis

"""
        
        # Sort themes by success rate
        sorted_themes = sorted(theme_results.items(), key=lambda x: x[1].success_rate, reverse=True)
        
        report += "| Theme | Success Rate | Puzzles Solved | Avg Time | Avg Rating | Difficulty |\n"
        report += "|-------|--------------|----------------|----------|------------|------------|\n"
        
        for theme, analysis in sorted_themes:
            difficulty = "🟢 Easy" if analysis.success_rate >= 80 else "🟡 Medium" if analysis.success_rate >= 50 else "🔴 Hard"
            report += f"| {theme} | {analysis.success_rate:.1f}% | {analysis.solved_puzzles}/{analysis.total_puzzles} | {analysis.avg_time:.2f}s | {analysis.avg_rating:.0f} | {difficulty} |\n"
        
        report += "\n## Detailed Theme Analysis\n\n"
        
        for theme, analysis in sorted_themes:
            report += f"### {theme.title()} ({analysis.success_rate:.1f}%)\n"
            
            if analysis.success_rate >= 80:
                report += f"**✅ STRENGTH**: Excellent performance on {theme} tactics\n"
            elif analysis.success_rate >= 50:
                report += f"**⚠️ MODERATE**: Room for improvement on {theme} tactics\n"
            else:
                report += f"**❌ WEAKNESS**: Poor performance on {theme} tactics\n"
            
            if analysis.difficult_puzzles:
                report += f"**Failed puzzles**: {', '.join(analysis.difficult_puzzles)}\n"
            
            report += f"- Solved: {analysis.solved_puzzles}/{analysis.total_puzzles} puzzles\n"
            report += f"- Average time: {analysis.avg_time:.2f}s\n"
            report += f"- Average rating: {analysis.avg_rating:.0f}\n\n"
        
        # Identify strengths and weaknesses
        strengths = [theme for theme, analysis in theme_results.items() if analysis.success_rate >= 80]
        moderate = [theme for theme, analysis in theme_results.items() if 50 <= analysis.success_rate < 80]
        weaknesses = [theme for theme, analysis in theme_results.items() if analysis.success_rate < 50]
        
        report += "## Strategic Assessment\n\n"
        
        if strengths:
            report += f"**🎯 TACTICAL STRENGTHS**:\n"
            for theme in strengths:
                report += f"- {theme.title()}: {theme_results[theme].success_rate:.1f}%\n"
            report += "\n"
        
        if moderate:
            report += f"**⚖️ MODERATE PERFORMANCE**:\n"
            for theme in moderate:
                report += f"- {theme.title()}: {theme_results[theme].success_rate:.1f}%\n"
            report += "\n"
        
        if weaknesses:
            report += f"**⚠️ TACTICAL WEAKNESSES**:\n"
            for theme in weaknesses:
                report += f"- {theme.title()}: {theme_results[theme].success_rate:.1f}%\n"
            report += "\n"
        
        return report

def main():
    """Run tactical analysis comparison."""
    print("🔍 V7P3R TACTICAL ANALYSIS: v9.2 vs v7.0")
    print("=" * 60)
    
    # Engine paths
    engines_dir = Path("engines/V7P3R")
    v70_path = engines_dir / "V7P3R_v7.0.exe"
    v92_path = engines_dir / "V7P3R_v9.2.exe"
    
    # Verify engines exist
    if not v70_path.exists():
        print(f"❌ V7P3R v7.0 not found: {v70_path}")
        return
    
    if not v92_path.exists():
        print(f"❌ V7P3R v9.2 not found: {v92_path}")
        return
    
    print(f"✅ V7P3R v7.0: {v70_path}")
    print(f"✅ V7P3R v9.2: {v92_path}")
    
    tester = TacticalPuzzleTester()
    
    # Test both engines
    v70_results, v70_all = tester.run_themed_analysis(str(v70_path), "V7P3R v7.0")
    v92_results, v92_all = tester.run_themed_analysis(str(v92_path), "V7P3R v9.2")
    
    # Generate reports
    v70_report = tester.generate_analysis_report("V7P3R v7.0", v70_results, v70_all)
    v92_report = tester.generate_analysis_report("V7P3R v9.2", v92_results, v92_all)
    
    # Save reports
    with open("V7P3R_v7.0_tactical_analysis.md", "w", encoding='utf-8') as f:
        f.write(v70_report)
    
    with open("V7P3R_v9.2_tactical_analysis.md", "w", encoding='utf-8') as f:
        f.write(v92_report)
    
    print(f"\n📊 Analysis complete!")
    print(f"📄 Reports saved:")
    print(f"  - V7P3R_v7.0_tactical_analysis.md")
    print(f"  - V7P3R_v9.2_tactical_analysis.md")
    
    # Generate comparison summary
    print(f"\n🔄 QUICK COMPARISON SUMMARY:")
    print(f"=" * 60)
    
    for theme in v70_results.keys():
        v70_rate = v70_results[theme].success_rate
        v92_rate = v92_results[theme].success_rate
        diff = v92_rate - v70_rate
        
        if diff > 10:
            status = "🟢 v9.2 BETTER"
        elif diff < -10:
            status = "🔴 v7.0 BETTER"
        else:
            status = "🟡 SIMILAR"
        
        print(f"{theme:12} | v7.0: {v70_rate:5.1f}% | v9.2: {v92_rate:5.1f}% | {status}")

if __name__ == "__main__":
    main()
