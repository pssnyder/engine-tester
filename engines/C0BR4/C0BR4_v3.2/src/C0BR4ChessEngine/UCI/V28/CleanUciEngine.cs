using System;
using System.Collections.Generic;
using System.Linq;
using C0BR4ChessEngine.Core.V28;

namespace C0BR4ChessEngine.UCI.V28
{
    /// <summary>
    /// Clean UCI engine implementation for C0BR4 v2.8
    /// Simple, reliable UCI protocol handler
    /// Built from scratch to eliminate legacy issues
    /// </summary>
    public class CleanUciEngine
    {
        private CleanBoardState _currentPosition;
        private bool _debugMode;
        private const string EngineName = "C0BR4";
        private const string EngineVersion = "2.8";
        private const string EngineAuthor = "C0BR4 Team";
        
        public CleanUciEngine()
        {
            _currentPosition = CleanBoardState.StartingPosition();
            _debugMode = false;
        }
        
        /// <summary>
        /// Process UCI command and return response
        /// </summary>
        public string ProcessCommand(string input)
        {
            if (string.IsNullOrWhiteSpace(input))
                return "";
            
            string[] tokens = input.Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries);
            if (tokens.Length == 0)
                return "";
            
            string command = tokens[0].ToLower();
            
            try
            {
                return command switch
                {
                    "uci" => HandleUciCommand(),
                    "debug" => HandleDebugCommand(tokens),
                    "isready" => HandleIsReadyCommand(),
                    "setoption" => HandleSetOptionCommand(tokens),
                    "register" => HandleRegisterCommand(),
                    "ucinewgame" => HandleUciNewGameCommand(),
                    "position" => HandlePositionCommand(tokens),
                    "go" => HandleGoCommand(tokens),
                    "stop" => HandleStopCommand(),
                    "ponderhit" => HandlePonderHitCommand(),
                    "quit" => HandleQuitCommand(),
                    _ => _debugMode ? $"info string Unknown command: {command}" : ""
                };
            }
            catch (Exception ex)
            {
                return _debugMode ? $"info string Error processing command '{command}': {ex.Message}" : "";
            }
        }
        
        /// <summary>
        /// Handle UCI identification command
        /// </summary>
        private string HandleUciCommand()
        {
            var response = new List<string>
            {
                $"id name {EngineName} v{EngineVersion}",
                $"id author {EngineAuthor}",
                "option name Hash type spin default 16 min 1 max 1024",
                "option name Threads type spin default 1 min 1 max 1",
                "option name OwnBook type check default false",
                "uciok"
            };
            
            return string.Join("\n", response);
        }
        
        /// <summary>
        /// Handle debug command
        /// </summary>
        private string HandleDebugCommand(string[] tokens)
        {
            if (tokens.Length > 1)
            {
                _debugMode = tokens[1].ToLower() == "on";
            }
            
            return _debugMode ? "info string Debug mode enabled" : "";
        }
        
        /// <summary>
        /// Handle isready command
        /// </summary>
        private string HandleIsReadyCommand()
        {
            // Initialize clean bitboards if not already done
            CleanBitboard.Initialize();
            return "readyok";
        }
        
        /// <summary>
        /// Handle setoption command
        /// </summary>
        private string HandleSetOptionCommand(string[] tokens)
        {
            // Basic option handling - can be expanded later
            if (_debugMode && tokens.Length > 2)
            {
                return $"info string Option set: {string.Join(" ", tokens.Skip(1))}";
            }
            
            return "";
        }
        
        /// <summary>
        /// Handle register command
        /// </summary>
        private string HandleRegisterCommand()
        {
            return ""; // No registration required
        }
        
        /// <summary>
        /// Handle ucinewgame command
        /// </summary>
        private string HandleUciNewGameCommand()
        {
            _currentPosition = CleanBoardState.StartingPosition();
            
            if (_debugMode)
                return "info string New game started";
            
            return "";
        }
        
