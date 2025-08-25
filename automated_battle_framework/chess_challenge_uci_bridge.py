#!/usr/bin/env python3
"""
Chess Challenge UCI Bridge
==========================

Creates a UCI interface for Chess Challenge bots by:
1. Wrapping the Chess Challenge API in a UCI-compatible subprocess
2. Translating between UCI commands and Chess Challenge Think() calls
3. Managing the bot execution and position state

This allows rated Chess Challenge bots to work with our battle framework.
"""

import subprocess
import sys
import os
import tempfile
from pathlib import Path
import threading
import queue
import time
import json

class ChessChallengeBridge:
    """UCI bridge for Chess Challenge bots"""
    
    def __init__(self, bot_name: str):
        self.bot_name = bot_name
        self.engine_tester_root = Path("s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester")
        self.chess_challenge_source = self.engine_tester_root / "source_repos" / "Chess-Challenge" / "Chess-Challenge"
        self.process = None
        self.temp_dir = None
        
    def create_uci_wrapper_bot(self, original_bot_content: str) -> str:
        """Create a UCI-compatible version of a Chess Challenge bot"""
        
        # Extract the Think method and adapt it
        uci_bot_template = '''using ChessChallenge.API;
using System;

public class MyBot : IChessBot
{
    // UCI Bridge - This bot is adapted for UCI compatibility
    // Original bot logic preserved in Think method
    
{original_think_method}
    
    // UCI Communication methods
    static void Main(string[] args)
    {{
        var bot = new MyBot();
        var bridge = new UCIBridge(bot);
        bridge.Run();
    }}
}}

public class UCIBridge
{{
    private MyBot bot;
    private Board currentBoard;
    private Timer timer;
    
    public UCIBridge(MyBot bot)
    {{
        this.bot = bot;
        // Initialize with starting position
        this.currentBoard = Board.CreateBoardFromFen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
        this.timer = new Timer(1000); // Default 1 second
    }}
    
    public void Run()
    {{
        string line;
        while ((line = Console.ReadLine()) != null)
        {{
            try
            {{
                ProcessCommand(line.Trim());
            }}
            catch (Exception ex)
            {{
                Console.WriteLine($"info string Error: {{ex.Message}}");
            }}
        }}
    }}
    
    private void ProcessCommand(string command)
    {{
        var parts = command.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (parts.Length == 0) return;
        
        switch (parts[0].ToLower())
        {{
            case "uci":
                Console.WriteLine("id name BongcloudEnthusiast_ChessChallenge");
                Console.WriteLine("id author Chess Challenge Bot");
                Console.WriteLine("uciok");
                break;
                
            case "isready":
                Console.WriteLine("readyok");
                break;
                
            case "ucinewgame":
                currentBoard = Board.CreateBoardFromFen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
                break;
                
            case "position":
                HandlePosition(parts);
                break;
                
            case "go":
                HandleGo(parts);
                break;
                
            case "quit":
                Environment.Exit(0);
                break;
        }}
    }}
    
    private void HandlePosition(string[] parts)
    {{
        if (parts.Length < 2) return;
        
        if (parts[1] == "startpos")
        {{
            currentBoard = Board.CreateBoardFromFen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
            
            // Apply moves if provided
            int movesIndex = Array.IndexOf(parts, "moves");
            if (movesIndex >= 0 && movesIndex + 1 < parts.Length)
            {{
                for (int i = movesIndex + 1; i < parts.Length; i++)
                {{
                    try
                    {{
                        var move = new Move(parts[i], currentBoard);
                        currentBoard.MakeMove(move);
                    }}
                    catch
                    {{
                        Console.WriteLine($"info string Invalid move: {{parts[i]}}");
                    }}
                }}
            }}
        }}
        else if (parts[1] == "fen" && parts.Length >= 8)
        {{
            // Reconstruct FEN from parts[2] through parts[7]
            string fen = string.Join(" ", parts, 2, 6);
            currentBoard = Board.CreateBoardFromFen(fen);
            
            // Apply moves if provided
            int movesIndex = Array.IndexOf(parts, "moves");
            if (movesIndex >= 0 && movesIndex + 1 < parts.Length)
            {{
                for (int i = movesIndex + 1; i < parts.Length; i++)
                {{
                    try
                    {{
                        var move = new Move(parts[i], currentBoard);
                        currentBoard.MakeMove(move);
                    }}
                    catch
                    {{
                        Console.WriteLine($"info string Invalid move: {{parts[i]}}");
                    }}
                }}
            }}
        }}
    }}
    
    private void HandleGo(string[] parts)
    {{
        // Parse time control (simplified)
        int timeMs = 1000; // Default 1 second
        
        for (int i = 1; i < parts.Length - 1; i++)
        {{
            if (parts[i] == "movetime")
            {{
                if (int.TryParse(parts[i + 1], out int mt))
                    timeMs = mt;
            }}
            else if (parts[i] == "wtime" && currentBoard.IsWhiteToMove)
            {{
                if (int.TryParse(parts[i + 1], out int wt))
                    timeMs = wt / 20; // Use 1/20th of remaining time
            }}
            else if (parts[i] == "btime" && !currentBoard.IsWhiteToMove)
            {{
                if (int.TryParse(parts[i + 1], out int bt))
                    timeMs = bt / 20; // Use 1/20th of remaining time
            }}
        }}
        
        timer = new Timer(timeMs);
        
        try
        {{
            var bestMove = bot.Think(currentBoard, timer);
            Console.WriteLine($"bestmove {{bestMove.StartSquare.Name}}{{bestMove.TargetSquare.Name}}");
        }}
        catch (Exception ex)
        {{
            Console.WriteLine($"info string Think error: {{ex.Message}}");
            // Return first legal move as fallback
            var moves = currentBoard.GetLegalMoves();
            if (moves.Length > 0)
            {{
                Console.WriteLine($"bestmove {{moves[0].StartSquare.Name}}{{moves[0].TargetSquare.Name}}");
            }}
            else
            {{
                Console.WriteLine("bestmove 0000");
            }}
        }}
    }}
}}
'''
        
        # Replace the placeholder with the actual Think method
        # For BongcloudEnthusiast, we already have the content
        return uci_bot_template.replace("{original_think_method}", self.extract_think_method(original_bot_content))
    
    def extract_think_method(self, bot_content: str) -> str:
        """Extract the Think method from the original bot"""
        # For now, return the BongcloudEnthusiast Think method
        # This could be made more sophisticated to parse any bot
        return '''
    Random random = new Random();
    //Material for air, pawn, knight, bishop, rook, queen, and king, respectively
    int[] PieceMaterial = { 0, 10, 30, 35, 50, 90, 6969 };
    int Evaluation;

    //This is the function that returns the move to be actually played
    public Move Think(Board Position, Timer timer)
    {
        // BongcloudEnthusiast Strategy (307 ELO)
        switch (Position.PlyCount)
        {
            case 0:
                return new Move("e2e4", Position);
            case 1:
                return new Move("e7e5", Position);
            case 2:
                return new Move("e1e2", Position);
            case 3:
                return new Move("e8e7", Position);
        }

        Move[] Moves = Position.GetLegalMoves();

        foreach (Move move in Moves)
        {
            if (move.IsCapture || move.IsPromotion) return move;

            Position.MakeMove(move);

            if (Position.IsInCheckmate()) return move;
            if (Position.IsInStalemate())
            {
                Position.UndoMove(move);
                continue;
            }
            Position.UndoMove(move);
        }

        return Moves[random.Next(Moves.Length)];
    }'''
    
    def compile_uci_bot(self, bot_content: str) -> Path:
        """Compile a UCI-compatible version of the bot"""
        
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix=f"uci_bridge_{self.bot_name}_"))
        
        # Copy Chess Challenge framework
        import shutil
        framework_dest = self.temp_dir / "Chess-Challenge"
        shutil.copytree(self.chess_challenge_source, framework_dest)
        
        # Create UCI wrapper bot
        uci_bot_content = self.create_uci_wrapper_bot(bot_content)
        
        # Write to MyBot.cs
        my_bot_file = framework_dest / "src" / "My Bot" / "MyBot.cs"
        with open(my_bot_file, 'w') as f:
            f.write(uci_bot_content)
        
        # Build the project
        try:
            result = subprocess.run(
                ["dotnet", "build", "-c", "Release"],
                cwd=framework_dest,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Find the compiled executable
            bin_dir = framework_dest / "bin" / "Release" / "net6.0"
            exe_path = bin_dir / "Chess-Challenge.exe"
            
            if exe_path.exists():
                return exe_path
            else:
                raise RuntimeError("Compiled executable not found")
                
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Compilation failed: {e.stderr}")


def create_bongcloud_uci_engine():
    """Create a UCI-compatible BongcloudEnthusiast engine"""
    
    print("🔨 Creating UCI-compatible BongcloudEnthusiast engine...")
    
    # Load the original bot
    bot_file = Path("s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester/engines/Opponents/beginner/BongcloudEnthusiast_Bot_278.cs")
    
    with open(bot_file, 'r') as f:
        bot_content = f.read()
    
    # Create UCI bridge
    bridge = ChessChallengeBridge("BongcloudEnthusiast")
    
    try:
        uci_exe = bridge.compile_uci_bot(bot_content)
        
        # Copy to engines directory
        engines_dir = Path("s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester/engines")
        dest_path = engines_dir / "BongcloudEnthusiast_UCI.exe"
        
        import shutil
        shutil.copy2(uci_exe, dest_path)
        
        print(f"✅ UCI BongcloudEnthusiast created: {dest_path}")
        return dest_path
        
    except Exception as e:
        print(f"❌ Failed to create UCI engine: {e}")
        return None


if __name__ == "__main__":
    """Test the UCI bridge"""
    result = create_bongcloud_uci_engine()
    
    if result:
        print(f"🎉 Success! UCI engine ready at: {result}")
        print("🚀 Next: Test with V7P3R vs BongcloudEnthusiast")
    else:
        print("❌ UCI bridge creation failed")
