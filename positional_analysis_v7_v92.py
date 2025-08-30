#!/usr/bin/env python3
"""
V7P3R Positional Analysis: v7.0 vs v9.2 
Analyzes positional understanding across game phases
"""

import subprocess
import time
import chess
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

@dataclass
class PositionAnalysis:
    """Analysis result for a single position."""
    fen: str
    description: str
    phase: str  # opening, middlegame, endgame
    v70_move: str
    v70_eval: int
    v70_depth: int
    v70_time: float
    v92_move: str
    v92_eval: int
    v92_depth: int
    v92_time: float
    eval_diff: int
    moves_agree: bool
    analysis_notes: str = ""

class PositionalAnalyzer:
    """Analyze positional understanding between engine versions."""
    
    def __init__(self):
        self.test_positions = {
            "opening": [
                {
                    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                    "description": "Starting position - development priority",
                    "key_concepts": ["development", "center_control", "king_safety"]
                },
                {
                    "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
                    "description": "King's pawn opening - center tension",
                    "key_concepts": ["center_control", "piece_activity"]
                },
                {
                    "fen": "rnbqkb1r/pppp1ppp/4pn2/8/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 2 3",
                    "description": "French Defense - space advantage",
                    "key_concepts": ["space_advantage", "pawn_structure", "piece_placement"]
                },
                {
                    "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
                    "description": "Italian Game setup - piece activity",
                    "key_concepts": ["piece_activity", "development", "center_control"]
                }
            ],
            
            "middlegame": [
                {
                    "fen": "r2q1rk1/ppp2ppp/2n1bn2/2bpP3/3P4/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 10",
                    "description": "Complex middlegame - tactical opportunities",
                    "key_concepts": ["tactical_awareness", "piece_coordination", "king_safety"]
                },
                {
                    "fen": "r1bq1rk1/pp3ppp/2n1pn2/3p4/1bPP4/2N1PN2/PP2BPPP/R1BQK2R w KQ - 2 8",
                    "description": "Queen's Gambit Declined - positional pressure",
                    "key_concepts": ["positional_pressure", "pawn_structure", "piece_activity"]
                },
                {
                    "fen": "r2qk2r/ppp2ppp/2n1bn2/2bpp3/2B1P3/3P1N2/PPP1NPPP/R1BQK2R w KQkq - 6 6",
                    "description": "Open center - piece activity crucial",
                    "key_concepts": ["piece_activity", "center_control", "tactical_motifs"]
                },
                {
                    "fen": "r3r1k1/pppq1ppp/3p1n2/4p3/4P3/2NP1Q2/PPP2PPP/R4RK1 w - - 0 12",
                    "description": "Middlegame with heavy pieces - coordination",
                    "key_concepts": ["piece_coordination", "heavy_piece_activity", "king_safety"]
                }
            ],
            
            "endgame": [
                {
                    "fen": "8/4kp2/6p1/4K3/6P1/8/5P2/8 w - - 0 40",
                    "description": "King and pawn endgame - opposition",
                    "key_concepts": ["opposition", "pawn_promotion", "king_activity"]
                },
                {
                    "fen": "8/8/4k3/4p3/4K3/8/8/8 w - - 0 50",
                    "description": "Simple king endgame - zugzwang concepts",
                    "key_concepts": ["zugzwang", "king_activity", "tempo"]
                },
                {
                    "fen": "8/8/8/4k3/4p3/4K3/8/8 b - - 0 60",
                    "description": "Pawn endgame - breakthrough",
                    "key_concepts": ["pawn_breakthrough", "king_support", "calculation"]
                },
                {
                    "fen": "4k3/8/4K3/8/8/8/6Q1/8 w - - 0 70",
                    "description": "Queen vs King - basic mate",
                    "key_concepts": ["basic_mates", "queen_technique", "king_restriction"]
                },
                {
                    "fen": "8/8/8/8/8/3k4/3R4/3K4 w - - 0 80",
                    "description": "Rook endgame - cutting off king",
                    "key_concepts": ["rook_technique", "king_restriction", "endgame_theory"]
                }
            ],
            
            "tactical": [
                {
                    "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP1NPPP/R1BQK2R w KQkq - 6 5",
                    "description": "Pin and fork opportunities",
                    "key_concepts": ["pins", "forks", "tactical_vision"]
                },
                {
                    "fen": "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/2B1P3/2NP1N2/PPP1BPPP/R2Q1RK1 w - - 0 8",
                    "description": "Discovery attack potential",
                    "key_concepts": ["discovery", "piece_coordination", "tactical_calculation"]
                },
                {
                    "fen": "r1bq1rk1/pp3ppp/2n1pn2/2pp4/1bPP4/2N1PN2/PP2BPPP/R1BQK2R w KQ - 0 9",
                    "description": "Deflection and decoy themes",
                    "key_concepts": ["deflection", "decoy", "piece_overloading"]
                }
            ]
        }
    
    def test_engine_position(self, engine_path: str, fen: str, time_limit: float = 5.0) -> Tuple[str, int, int, float]:
        """Test engine on a position with extended analysis time."""
        try:
            process = subprocess.Popen(
                [engine_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if not process.stdin or not process.stdout:
                return "", 0, 0, 0.0
            
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
            return best_move, evaluation, depth, total_time
            
        except Exception as e:
            return "", 0, 0, 0.0
    
    def analyze_position_set(self, phase: str, positions: List[Dict], v70_path: str, v92_path: str) -> List[PositionAnalysis]:
        """Analyze a set of positions for a specific game phase."""
        results = []
        
        print(f"\n🔍 Analyzing {phase.upper()} positions...")
        print("=" * 60)
        
        for i, pos_data in enumerate(positions, 1):
            fen = pos_data["fen"]
            description = pos_data["description"]
            key_concepts = pos_data["key_concepts"]
            
            print(f"\n{i}. {description}")
            print(f"   Key concepts: {', '.join(key_concepts)}")
            print(f"   FEN: {fen}")
            
            # Test both engines
            v70_move, v70_eval, v70_depth, v70_time = self.test_engine_position(v70_path, fen, 5.0)
            v92_move, v92_eval, v92_depth, v92_time = self.test_engine_position(v92_path, fen, 5.0)
            
            eval_diff = v92_eval - v70_eval
            moves_agree = v70_move == v92_move
            
            print(f"   v7.0:  {v70_move:8} eval={v70_eval:+6d} depth={v70_depth} time={v70_time:.2f}s")
            print(f"   v9.2:  {v92_move:8} eval={v92_eval:+6d} depth={v92_depth} time={v92_time:.2f}s")
            
            # Analysis notes
            notes = []
            if moves_agree:
                notes.append("✅ Move agreement")
            else:
                notes.append("⚠️ Move disagreement")
            
            if abs(eval_diff) > 100:
                if eval_diff > 0:
                    notes.append(f"🟢 v9.2 more optimistic (+{eval_diff})")
                else:
                    notes.append(f"🔴 v7.0 more optimistic (+{-eval_diff})")
            else:
                notes.append("✅ Similar evaluation")
            
            analysis_notes = " | ".join(notes)
            print(f"   Analysis: {analysis_notes}")
            
            # Create analysis result
            result = PositionAnalysis(
                fen=fen,
                description=description,
                phase=phase,
                v70_move=v70_move,
                v70_eval=v70_eval,
                v70_depth=v70_depth,
                v70_time=v70_time,
                v92_move=v92_move,
                v92_eval=v92_eval,
                v92_depth=v92_depth,
                v92_time=v92_time,
                eval_diff=eval_diff,
                moves_agree=moves_agree,
                analysis_notes=analysis_notes
            )
            
            results.append(result)
        
        return results
    
    def generate_comprehensive_report(self, all_results: List[PositionAnalysis]) -> str:
        """Generate a comprehensive positional analysis report."""
        
        # Group results by phase
        by_phase = {}
        for result in all_results:
            if result.phase not in by_phase:
                by_phase[result.phase] = []
            by_phase[result.phase].append(result)
        
        report = f"""
# V7P3R Positional Analysis Report: v7.0 vs v9.2
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

Total positions analyzed: {len(all_results)}
Move agreement rate: {sum(1 for r in all_results if r.moves_agree) / len(all_results) * 100:.1f}%
Average evaluation difference: {sum(abs(r.eval_diff) for r in all_results) / len(all_results):.0f} centipawns

### Evaluation Preferences
- v7.0 more optimistic: {sum(1 for r in all_results if r.eval_diff < -100)} positions
- v9.2 more optimistic: {sum(1 for r in all_results if r.eval_diff > 100)} positions
- Similar evaluations: {sum(1 for r in all_results if abs(r.eval_diff) <= 100)} positions

"""
        
        # Phase-by-phase analysis
        for phase, results in by_phase.items():
            report += f"\n## {phase.title()} Analysis\n\n"
            
            move_agreement = sum(1 for r in results if r.moves_agree) / len(results) * 100
            avg_eval_diff = sum(abs(r.eval_diff) for r in results) / len(results)
            v70_better_count = sum(1 for r in results if r.eval_diff < -100)
            v92_better_count = sum(1 for r in results if r.eval_diff > 100)
            
            report += f"**Phase Statistics:**\n"
            report += f"- Positions analyzed: {len(results)}\n"
            report += f"- Move agreement: {move_agreement:.1f}%\n"
            report += f"- Average eval difference: {avg_eval_diff:.0f} cp\n"
            report += f"- v7.0 more optimistic: {v70_better_count} positions\n"
            report += f"- v9.2 more optimistic: {v92_better_count} positions\n\n"
            
            # Performance assessment
            if move_agreement >= 80:
                report += "**✅ HIGH AGREEMENT**: Both engines understand this phase similarly\n\n"
            elif move_agreement >= 60:
                report += "**⚠️ MODERATE AGREEMENT**: Some differences in understanding\n\n"
            else:
                report += "**❌ LOW AGREEMENT**: Significant differences in positional understanding\n\n"
            
            # Detailed position analysis
            report += "**Position Details:**\n\n"
            report += "| Description | v7.0 Move | v7.0 Eval | v9.2 Move | v9.2 Eval | Diff | Agreement |\n"
            report += "|-------------|-----------|-----------|-----------|-----------|------|----------|\n"
            
            for result in results:
                agreement_icon = "✅" if result.moves_agree else "❌"
                report += f"| {result.description[:30]} | {result.v70_move} | {result.v70_eval:+d} | {result.v92_move} | {result.v92_eval:+d} | {result.eval_diff:+d} | {agreement_icon} |\n"
            
            report += "\n"
        
        # Strategic insights
        report += "\n## Strategic Insights\n\n"
        
        # Find patterns
        opening_results = by_phase.get("opening", [])
        middlegame_results = by_phase.get("middlegame", [])
        endgame_results = by_phase.get("endgame", [])
        tactical_results = by_phase.get("tactical", [])
        
        if opening_results:
            opening_agreement = sum(1 for r in opening_results if r.moves_agree) / len(opening_results) * 100
            if opening_agreement >= 75:
                report += "**🟢 OPENING STRENGTH**: Both engines show good opening understanding\n"
            else:
                report += "**🔴 OPENING CONCERN**: Significant opening move differences suggest evaluation changes\n"
        
        if middlegame_results:
            middlegame_agreement = sum(1 for r in middlegame_results if r.moves_agree) / len(middlegame_results) * 100
            if middlegame_agreement >= 75:
                report += "**🟢 MIDDLEGAME STRENGTH**: Consistent middlegame evaluation\n"
            else:
                report += "**🔴 MIDDLEGAME CONCERN**: Middlegame understanding has diverged\n"
        
        if endgame_results:
            endgame_agreement = sum(1 for r in endgame_results if r.moves_agree) / len(endgame_results) * 100
            if endgame_agreement >= 75:
                report += "**🟢 ENDGAME STRENGTH**: Strong endgame technique preserved\n"
            else:
                report += "**🔴 ENDGAME CONCERN**: Endgame evaluation needs attention\n"
        
        if tactical_results:
            tactical_agreement = sum(1 for r in tactical_results if r.moves_agree) / len(tactical_results) * 100
            if tactical_agreement >= 75:
                report += "**🟢 TACTICAL STRENGTH**: Tactical pattern recognition maintained\n"
            else:
                report += "**🔴 TACTICAL CONCERN**: Tactical evaluation has regressed\n"
        
        # Recommendations for v9.3
        report += "\n## Recommendations for V7P3R v9.3\n\n"
        
        overall_agreement = sum(1 for r in all_results if r.moves_agree) / len(all_results) * 100
        
        if overall_agreement < 60:
            report += "**🚨 CRITICAL**: Major evaluation function changes needed\n"
            report += "- Investigate core evaluation differences\n"
            report += "- Consider restoring v7.0 evaluation weights\n"
            report += "- Review piece-square table modifications\n\n"
        
        # Phase-specific recommendations
        phase_agreements = {
            "opening": sum(1 for r in opening_results if r.moves_agree) / len(opening_results) * 100 if opening_results else 100,
            "middlegame": sum(1 for r in middlegame_results if r.moves_agree) / len(middlegame_results) * 100 if middlegame_results else 100,
            "endgame": sum(1 for r in endgame_results if r.moves_agree) / len(endgame_results) * 100 if endgame_results else 100,
            "tactical": sum(1 for r in tactical_results if r.moves_agree) / len(tactical_results) * 100 if tactical_results else 100
        }
        
        weakest_phase = min(phase_agreements.items(), key=lambda x: x[1])
        
        if weakest_phase[1] < 70:
            report += f"**🎯 PRIORITY FOCUS**: {weakest_phase[0].title()} evaluation needs improvement ({weakest_phase[1]:.1f}% agreement)\n"
            
            if weakest_phase[0] == "tactical":
                report += "- Restore aggressive tactical pattern recognition\n"
                report += "- Enhance forcing move evaluation\n"
                report += "- Improve tactical search depth\n"
            elif weakest_phase[0] == "endgame":
                report += "- Review endgame evaluation tables\n"
                report += "- Enhance king activity evaluation\n"
                report += "- Improve pawn structure assessment\n"
            elif weakest_phase[0] == "opening":
                report += "- Review opening piece values\n"
                report += "- Enhance development evaluation\n"
                report += "- Improve center control assessment\n"
            elif weakest_phase[0] == "middlegame":
                report += "- Balance tactical vs positional evaluation\n"
                report += "- Improve piece coordination assessment\n"
                report += "- Enhance king safety evaluation\n"
        
        return report

def main():
    """Run comprehensive positional analysis."""
    print("🔍 V7P3R COMPREHENSIVE POSITIONAL ANALYSIS")
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
    
    analyzer = PositionalAnalyzer()
    all_results = []
    
    # Analyze each phase
    for phase, positions in analyzer.test_positions.items():
        phase_results = analyzer.analyze_position_set(phase, positions, str(v70_path), str(v92_path))
        all_results.extend(phase_results)
    
    # Generate comprehensive report
    report = analyzer.generate_comprehensive_report(all_results)
    
    # Save report
    report_file = "V7P3R_positional_analysis_v7.0_vs_v9.2.md"
    with open(report_file, "w", encoding='utf-8') as f:
        f.write(report)
    
    # Save detailed JSON data
    json_data = [asdict(result) for result in all_results]
    with open("V7P3R_positional_analysis_data.json", "w", encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"\n📊 ANALYSIS COMPLETE!")
    print(f"📄 Report saved: {report_file}")
    print(f"📄 Data saved: V7P3R_positional_analysis_data.json")
    
    # Quick summary
    move_agreement = sum(1 for r in all_results if r.moves_agree) / len(all_results) * 100
    print(f"\n🎯 QUICK SUMMARY:")
    print(f"Overall move agreement: {move_agreement:.1f}%")
    print(f"Total positions analyzed: {len(all_results)}")
    
    if move_agreement >= 80:
        print("✅ High agreement - engines are very similar")
    elif move_agreement >= 60:
        print("⚠️ Moderate agreement - some evaluation differences")
    else:
        print("❌ Low agreement - significant evaluation changes")

if __name__ == "__main__":
    main()