        /// <summary>
        /// Handle position command
        /// </summary>
        private string HandlePositionCommand(string[] tokens)
        {
            if (tokens.Length < 2)
                return _debugMode ? "info string Error: position command requires arguments" : "";
            
            try
            {
                if (tokens[1] == "startpos")
                {
                    _currentPosition = CleanBoardState.StartingPosition();
                    
                    // Apply moves if provided
                    int movesIndex = Array.FindIndex(tokens, t => t == "moves");
                    if (movesIndex != -1 && movesIndex + 1 < tokens.Length)
                    {
                        for (int i = movesIndex + 1; i < tokens.Length; i++)
                        {
                            ApplyMove(tokens[i]);
                        }
                    }
                }
                else if (tokens[1] == "fen")
                {
                    // Build FEN string from tokens
                    var fenParts = new List<string>();
                    int i = 2;
                    
                    // Collect FEN parts until we hit "moves" or end
                    while (i < tokens.Length && tokens[i] != "moves")
                    {
                        fenParts.Add(tokens[i]);
                        i++;
                    }
                    
                    if (fenParts.Count == 0)
                        return _debugMode ? "info string Error: FEN position requires FEN string" : "";
                    
                    string fenString = string.Join(" ", fenParts);
                    _currentPosition = CleanFenParser.ParseFen(fenString);
                    
                    // Apply moves if provided
                    if (i < tokens.Length && tokens[i] == "moves")
                    {
                        for (int j = i + 1; j < tokens.Length; j++)
                        {
                            ApplyMove(tokens[j]);
                        }
                    }
                }
                
                if (_debugMode)
                {
                    return $"info string Position set. FEN: {_currentPosition.ToFEN()}";
                }
            }
            catch (Exception ex)
            {
                return _debugMode ? $"info string Error setting position: {ex.Message}" : "";
            }
            
            return "";
        }
        
        /// <summary>
        /// Handle go command
        /// </summary>
        private string HandleGoCommand(string[] tokens)
        {
            try
            {
                // Generate legal moves for current position
                var legalMoves = CleanMoveGenerator.GenerateLegalMoves(_currentPosition);
                
                if (legalMoves.Count == 0)
                {
                    return "bestmove 0000"; // No legal moves (checkmate or stalemate)
                }
                
                // For now, just pick the first legal move
                // This will be replaced with actual search later
                var bestMove = legalMoves[0];
                
                var response = new List<string>();
                
                if (_debugMode)
                {
                    response.Add($"info string Generated {legalMoves.Count} legal moves");
                    response.Add($"info string Selected move: {bestMove.ToUCI()}");
                }
                
                response.Add($"bestmove {bestMove.ToUCI()}");
                
                return string.Join("\n", response);
            }
            catch (Exception ex)
            {
                return _debugMode ? 
                    $"info string Error generating move: {ex.Message}\nbestmove 0000" : 
                    "bestmove 0000";
            }
        }
        
        /// <summary>
        /// Handle stop command
        /// </summary>
        private string HandleStopCommand()
        {
            // For now, just return a default move since we don't have search yet
            return "bestmove 0000";
        }
        
        /// <summary>
        /// Handle ponderhit command
        /// </summary>
        private string HandlePonderHitCommand()
        {
            return ""; // Not implemented yet
        }
        
        /// <summary>
        /// Handle quit command
        /// </summary>
        private string HandleQuitCommand()
        {
            return ""; // Caller should handle termination
        }
        
        /// <summary>
        /// Apply a move in UCI notation to the current position
        /// </summary>
        private void ApplyMove(string uciMove)
        {
            try
            {
                var move = CleanMove.FromUCI(uciMove, _currentPosition);
                
                // Validate that the move is legal
                var legalMoves = CleanMoveGenerator.GenerateLegalMoves(_currentPosition);
                
                if (!legalMoves.Contains(move))
                {
                    throw new ArgumentException($"Illegal move: {uciMove}");
                }
                
                // Apply the move
                CleanMoveGenerator.MakeMove(ref _currentPosition, move);
                
                if (_debugMode)
                {
                    Console.WriteLine($"info string Applied move: {uciMove}");
                }
            }
            catch (Exception ex)
            {
                if (_debugMode)
                {
                    Console.WriteLine($"info string Error applying move {uciMove}: {ex.Message}");
                }
                throw;
            }
        }
        
        /// <summary>
        /// Get current position FEN (for debugging)
        /// </summary>
        public string GetCurrentPositionFen()
        {
            return _currentPosition.ToFEN();
        }
        
        /// <summary>
        /// Get legal moves for current position (for debugging)
        /// </summary>
        public List<CleanMove> GetLegalMoves()
        {
            return CleanMoveGenerator.GenerateLegalMoves(_currentPosition);
        }
        
        /// <summary>
        /// Validate current position (for debugging)
        /// </summary>
        public bool IsCurrentPositionValid()
        {
            return _currentPosition.IsValid();
        }
    }
}
