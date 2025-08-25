#!/usr/bin/env python3
"""
🤖 Auto# Add engine paths to Python path for imports
ENGINE_TESTER_ROOT = Path(__file__).parent.parent
V7P3R_SRC = Path("S:/Maker Stuff/Programming/Chess Engines/V7P3R Chess Engine/v7p3r-chess-engine/src")
SLOWMATE_SRC = Path("S:/Maker Stuff/Programming/Chess Engines/SlowMate Chess Engine/slowmate-chess-engine/src")

sys.path.append(str(V7P3R_SRC))
sys.path.append(str(SLOWMATE_SRC))ngine Battle Framework
====================================

A comprehensive automated testing system for chess engines, specifically designed
for V7P3R vs SlowMate competition with C0BR4 as a control engine.

Features:
- UCI communication with all engine types (Python, C#, exe)
- Multiple challenge types: puzzles, speed, depth, traditional games
- Real-time metrics collection without visual overhead
- Terminal-based progress monitoring
- Automated result processing and analysis
- Version vs version gauntlets
- Background execution capability

Author: AI Assistant & User Collaboration
Date: August 2025
"""

import asyncio
import json
import logging
import subprocess
import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import sys
import os

# Add engine paths to Python path for imports
ENGINE_TESTER_ROOT = Path(__file__).parent.parent
ENGINES_DIR = ENGINE_TESTER_ROOT / "engines"

# Engine executable paths
V7P3R_EXE = ENGINES_DIR / "V7P3R" / "V7P3R_v7.0.exe"
SLOWMATE_EXE = ENGINES_DIR / "SlowMate" / "SlowMate_v3.0.exe"
C0BR4_EXE = ENGINES_DIR / "C0BR4" / "C0BR4_v2.1.exe"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('battle_framework.log'),
        logging.StreamHandler()
    ]
)

class EngineType(Enum):
    """Types of engines supported by the framework"""
    PYTHON_V7P3R = "python_v7p3r"
    PYTHON_SLOWMATE = "python_slowmate"
    EXE_CONTROL = "exe_control"
    EXE_HISTORICAL = "exe_historical"

class ChallengeType(Enum):
    """Types of challenges engines can compete in"""
    TRADITIONAL_GAME = "traditional_game"
    PUZZLE_SOLVE = "puzzle_solve"
    SPEED_CHALLENGE = "speed_challenge"
    DEPTH_CHALLENGE = "depth_challenge"
    POSITION_ANALYSIS = "position_analysis"
    TACTICAL_CHALLENGE = "tactical_challenge"

