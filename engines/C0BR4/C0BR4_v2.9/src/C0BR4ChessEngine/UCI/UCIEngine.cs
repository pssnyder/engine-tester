using System;
using System.IO;
using System.Threading;
using C0BR4ChessEngine.Core;
using C0BR4ChessEngine.Search;
using C0BR4ChessEngine.Testing;
using C0BR4ChessEngine.Evaluation;
using C0BR4ChessEngine.Opening;

namespace C0BR4ChessEngine.UCI
{
    /// <summary>
    /// UCI (Universal Chess Interface) implementation
    /// Handles communication with chess GUIs
    /// </summary>
    public class UCIEngine
    {
        private Board board = new();
        private IChessBot bot = new TranspositionSearchBot(); // v0.6: Alpha-beta with move ordering, quiescence, and transposition table
        private bool isRunning = true;
        private const string EngineVersion = "v2.9";

        public UCIEngine()
        {
            // Version is now hardcoded - no external file dependency
        }

        public void Run()
        {
            Console.WriteLine($"C0BR4 {EngineVersion}");
            
            while (isRunning)
            {
                string? input = Console.ReadLine();
                if (input == null) break;
                
                ProcessCommand(input.Trim());
            }
        }

        private void ProcessCommand(string command)
        {
            string[] parts = command.Split(' ', StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length == 0) return;

            switch (parts[0].ToLower())
            {
                case "uci":
                    HandleUCI();
                    break;
                case "isready":
                    Console.WriteLine("readyok");
                    break;
                case "ucinewgame":
                    board = new Board();
                    break;
                case "position":
                    HandlePosition(parts);
                    break;
                case "go":
                    HandleGo(parts);
                    break;
                case "stop":
                    // TODO: Implement search stopping
                    break;
                case "quit":
                    isRunning = false;
                    break;
                case "d":
                case "display":
                    DisplayBoard();
                    break;
                case "bench":
                case "benchmark":
                    RunBenchmark();
                    break;
                case "perft":
                    RunPerft(parts);
                    break;
                case "eval":
                    RunEval();
                    break;
                case "depth":
                    SetDepth(parts);
                    break;
                case "engine":
                    SetEngine(parts);
                    break;
                case "debug":
                    DebugPosition();
                    break;
                case "test":
                case "validate":
                    TestPosition();
                    break;
                case "testmove":
                    TestSpecificMove(parts);
                    break;
                case "testall":
                    RunBitboardValidationTests();
                    break;
                default:
                    // Unknown command - ignore in UCI mode
                    break;
            }
        }

        private void HandleUCI()
        {
            Console.WriteLine($"id name C0BR4 {EngineVersion}");
            Console.WriteLine("id author C0BR4 Developer");
            // TODO: Add UCI options here
            Console.WriteLine("uciok");
        }

        private void HandlePosition(string[] parts)
        {
            if (parts.Length < 2) return;

            if (parts[1] == "startpos")
            {
                board.LoadStartPosition();
                
                // Apply moves if provided
                int movesIndex = Array.IndexOf(parts, "moves");
                if (movesIndex != -1 && movesIndex + 1 < parts.Length)
                {
                    for (int i = movesIndex + 1; i < parts.Length; i++)
                    {
                        if (TryParseAndApplyMove(parts[i]))
                        {
                            Console.WriteLine($"info string Applied move: {parts[i]}");
                        }
                        else
                        {
                            Console.WriteLine($"info string Failed to apply move: {parts[i]}");
                        }
                    }
                }
            }
            else if (parts[1] == "fen" && parts.Length >= 8)
            {
                // Reconstruct FEN string
                string fen = string.Join(" ", parts, 2, 6);
                board.LoadPosition(fen);
                
                // Apply moves if provided
                int movesIndex = Array.IndexOf(parts, "moves");
                if (movesIndex != -1 && movesIndex + 1 < parts.Length)
                {
                    for (int i = movesIndex + 1; i < parts.Length; i++)
                    {
                        if (TryParseAndApplyMove(parts[i]))
                        {
                            Console.WriteLine($"info string Applied move: {parts[i]}");
                        }
                        else
                        {
                            Console.WriteLine($"info string Failed to apply move: {parts[i]}");
                        }
                    }
                }
            }
        }

