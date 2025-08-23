#!/usr/bin/env python3
"""
🎯 Advanced Challenge Types for Engine Battle Framework
======================================================

Additional challenge types beyond traditional games:
- Puzzle solving challenges
- Depth analysis challenges  
- Position evaluation challenges
- Tactical pattern recognition
- Endgame challenges
"""

import asyncio
import time
import random
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from engine_battle_framework import (
    ChallengeBase, ChallengeType, ChallengeResult, BattleStatus, UCIEngine
)

class PuzzleSolveChallenge(ChallengeBase):
    """Chess puzzle solving challenge"""
    
    def __init__(self):
        super().__init__(ChallengeType.PUZZLE_SOLVE)
        
        # Famous tactical puzzles (FEN, best move, description)
        self.puzzles = [
            {
                "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 4",
                "best_moves": ["Nxe4"],
                "description": "Fork the bishop and pawn",
                "difficulty": "easy"
            },
            {
                "fen": "rnbqkb1r/ppp2ppp/4pn2/3p4/2PP4/2N2N2/PP2PPPP/R1BQKB1R b KQkq - 0 4",
                "best_moves": ["dxc4"],
                "description": "Capture the pawn",
                "difficulty": "easy"
            },
            {
                "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 6",
                "best_moves": ["Ng5", "Nd4"],
                "description": "Attack weak squares",
                "difficulty": "medium"
            },
            {
                "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
                "best_moves": ["f5"],
                "description": "King's Gambit defense",
                "difficulty": "medium"
            },
            {
                "fen": "r2qkb1r/ppp2ppp/2n1bn2/3pp3/3PP3/2N2N2/PPP2PPP/R1BQKB1R w KQkq - 2 6",
                "best_moves": ["exd5"],
                "description": "Central tension",
                "difficulty": "hard"
            }
        ]
    
    async def execute(self, engine1: UCIEngine, engine2: UCIEngine, **kwargs) -> ChallengeResult:
        """Execute puzzle solving challenge"""
        time_limit = kwargs.get('time_limit', 15.0)
        puzzle_count = kwargs.get('puzzle_count', min(len(self.puzzles), 5))
        
        start_time = time.time()
        challenge_id = f"puzzle_{int(start_time)}"
        
        self.logger.info(f"Starting puzzle challenge: {engine1.config.name} vs {engine2.config.name}")
        
        engine1_results = []
        engine2_results = []
        
        try:
            # Select random puzzles
            selected_puzzles = random.sample(self.puzzles, puzzle_count)
            
            for i, puzzle in enumerate(selected_puzzles):
                self.logger.info(f"Puzzle {i + 1}/{puzzle_count}: {puzzle['description']}")
                
                # Engine 1 attempt
                move1, metrics1 = await engine1.get_best_move(f"fen {puzzle['fen']}", time_limit)
                correct1 = move1 in puzzle['best_moves'] if move1 else False
                solve_time1 = metrics1.get("search_time", time_limit)
                
                engine1_results.append({
                    "puzzle": i,
                    "move": move1,
                    "correct": correct1,
                    "time": solve_time1,
                    "depth": metrics1.get("depth", 0),
                    "nodes": metrics1.get("nodes", 0)
                })
                
                # Engine 2 attempt
                move2, metrics2 = await engine2.get_best_move(f"fen {puzzle['fen']}", time_limit)
                correct2 = move2 in puzzle['best_moves'] if move2 else False
                solve_time2 = metrics2.get("search_time", time_limit)
                
                engine2_results.append({
                    "puzzle": i,
                    "move": move2,
                    "correct": correct2,
                    "time": solve_time2,
                    "depth": metrics2.get("depth", 0),
                    "nodes": metrics2.get("nodes", 0)
                })
            
            # Calculate scores
            engine1_score = sum(1 for r in engine1_results if r["correct"])
            engine2_score = sum(1 for r in engine2_results if r["correct"])
            
            # Determine winner
            if engine1_score > engine2_score:
                winner = engine1.config.name
            elif engine2_score > engine1_score:
                winner = engine2.config.name
            else:
                # Tie-breaker: faster average solve time for correct answers
                correct1_times = [r["time"] for r in engine1_results if r["correct"]]
                correct2_times = [r["time"] for r in engine2_results if r["correct"]]
                
                avg_time1 = sum(correct1_times) / len(correct1_times) if correct1_times else float('inf')
                avg_time2 = sum(correct2_times) / len(correct2_times) if correct2_times else float('inf')
                
                winner = engine1.config.name if avg_time1 < avg_time2 else engine2.config.name
            
            execution_time = time.time() - start_time
            
            return ChallengeResult(
                challenge_id=challenge_id,
                challenge_type=self.challenge_type,
                engine1=engine1.config.name,
                engine2=engine2.config.name,
                winner=winner,
                result_details={
                    "puzzles": selected_puzzles,
                    "engine1_results": engine1_results,
                    "engine2_results": engine2_results,
                    "engine1_score": engine1_score,
                    "engine2_score": engine2_score,
                    "total_puzzles": puzzle_count
                },
                execution_time=execution_time,
                timestamp=datetime.now(),
                status=BattleStatus.COMPLETED,
                metrics={
                    "accuracy_engine1": engine1_score / puzzle_count,
                    "accuracy_engine2": engine2_score / puzzle_count,
                    "score_difference": abs(engine1_score - engine2_score)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in puzzle challenge: {e}")
            return ChallengeResult(
                challenge_id=challenge_id,
                challenge_type=self.challenge_type,
                engine1=engine1.config.name,
                engine2=engine2.config.name,
                winner=None,
                result_details={"error": str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
                status=BattleStatus.FAILED
            )

class DepthChallenge(ChallengeBase):
    """Depth analysis challenge - who can search deeper in limited time"""
    
    def __init__(self):
        super().__init__(ChallengeType.DEPTH_CHALLENGE)
    
    async def execute(self, engine1: UCIEngine, engine2: UCIEngine, **kwargs) -> ChallengeResult:
        """Execute depth challenge"""
        positions = kwargs.get('positions', [
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",  # Starting position
            "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 4",  # Complex middle game
            "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"  # Endgame position
        ])
        time_limit = kwargs.get('time_limit', 10.0)
        
        start_time = time.time()
        challenge_id = f"depth_{int(start_time)}"
        
        self.logger.info(f"Starting depth challenge: {engine1.config.name} vs {engine2.config.name}")
        
        engine1_depths = []
        engine2_depths = []
        engine1_nodes = []
        engine2_nodes = []
        
        try:
            for i, position in enumerate(positions):
                self.logger.info(f"Depth test position {i + 1}/{len(positions)}")
                
                # Test engine1
                move1, metrics1 = await engine1.get_best_move(f"fen {position}", time_limit)
                engine1_depths.append(metrics1.get("depth", 0))
                engine1_nodes.append(metrics1.get("nodes", 0))
                
                # Test engine2
                move2, metrics2 = await engine2.get_best_move(f"fen {position}", time_limit)
                engine2_depths.append(metrics2.get("depth", 0))
                engine2_nodes.append(metrics2.get("nodes", 0))
            
            # Calculate results
            avg_depth1 = sum(engine1_depths) / len(engine1_depths)
            avg_depth2 = sum(engine2_depths) / len(engine2_depths)
            total_nodes1 = sum(engine1_nodes)
            total_nodes2 = sum(engine2_nodes)
            
            # Winner is determined by average depth
            winner = engine1.config.name if avg_depth1 > avg_depth2 else engine2.config.name
            
            execution_time = time.time() - start_time
            
            return ChallengeResult(
                challenge_id=challenge_id,
                challenge_type=self.challenge_type,
                engine1=engine1.config.name,
                engine2=engine2.config.name,
                winner=winner,
                result_details={
                    "positions": positions,
                    "engine1_depths": engine1_depths,
                    "engine2_depths": engine2_depths,
                    "engine1_nodes": engine1_nodes,
                    "engine2_nodes": engine2_nodes,
                    "avg_depth_engine1": avg_depth1,
                    "avg_depth_engine2": avg_depth2,
                    "total_nodes_engine1": total_nodes1,
                    "total_nodes_engine2": total_nodes2
                },
                execution_time=execution_time,
                timestamp=datetime.now(),
                status=BattleStatus.COMPLETED,
                metrics={
                    "depth_advantage": abs(avg_depth1 - avg_depth2),
                    "max_depth": max(max(engine1_depths), max(engine2_depths)),
                    "nodes_per_second_engine1": total_nodes1 / execution_time if execution_time > 0 else 0,
                    "nodes_per_second_engine2": total_nodes2 / execution_time if execution_time > 0 else 0
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in depth challenge: {e}")
            return ChallengeResult(
                challenge_id=challenge_id,
                challenge_type=self.challenge_type,
                engine1=engine1.config.name,
                engine2=engine2.config.name,
                winner=None,
                result_details={"error": str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
                status=BattleStatus.FAILED
            )

class PositionAnalysisChallenge(ChallengeBase):
    """Position analysis challenge - evaluate complex positions"""
    
    def __init__(self):
        super().__init__(ChallengeType.POSITION_ANALYSIS)
        
        # Known positions with expected evaluations
        self.analysis_positions = [
            {
                "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "expected_eval": 0,  # Starting position should be roughly equal
                "tolerance": 50,
                "description": "Starting position"
            },
            {
                "fen": "rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 2 3",
                "expected_eval": 30,  # Slight advantage to white
                "tolerance": 100,
                "description": "Italian Game opening"
            },
            {
                "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 4",
                "expected_eval": 0,  # Roughly equal
                "tolerance": 80,
                "description": "Four Knights Game"
            }
        ]
    
    async def execute(self, engine1: UCIEngine, engine2: UCIEngine, **kwargs) -> ChallengeResult:
        """Execute position analysis challenge"""
        time_limit = kwargs.get('time_limit', 8.0)
        
        start_time = time.time()
        challenge_id = f"analysis_{int(start_time)}"
        
        self.logger.info(f"Starting position analysis: {engine1.config.name} vs {engine2.config.name}")
        
        engine1_evaluations = []
        engine2_evaluations = []
        
        try:
            for i, pos_data in enumerate(self.analysis_positions):
                position = pos_data["fen"]
                expected = pos_data["expected_eval"]
                
                self.logger.info(f"Analyzing position {i + 1}: {pos_data['description']}")
                
                # Get evaluations from both engines
                move1, metrics1 = await engine1.get_best_move(f"fen {position}", time_limit)
                eval1 = metrics1.get("score", 0)
                
                move2, metrics2 = await engine2.get_best_move(f"fen {position}", time_limit)
                eval2 = metrics2.get("score", 0)
                
                # Calculate accuracy (how close to expected evaluation)
                accuracy1 = max(0, 1 - abs(eval1 - expected) / max(pos_data["tolerance"], 1))
                accuracy2 = max(0, 1 - abs(eval2 - expected) / max(pos_data["tolerance"], 1))
                
                engine1_evaluations.append({
                    "position": i,
                    "evaluation": eval1,
                    "expected": expected,
                    "accuracy": accuracy1,
                    "move": move1,
                    "depth": metrics1.get("depth", 0)
                })
                
                engine2_evaluations.append({
                    "position": i,
                    "evaluation": eval2,
                    "expected": expected,
                    "accuracy": accuracy2,
                    "move": move2,
                    "depth": metrics2.get("depth", 0)
                })
            
            # Calculate overall accuracy scores
            avg_accuracy1 = sum(e["accuracy"] for e in engine1_evaluations) / len(engine1_evaluations)
            avg_accuracy2 = sum(e["accuracy"] for e in engine2_evaluations) / len(engine2_evaluations)
            
            winner = engine1.config.name if avg_accuracy1 > avg_accuracy2 else engine2.config.name
            
            execution_time = time.time() - start_time
            
            return ChallengeResult(
                challenge_id=challenge_id,
                challenge_type=self.challenge_type,
                engine1=engine1.config.name,
                engine2=engine2.config.name,
                winner=winner,
                result_details={
                    "positions": self.analysis_positions,
                    "engine1_evaluations": engine1_evaluations,
                    "engine2_evaluations": engine2_evaluations,
                    "avg_accuracy_engine1": avg_accuracy1,
                    "avg_accuracy_engine2": avg_accuracy2
                },
                execution_time=execution_time,
                timestamp=datetime.now(),
                status=BattleStatus.COMPLETED,
                metrics={
                    "accuracy_difference": abs(avg_accuracy1 - avg_accuracy2),
                    "best_accuracy": max(avg_accuracy1, avg_accuracy2)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in position analysis: {e}")
            return ChallengeResult(
                challenge_id=challenge_id,
                challenge_type=self.challenge_type,
                engine1=engine1.config.name,
                engine2=engine2.config.name,
                winner=None,
                result_details={"error": str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
                status=BattleStatus.FAILED
            )

class TacticalChallenge(ChallengeBase):
    """Tactical pattern recognition challenge"""
    
    def __init__(self):
        super().__init__(ChallengeType.TACTICAL_CHALLENGE)
        
        # Tactical patterns to recognize
        self.tactical_positions = [
            {
                "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 6",
                "pattern": "pin",
                "best_moves": ["Bg5"],
                "description": "Pin the knight to the queen"
            },
            {
                "fen": "rnbqkb1r/ppp2ppp/4pn2/3P4/3P4/8/PPP2PPP/RNBQKBNR b KQkq - 0 4",
                "pattern": "fork",
                "best_moves": ["Nc6"],
                "description": "Knight fork opportunity"
            },
            {
                "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 4",
                "pattern": "discovery",
                "best_moves": ["Nd4"],
                "description": "Discovered attack"
            }
        ]
    
    async def execute(self, engine1: UCIEngine, engine2: UCIEngine, **kwargs) -> ChallengeResult:
        """Execute tactical challenge"""
        time_limit = kwargs.get('time_limit', 12.0)
        
        start_time = time.time()
        challenge_id = f"tactical_{int(start_time)}"
        
        self.logger.info(f"Starting tactical challenge: {engine1.config.name} vs {engine2.config.name}")
        
        engine1_results = []
        engine2_results = []
        
        try:
            for i, tactic in enumerate(self.tactical_positions):
                self.logger.info(f"Tactical pattern {i + 1}: {tactic['description']}")
                
                # Engine 1 attempt
                move1, metrics1 = await engine1.get_best_move(f"fen {tactic['fen']}", time_limit)
                found1 = move1 in tactic['best_moves'] if move1 else False
                
                engine1_results.append({
                    "pattern": tactic["pattern"],
                    "move": move1,
                    "found_tactic": found1,
                    "time": metrics1.get("search_time", time_limit),
                    "depth": metrics1.get("depth", 0)
                })
                
                # Engine 2 attempt
                move2, metrics2 = await engine2.get_best_move(f"fen {tactic['fen']}", time_limit)
                found2 = move2 in tactic['best_moves'] if move2 else False
                
                engine2_results.append({
                    "pattern": tactic["pattern"],
                    "move": move2,
                    "found_tactic": found2,
                    "time": metrics2.get("search_time", time_limit),
                    "depth": metrics2.get("depth", 0)
                })
            
            # Calculate tactical scores
            tactics_found1 = sum(1 for r in engine1_results if r["found_tactic"])
            tactics_found2 = sum(1 for r in engine2_results if r["found_tactic"])
            
            winner = engine1.config.name if tactics_found1 > tactics_found2 else engine2.config.name
            if tactics_found1 == tactics_found2:
                # Tie-breaker: faster average time
                avg_time1 = sum(r["time"] for r in engine1_results) / len(engine1_results)
                avg_time2 = sum(r["time"] for r in engine2_results) / len(engine2_results)
                winner = engine1.config.name if avg_time1 < avg_time2 else engine2.config.name
            
            execution_time = time.time() - start_time
            
            return ChallengeResult(
                challenge_id=challenge_id,
                challenge_type=self.challenge_type,
                engine1=engine1.config.name,
                engine2=engine2.config.name,
                winner=winner,
                result_details={
                    "tactical_positions": self.tactical_positions,
                    "engine1_results": engine1_results,
                    "engine2_results": engine2_results,
                    "tactics_found_engine1": tactics_found1,
                    "tactics_found_engine2": tactics_found2,
                    "total_tactics": len(self.tactical_positions)
                },
                execution_time=execution_time,
                timestamp=datetime.now(),
                status=BattleStatus.COMPLETED,
                metrics={
                    "tactical_accuracy_engine1": tactics_found1 / len(self.tactical_positions),
                    "tactical_accuracy_engine2": tactics_found2 / len(self.tactical_positions),
                    "tactical_difference": abs(tactics_found1 - tactics_found2)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in tactical challenge: {e}")
            return ChallengeResult(
                challenge_id=challenge_id,
                challenge_type=self.challenge_type,
                engine1=engine1.config.name,
                engine2=engine2.config.name,
                winner=None,
                result_details={"error": str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
                status=BattleStatus.FAILED
            )