class BattleStatus(Enum):
    """Status of battles and challenges"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class EngineConfig:
    """Configuration for an engine"""
    name: str
    engine_type: EngineType
    path: str
    version: str
    executable_args: List[str] = None
    time_limit: float = 30.0
    memory_limit: int = 128  # MB
    
    def __post_init__(self):
        if self.executable_args is None:
            self.executable_args = []

@dataclass
class ChallengeResult:
    """Result of a single challenge"""
    challenge_id: str
    challenge_type: ChallengeType
    engine1: str
    engine2: str
    winner: Optional[str]
    result_details: Dict[str, Any]
    execution_time: float
    timestamp: datetime
    status: BattleStatus
    metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}

@dataclass
class BattleSession:
    """A complete battle session containing multiple challenges"""
    session_id: str
    name: str
    description: str
    engines: List[EngineConfig]
    challenges: List[ChallengeResult]
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration: float = 0.0
    status: BattleStatus = BattleStatus.PENDING

class UCIEngine:
    """Universal Chess Interface communication handler"""
    
    def __init__(self, config: EngineConfig):
        self.config = config
        self.process = None
        self.logger = logging.getLogger(f"UCI_{config.name}")
        
    async def start(self) -> bool:
        """Start the UCI engine process"""
        try:
            if self.config.engine_type == EngineType.PYTHON_V7P3R:
                # Start V7P3R executable engine
                cmd = [str(V7P3R_EXE)]
                cwd = str(V7P3R_EXE.parent)
            elif self.config.engine_type == EngineType.PYTHON_SLOWMATE:
                # Start SlowMate executable engine
                cmd = [str(SLOWMATE_EXE)]
                cwd = str(SLOWMATE_EXE.parent)
            elif self.config.engine_type in [EngineType.EXE_CONTROL, EngineType.EXE_HISTORICAL]:
                # Start other executable engines
                cmd = [self.config.path] + self.config.executable_args
                cwd = str(Path(self.config.path).parent)
            else:
                raise ValueError(f"Unsupported engine type: {self.config.engine_type}")
            
            self.logger.info(f"Starting {self.config.name}: {' '.join(cmd)}")
            self.logger.info(f"Working directory: {cwd}")
            
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )            # Send UCI handshake
            await self.send_command("uci")
            response = await self.read_until("uciok")
            
            if "uciok" in response:
                self.logger.info(f"Successfully started {self.config.name}")
                return True
            else:
                self.logger.error(f"Failed UCI handshake with {self.config.name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting {self.config.name}: {e}")
            return False
    
    async def send_command(self, command: str):
        """Send a command to the UCI engine"""
        if self.process and self.process.stdin:
            self.process.stdin.write((command + "\n").encode())
            await self.process.stdin.drain()
            self.logger.debug(f"Sent to {self.config.name}: {command}")
    
    async def read_until(self, terminator: str, timeout: float = 5.0) -> str:
        """Read engine output until a specific terminator is found"""
        output = ""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.process and self.process.stdout:
                try:
                    line = await asyncio.wait_for(
                        self.process.stdout.readline(), 
                        timeout=0.1
                    )
                    if line:
                        line_str = line.decode().strip()
                        output += line_str + "\n"
                        self.logger.debug(f"Received from {self.config.name}: {line_str}")
                        
                        if terminator in line_str:
                            break
                except asyncio.TimeoutError:
                    continue
        
        return output
    
    async def get_best_move(self, position: str, time_limit: float = None) -> Tuple[str, Dict[str, Any]]:
        """Get the best move for a position with optional time limit"""
        if time_limit is None:
            time_limit = self.config.time_limit
        
        # Set up position
        await self.send_command(f"position {position}")
        
        # Start search
        search_cmd = f"go movetime {int(time_limit * 1000)}"
        await self.send_command(search_cmd)
        
        # Read search results
        start_time = time.time()
        output = await self.read_until("bestmove", timeout=time_limit + 5.0)
        search_time = time.time() - start_time
        
        # Parse results
        best_move = None
        metrics = {
            "search_time": search_time,
            "nodes": 0,
            "depth": 0,
            "score": 0
        }
        
        for line in output.split("\n"):
            if line.startswith("bestmove"):
                parts = line.split()
                if len(parts) > 1:
                    best_move = parts[1]
            elif "info" in line and "depth" in line:
                # Parse UCI info for metrics
                if "nodes" in line:
                    try:
                        nodes_idx = line.split().index("nodes")
                        metrics["nodes"] = int(line.split()[nodes_idx + 1])
                    except (ValueError, IndexError):
                        pass
                if "depth" in line:
                    try:
                        depth_idx = line.split().index("depth")
                        metrics["depth"] = int(line.split()[depth_idx + 1])
                    except (ValueError, IndexError):
                        pass
                if "score cp" in line:
                    try:
                        score_idx = line.split().index("cp")
                        metrics["score"] = int(line.split()[score_idx + 1])
                    except (ValueError, IndexError):
                        pass
        
        return best_move, metrics
    
    async def stop(self):
        """Stop the UCI engine"""
        if self.process:
            await self.send_command("quit")
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.terminate()
                await self.process.wait()
            self.logger.info(f"Stopped {self.config.name}")

class ChallengeBase(ABC):
    """Base class for all challenge types"""
    
    def __init__(self, challenge_type: ChallengeType):
        self.challenge_type = challenge_type
        self.logger = logging.getLogger(f"Challenge_{challenge_type.value}")
    
    @abstractmethod
    async def execute(self, engine1: UCIEngine, engine2: UCIEngine, **kwargs) -> ChallengeResult:
        """Execute the challenge between two engines"""
        pass

class TraditionalGameChallenge(ChallengeBase):
    """Traditional chess game challenge"""
    
    def __init__(self):
        super().__init__(ChallengeType.TRADITIONAL_GAME)
    
    async def execute(self, engine1: UCIEngine, engine2: UCIEngine, **kwargs) -> ChallengeResult:
        """Execute a traditional chess game"""
        time_control = kwargs.get('time_control', 30.0)  # seconds per move
        max_moves = kwargs.get('max_moves', 100)
        
        start_time = time.time()
        challenge_id = f"trad_game_{int(start_time)}"
        
        # Initialize game state
        position = "startpos"
        moves = []
        game_result = None
        turn = 0  # 0 = engine1 (white), 1 = engine2 (black)
        
        self.logger.info(f"Starting traditional game: {engine1.config.name} vs {engine2.config.name}")
        
        try:
            for move_num in range(max_moves):
                current_engine = engine1 if turn == 0 else engine2
                
                # Build position string
                if moves:
                    position_cmd = f"startpos moves {' '.join(moves)}"
                else:
                    position_cmd = "startpos"
                
                # Get move from current engine
                move, metrics = await current_engine.get_best_move(position_cmd, time_control)
                
                if not move or move == "(none)":
                    # Game ended (checkmate, stalemate, etc.)
                    game_result = "1-0" if turn == 1 else "0-1"
                    break
                
                moves.append(move)
                turn = 1 - turn
                
                self.logger.debug(f"Move {move_num + 1}: {move}")
            
            if game_result is None:
                game_result = "1/2-1/2"  # Draw by move limit
            
            execution_time = time.time() - start_time
            
            return ChallengeResult(
                challenge_id=challenge_id,
                challenge_type=self.challenge_type,
                engine1=engine1.config.name,
                engine2=engine2.config.name,
                winner=self._parse_winner(game_result, engine1.config.name, engine2.config.name),
                result_details={
                    "result": game_result,
                    "moves": moves,
                    "move_count": len(moves)
                },
                execution_time=execution_time,
                timestamp=datetime.now(),
                status=BattleStatus.COMPLETED,
                metrics={
                    "game_length": len(moves),
                    "avg_time_per_move": execution_time / max(len(moves), 1)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in traditional game: {e}")
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
    
    def _parse_winner(self, result: str, engine1_name: str, engine2_name: str) -> Optional[str]:
        """Parse game result to determine winner"""
        if result == "1-0":
            return engine1_name
        elif result == "0-1":
            return engine2_name
        else:
            return None  # Draw

class SpeedChallenge(ChallengeBase):
    """Speed challenge - who can find a good move fastest"""
    
    def __init__(self):
        super().__init__(ChallengeType.SPEED_CHALLENGE)
    
    async def execute(self, engine1: UCIEngine, engine2: UCIEngine, **kwargs) -> ChallengeResult:
        """Execute speed challenge"""
        positions = kwargs.get('positions', [
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",  # Starting position
            "rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 2 3",  # Italian game
            "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 4"  # Four knights
        ])
        time_limit = kwargs.get('time_limit', 5.0)
        
        start_time = time.time()
        challenge_id = f"speed_{int(start_time)}"
        
        self.logger.info(f"Starting speed challenge: {engine1.config.name} vs {engine2.config.name}")
        
        engine1_times = []
        engine2_times = []
        engine1_moves = []
        engine2_moves = []
        
        try:
            for i, position in enumerate(positions):
                self.logger.info(f"Speed test position {i + 1}/{len(positions)}")
                
                # Test engine1
                move1, metrics1 = await engine1.get_best_move(f"fen {position}", time_limit)
                engine1_times.append(metrics1.get("search_time", time_limit))
                engine1_moves.append(move1)
                
                # Test engine2
                move2, metrics2 = await engine2.get_best_move(f"fen {position}", time_limit)
                engine2_times.append(metrics2.get("search_time", time_limit))
                engine2_moves.append(move2)
            
            # Calculate results
            avg_time1 = sum(engine1_times) / len(engine1_times)
            avg_time2 = sum(engine2_times) / len(engine2_times)
            
            winner = engine1.config.name if avg_time1 < avg_time2 else engine2.config.name
            
            execution_time = time.time() - start_time
            
            return ChallengeResult(
                challenge_id=challenge_id,
                challenge_type=self.challenge_type,
                engine1=engine1.config.name,
                engine2=engine2.config.name,
                winner=winner,
                result_details={
                    "engine1_times": engine1_times,
                    "engine2_times": engine2_times,
                    "engine1_moves": engine1_moves,
                    "engine2_moves": engine2_moves,
                    "avg_time_engine1": avg_time1,
                    "avg_time_engine2": avg_time2
                },
                execution_time=execution_time,
                timestamp=datetime.now(),
                status=BattleStatus.COMPLETED,
                metrics={
                    "speed_advantage": abs(avg_time1 - avg_time2),
                    "fastest_time": min(avg_time1, avg_time2)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in speed challenge: {e}")
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

class BattleFramework:
    """Main framework for orchestrating engine battles"""
    
    def __init__(self):
        self.logger = logging.getLogger("BattleFramework")
        self.engines: Dict[str, EngineConfig] = {}
        self.challenges: Dict[ChallengeType, ChallengeBase] = {
            ChallengeType.TRADITIONAL_GAME: TraditionalGameChallenge(),
            ChallengeType.SPEED_CHALLENGE: SpeedChallenge(),
        }
        self.active_sessions: Dict[str, BattleSession] = {}
        self.results_dir = Path("battle_results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Initialize default engines
        self._setup_default_engines()
    
    def _setup_default_engines(self):
        """Setup default engine configurations"""
        # V7P3R Engine (using executable)
        if V7P3R_EXE.exists():
            self.add_engine(EngineConfig(
                name="V7P3R_Current",
                engine_type=EngineType.PYTHON_V7P3R,
                path=str(V7P3R_EXE),
                version="v7.0"
            ))
        
        # SlowMate Engine (using executable)  
        if SLOWMATE_EXE.exists():
            self.add_engine(EngineConfig(
                name="SlowMate_Current",
                engine_type=EngineType.PYTHON_SLOWMATE,
                path=str(SLOWMATE_EXE),
                version="v3.0"
            ))
        
        # C0BR4 Control Engine
        if C0BR4_EXE.exists():
            self.add_engine(EngineConfig(
                name="C0BR4_Control",
                engine_type=EngineType.EXE_CONTROL,
                path=str(C0BR4_EXE),
                version="v2.1"
            ))
    
    def add_engine(self, config: EngineConfig):
        """Add an engine configuration"""
        self.engines[config.name] = config
        self.logger.info(f"Added engine: {config.name} ({config.engine_type.value})")
    
    async def create_battle_session(self, session_name: str, description: str = "") -> str:
        """Create a new battle session"""
        session_id = f"battle_{int(time.time())}"
        
        session = BattleSession(
            session_id=session_id,
            name=session_name,
            description=description,
            engines=list(self.engines.values()),
            challenges=[],
            start_time=datetime.now()
        )
        
        self.active_sessions[session_id] = session
        self.logger.info(f"Created battle session: {session_name} ({session_id})")
        
        return session_id
    
    async def run_challenge(self, session_id: str, challenge_type: ChallengeType, 
                          engine1_name: str, engine2_name: str, **kwargs) -> ChallengeResult:
        """Run a specific challenge between two engines"""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        if engine1_name not in self.engines or engine2_name not in self.engines:
            raise ValueError("One or both engines not found")
        
        if challenge_type not in self.challenges:
            raise ValueError(f"Challenge type {challenge_type} not supported")
        
        session = self.active_sessions[session_id]
        session.status = BattleStatus.RUNNING
        
        # Create engine instances
        engine1 = UCIEngine(self.engines[engine1_name])
        engine2 = UCIEngine(self.engines[engine2_name])
        
        try:
            # Start engines
            if not await engine1.start():
                raise RuntimeError(f"Failed to start {engine1_name}")
            if not await engine2.start():
                raise RuntimeError(f"Failed to start {engine2_name}")
            
            # Run challenge
            self.logger.info(f"Running {challenge_type.value}: {engine1_name} vs {engine2_name}")
            challenge = self.challenges[challenge_type]
            result = await challenge.execute(engine1, engine2, **kwargs)
            
            # Store result
            session.challenges.append(result)
            
            return result
            
        finally:
            # Cleanup engines
            await engine1.stop()
            await engine2.stop()
    
    async def run_battle_gauntlet(self, session_id: str, engine1_name: str, engine2_name: str,
                                challenge_types: List[ChallengeType] = None) -> List[ChallengeResult]:
        """Run a gauntlet of challenges between two engines"""
        
        if challenge_types is None:
            challenge_types = [ChallengeType.SPEED_CHALLENGE, ChallengeType.TRADITIONAL_GAME]
        
        results = []
        
        for challenge_type in challenge_types:
            self.logger.info(f"Running gauntlet challenge: {challenge_type.value}")
            result = await self.run_challenge(session_id, challenge_type, engine1_name, engine2_name)
            results.append(result)
            
            # Brief pause between challenges
            await asyncio.sleep(1.0)
        
        return results
    
    def save_session(self, session_id: str):
        """Save battle session results to file"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        session.end_time = datetime.now()
        session.total_duration = (session.end_time - session.start_time).total_seconds()
        session.status = BattleStatus.COMPLETED
        
        # Convert to dict for JSON serialization
        session_data = {
            "session_id": session.session_id,
            "name": session.name,
            "description": session.description,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "total_duration": session.total_duration,
            "status": session.status.value,
            "engines": [asdict(engine) for engine in session.engines],
            "challenges": [asdict(challenge) for challenge in session.challenges]
        }
        
        # Save to file
        filename = f"{session.name.replace(' ', '_')}_{session_id}.json"
        filepath = self.results_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2, default=str)
        
        self.logger.info(f"Saved session results to: {filepath}")
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary statistics for a battle session"""
        if session_id not in self.active_sessions:
            return {}
        
        session = self.active_sessions[session_id]
        
        # Calculate summary stats
        total_challenges = len(session.challenges)
        completed_challenges = len([c for c in session.challenges if c.status == BattleStatus.COMPLETED])
        
        engine_wins = {}
        for challenge in session.challenges:
            if challenge.winner:
                engine_wins[challenge.winner] = engine_wins.get(challenge.winner, 0) + 1
        
        return {
            "session_id": session_id,
            "name": session.name,
            "status": session.status.value,
            "total_challenges": total_challenges,
            "completed_challenges": completed_challenges,
            "engine_wins": engine_wins,
            "duration": session.total_duration
        }

# Example usage and testing
async def main():
    """Example usage of the battle framework"""
    framework = BattleFramework()
    
    # Create a battle session
    session_id = await framework.create_battle_session(
        "V7P3R_vs_SlowMate_Automated_Battle",
        "Comprehensive automated testing between V7P3R and SlowMate engines"
    )
    
    print(f"🚀 Starting Automated Engine Battle Session: {session_id}")
    print("=" * 60)
    
    try:
        # Run speed challenge
        print("⚡ Running Speed Challenge...")
        speed_result = await framework.run_challenge(
            session_id, 
            ChallengeType.SPEED_CHALLENGE,
            "V7P3R_Current",
            "SlowMate_Current",
            time_limit=3.0
        )
        print(f"Speed Challenge Winner: {speed_result.winner}")
        print(f"Execution Time: {speed_result.execution_time:.2f}s")
        
        # Run traditional game
        print("\n♟️  Running Traditional Game...")
        game_result = await framework.run_challenge(
            session_id,
            ChallengeType.TRADITIONAL_GAME,
            "V7P3R_Current", 
            "SlowMate_Current",
            time_control=10.0,
            max_moves=50
        )
        print(f"Traditional Game Winner: {game_result.winner}")
        print(f"Game Length: {game_result.result_details.get('move_count', 0)} moves")
        
        # Save results
        framework.save_session(session_id)
        
        # Print summary
        summary = framework.get_session_summary(session_id)
        print("\n📊 Battle Session Summary:")
        print(f"Total Challenges: {summary['total_challenges']}")
        print(f"Completed: {summary['completed_challenges']}")
        print(f"Engine Wins: {summary['engine_wins']}")
        print(f"Duration: {summary['duration']:.2f}s")
        
    except Exception as e:
        print(f"❌ Error during battle: {e}")
        framework.logger.error(f"Battle error: {e}")

if __name__ == "__main__":
    print("🤖 Automated Engine Battle Framework")
    print("===================================")
    asyncio.run(main())