        private void HandleGo(string[] parts)
        {
            // Parse time control parameters using TimeManager
            var timeControl = TimeManager.ParseTimeControl(parts);
            
            // Calculate game phase for time allocation
            double gamePhase = GamePhase.CalculatePhase(board);
            
            // Determine time allocation
            int timeAllocation;
            
            if (timeControl.Depth > 0)
            {
                // Fixed depth search - use generous time limit
                timeAllocation = 30000; // 30 seconds
            }
            else if (timeControl.Infinite)
            {
                // Infinite search - use very generous time limit
                timeAllocation = 300000; // 5 minutes
            }
            else
            {
                // Calculate optimal time allocation
                timeAllocation = TimeManager.CalculateTimeAllocation(timeControl, board.IsWhiteToMove, gamePhase);
            }
            
            // Apply material balance time multiplier
            double materialMultiplier = GamePhase.GetMaterialTimeMultiplier(board);
            timeAllocation = (int)(timeAllocation * materialMultiplier);
            
            // Output time management info for debugging
            Console.WriteLine($"info string Game phase: {GamePhase.GetPhaseName(board)} ({gamePhase:F2})");
            Console.WriteLine($"info string Time allocation: {timeAllocation}ms");
            if (timeControl.WhiteTime > 0 || timeControl.BlackTime > 0)
            {
                int remainingTime = board.IsWhiteToMove ? timeControl.WhiteTime : timeControl.BlackTime;
                Console.WriteLine($"info string Remaining time: {remainingTime}ms");
            }

            // Start search with time limit
            try
            {
                // Check opening book first
                string? bookMove = OpeningBook.GetOpeningMove(board);
                
                if (bookMove != null && OpeningBook.IsInOpeningPhase(board))
                {
                    // Try to parse and play the book move
                    var move = AlgebraicNotation.ParseMove(board, bookMove);
                    
                    if (move != null)
                    {
                        Console.WriteLine($"info string Opening book: {bookMove}");
                        Console.WriteLine($"bestmove {move}");
                        return;
                    }
                    
                    // If book move not found in legal moves, fall through to search
                    Console.WriteLine($"info string Book move {bookMove} not found, using search");
                }
                
                // Fall back to engine search
                var timeSpan = TimeSpan.FromMilliseconds(timeAllocation);
                Move bestMove = bot.Think(board, timeSpan);
                
                // Check if we got a valid move
                if (bestMove.IsNull || !IsValidMove(bestMove))
                {
                    Console.WriteLine($"info string Warning: Got invalid move {bestMove}, searching for any legal move");
                    var legalMoves = board.GetLegalMoves();
                    if (legalMoves.Length > 0)
                    {
                        bestMove = legalMoves[0]; // Take any legal move as fallback
                        Console.WriteLine($"info string Using fallback move: {bestMove}");
                    }
                    else
                    {
                        Console.WriteLine("bestmove (none)"); // No legal moves available
                        return;
                    }
                }
                
                Console.WriteLine($"bestmove {bestMove}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"info string Error: {ex.Message}");
                Console.WriteLine("bestmove (none)"); // Use proper UCI format for no move
            }
        }

        /// <summary>
        /// Validate that a move is legal in the current position using bitboard validation
        /// </summary>
        private bool IsValidMove(Move move)
        {
            if (move.IsNull) return false;
            
            // Use our bitboard-based validation - this is the key fix!
            return board.IsLegalMove(move);
        }

        private void DebugPosition()
        {
            Console.WriteLine("=== POSITION DEBUG ===");
            Console.WriteLine($"FEN: {board.GetFEN()}");
            Console.WriteLine($"Turn: {(board.IsWhiteToMove ? "White" : "Black")}");
            
            var legalMoves = board.GetLegalMoves();
            Console.WriteLine($"Legal moves ({legalMoves.Length}):");
            for (int i = 0; i < Math.Min(20, legalMoves.Length); i++)
            {
                Console.WriteLine($"  {legalMoves[i]}");
            }
            if (legalMoves.Length > 20)
            {
                Console.WriteLine($"  ... and {legalMoves.Length - 20} more");
            }
        }

        private void RunBitboardValidationTests()
        {
            Console.WriteLine("Running bitboard validation tests...");
            
            // Test current position
            var legalMoves = board.GetLegalMoves();
            Console.WriteLine($"Current position has {legalMoves.Length} legal moves");
            
            // Test each legal move
            int validMoves = 0;
            foreach (var move in legalMoves)
            {
                if (board.IsLegalMove(move))
                {
                    validMoves++;
                }
                else
                {
                    Console.WriteLine($"WARNING: Move {move} is in legal moves list but fails IsLegalMove check!");
                }
            }
            
            Console.WriteLine($"Validation: {validMoves}/{legalMoves.Length} moves passed IsLegalMove check");
        }

        private void TestPosition()
        {
            Console.WriteLine("=== MOVE VALIDATION TEST ===");
            var legalMoves = board.GetLegalMoves();
            Console.WriteLine($"Position has {legalMoves.Length} legal moves");
            
            // Test a few moves
            for (int i = 0; i < Math.Min(5, legalMoves.Length); i++)
            {
                var move = legalMoves[i];
                bool isValid = board.IsLegalMove(move);
                Console.WriteLine($"Move {move}: {(isValid ? "VALID" : "INVALID")}");
            }
        }

        private void TestSpecificMove(string[] parts)
        {
            if (parts.Length > 1)
            {
                try
                {
                    // CRITICAL FIX: Use ParseUciMove instead of Move constructor
                    var move = ParseUciMove(parts[1]);
                    if (move == null)
                    {
                        Console.WriteLine($"Move {parts[1]} is INVALID (not found in legal moves)");
                        return;
                    }
                    
                    bool isValid = board.IsLegalMove(move.Value);
                    Console.WriteLine($"Move {parts[1]} is {(isValid ? "VALID" : "INVALID")}");
                    
                    // Also check if it's in the legal moves list
                    var legalMoves = board.GetLegalMoves();
                    bool inLegalList = false;
                    foreach (var legalMove in legalMoves)
                    {
                        if (move.Value.Equals(legalMove))
                        {
                            inLegalList = true;
                            break;
                        }
                    }
                    Console.WriteLine($"Move {parts[1]} is {(inLegalList ? "in" : "NOT in")} legal moves list");
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error parsing move {parts[1]}: {ex.Message}");
                }
            }
            else
            {
                Console.WriteLine("Usage: testmove <move> (e.g., testmove e2e4)");
            }
        }

        private void DisplayBoard()
        {
            // TODO: Implement board display
            Console.WriteLine("Board display not yet implemented");
            Console.WriteLine($"Position: {board.IsWhiteToMove} to move");
            
            // Show move count for now
            var pseudoMoves = board.GetPseudoLegalMoves();
            var legalMoves = board.GetLegalMoves();
            Console.WriteLine($"Pseudo-legal moves: {pseudoMoves.Length}");
            Console.WriteLine($"Legal moves: {legalMoves.Length}");
            
            // Show first few legal moves
            for (int i = 0; i < Math.Min(10, legalMoves.Length); i++)
            {
                Console.WriteLine($"  {legalMoves[i]}");
            }
            if (legalMoves.Length > 10)
            {
                Console.WriteLine($"  ... and {legalMoves.Length - 10} more");
            }
        }

        private void RunBenchmark()
        {
            Console.WriteLine("Running performance benchmark...");
            PerformanceBenchmark.BenchmarkMoveGeneration(1000);
        }

        private void RunPerft(string[] parts)
        {
            if (parts.Length > 1 && int.TryParse(parts[1], out int depth))
            {
                Console.WriteLine($"Running perft to depth {depth}...");
                var stopwatch = System.Diagnostics.Stopwatch.StartNew();
                long nodes = PerformanceBenchmark.Perft(board, depth);
                stopwatch.Stop();
                Console.WriteLine($"Perft({depth}): {nodes} nodes in {stopwatch.ElapsedMilliseconds}ms");
            }
            else
            {
                PerformanceBenchmark.RunPerftTests();
            }
        }

        private bool TryParseAndApplyMove(string moveString)
        {
            try
            {
                // Parse UCI move with proper board context
                var move = ParseUciMove(moveString);
                
                if (move == null)
                {
                    Console.WriteLine($"ERROR: Could not parse UCI move {moveString}");
                    return false;
                }
                
                // Use bitboard-based validation - this is our critical fix!
                if (!board.IsLegalMove(move.Value))
                {
                    Console.WriteLine($"ERROR: Move {moveString} is not legal in current position");
                    return false;
                }
                
                // Make the move using bitboard system
                board.MakeMove(move.Value);
                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: Exception while parsing move {moveString}: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Parse a UCI move string (like "e2e4", "e1g1", "e7e8q") into a proper Move object
        /// with full board context including piece types and move flags
        /// </summary>
        private Move? ParseUciMove(string uciMove)
        {
            if (string.IsNullOrEmpty(uciMove) || uciMove.Length < 4)
                return null;

            try
            {
                // Parse source and target squares
                string fromSquare = uciMove.Substring(0, 2);
                string toSquare = uciMove.Substring(2, 2);
                
                int fromIndex = ParseSquareIndex(fromSquare);
                int toIndex = ParseSquareIndex(toSquare);
                
                if (fromIndex < 0 || toIndex < 0)
                    return null;

                // Get all legal moves and find the matching one
                var legalMoves = board.GetLegalMoves();
                
                foreach (var legalMove in legalMoves)
                {
                    if (legalMove.StartSquare.Index == fromIndex && 
                        legalMove.TargetSquare.Index == toIndex)
                    {
                        // Check for promotion
                        if (uciMove.Length == 5)
                        {
                            PieceType promotionType = uciMove[4] switch
                            {
                                'q' => PieceType.Queen,
                                'r' => PieceType.Rook,
                                'b' => PieceType.Bishop,
                                'n' => PieceType.Knight,
                                _ => PieceType.None
                            };
                            
                            // Only return if promotion piece matches
                            if (legalMove.PromotionPieceType == promotionType)
                                return legalMove;
                        }
                        else
                        {
                            // No promotion, so this should be a non-promotion move
                            if (legalMove.PromotionPieceType == PieceType.None)
                                return legalMove;
                        }
                    }
                }

                return null;
            }
            catch (Exception)
            {
                return null;
            }
        }

        /// <summary>
        /// Parse a square string like "e4" into a square index (0-63)
        /// </summary>
        private int ParseSquareIndex(string square)
        {
            if (string.IsNullOrEmpty(square) || square.Length != 2)
                return -1;

            char file = square[0];
            char rank = square[1];

            if (file < 'a' || file > 'h' || rank < '1' || rank > '8')
                return -1;

            int fileIndex = file - 'a';
            int rankIndex = rank - '1';
            
            return rankIndex * 8 + fileIndex;
        }

        private void RunEval()
        {
            var evaluator = new Evaluation.SimpleEvaluator();
            int evaluation = evaluator.Evaluate(board);
            Console.WriteLine($"Evaluation: {evaluation} cp ({evaluation / 100.0:F2} pawns) from {(board.IsWhiteToMove ? "white" : "black")} perspective");
        }

        private void SetDepth(string[] parts)
        {
            if (parts.Length > 1 && int.TryParse(parts[1], out int depth))
            {
                if (bot is SimpleSearchBot simpleBot)
                {
                    simpleBot.SetDepth(depth);
                    Console.WriteLine($"info string Search depth set to {depth}");
                }
                else if (bot is AlphaBetaSearchBot alphabetaBot)
                {
                    alphabetaBot.SetDepth(depth);
                    Console.WriteLine($"info string Search depth set to {depth}");
                }
            }
            else
            {
                Console.WriteLine("Usage: depth <number>");
            }
        }

        private void SetEngine(string[] parts)
        {
            if (parts.Length > 1)
            {
                switch (parts[1].ToLower())
                {
                    case "random":
                        bot = new RandomBot();
                        Console.WriteLine("info string Engine set to RandomBot");
                        break;
                    case "simple":
                        bot = new SimpleSearchBot();
                        Console.WriteLine("info string Engine set to SimpleSearchBot (negamax)");
                        break;
                    case "alphabeta":
                    case "ab":
                        bot = new AlphaBetaSearchBot();
                        Console.WriteLine("info string Engine set to AlphaBetaSearchBot");
                        break;
                    default:
                        Console.WriteLine("Available engines: random, simple, alphabeta");
                        break;
                }
            }
            else
            {
                Console.WriteLine("Current engine: " + bot.GetType().Name);
                Console.WriteLine("Available engines: random, simple, alphabeta");
            }
        }
    }
}
