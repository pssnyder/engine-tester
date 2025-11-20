using System;
using C0BR4ChessEngine.Core;
using C0BR4ChessEngine.Search;

namespace C0BR4ChessEngine.Testing
{
    /// <summary>
    /// Testing utility to validate moves and debug illegal move issues
    /// </summary>
    public static class MoveValidationTester
    {
        /// <summary>
        /// Test the engine's move generation and validation in a given position
        /// </summary>
        public static void TestPosition(Board board)
        {
            Console.WriteLine("=== Move Validation Test ===");
            Console.WriteLine($"Position: {(board.IsWhiteToMove ? "White" : "Black")} to move");
            Console.WriteLine($"In check: {board.IsInCheck()}");
            
            // Test move generation
            var pseudoMoves = board.GetPseudoLegalMoves();
            var legalMoves = board.GetLegalMoves();
            
            Console.WriteLine($"Pseudo-legal moves: {pseudoMoves.Length}");
            Console.WriteLine($"Legal moves: {legalMoves.Length}");
            
            if (legalMoves.Length == 0)
            {
                if (board.IsInCheck())
                {
                    Console.WriteLine("Position is CHECKMATE");
                }
                else
                {
                    Console.WriteLine("Position is STALEMATE");
                }
                return;
            }
            
            // Show all legal moves
            Console.WriteLine("Legal moves:");
            for (int i = 0; i < legalMoves.Length; i++)
            {
                Console.WriteLine($"  {i + 1}. {legalMoves[i]}");
            }
            
            // Test engine move selection
            Console.WriteLine("\n=== Engine Testing ===");
            var engine = new TranspositionSearchBot();
            
            try
            {
                var bestMove = engine.Think(board, TimeSpan.FromSeconds(1));
                Console.WriteLine($"Engine selected: {bestMove}");
                
                // Validate the engine's move
                bool isLegal = false;
                foreach (var legal in legalMoves)
                {
                    if (bestMove.Equals(legal))
                    {
                        isLegal = true;
                        break;
                    }
                }
                
                if (isLegal)
                {
                    Console.WriteLine("✓ Engine move is LEGAL");
                }
                else
                {
                    Console.WriteLine("✗ Engine move is ILLEGAL!");
                    Console.WriteLine($"Move details: {bestMove}");
                    Console.WriteLine($"Is null: {bestMove.IsNull}");
                    Console.WriteLine($"Start square: {bestMove.StartSquare.Name} ({bestMove.StartSquare.Index})");
                    Console.WriteLine($"Target square: {bestMove.TargetSquare.Name} ({bestMove.TargetSquare.Index})");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"✗ Engine error: {ex.Message}");
            }
        }
        
        /// <summary>
        /// Test a specific move in a position
        /// </summary>
        public static bool ValidateMove(Board board, Move move)
        {
            if (move.IsNull)
            {
                Console.WriteLine("Move is null");
                return false;
            }
            
            // Check basic move validity
            if (move.StartSquare.Index < 0 || move.StartSquare.Index > 63 ||
                move.TargetSquare.Index < 0 || move.TargetSquare.Index > 63)
            {
                Console.WriteLine($"Invalid square indices: {move.StartSquare.Index} -> {move.TargetSquare.Index}");
                return false;
            }
            
            // Check if move is in legal moves list
            var legalMoves = board.GetLegalMoves();
            foreach (var legal in legalMoves)
            {
                if (move.Equals(legal))
                {
                    return true;
                }
            }
            
            Console.WriteLine($"Move {move} not found in legal moves list");
            return false;
        }
        
        /// <summary>
        /// Run comprehensive tests on common positions
        /// </summary>
        public static void RunComprehensiveTests()
        {
            Console.WriteLine("=== Comprehensive Move Validation Tests ===\n");
            
            // Test starting position
            Console.WriteLine("1. Testing starting position:");
            var startBoard = new Board();
            startBoard.LoadStartPosition();
            TestPosition(startBoard);
            
            Console.WriteLine("\n" + new string('=', 50) + "\n");
            
            // Test a middle game position (from one of the problematic games)
            Console.WriteLine("2. Testing middle game position:");
            var midBoard = new Board();
            midBoard.LoadPosition("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1");
            TestPosition(midBoard);
            
            Console.WriteLine("\n" + new string('=', 50) + "\n");
            
            // Test endgame position
            Console.WriteLine("3. Testing king and pawn endgame:");
            var endBoard = new Board();
            endBoard.LoadPosition("8/8/8/8/8/8/K1k5/8 w - - 0 1");
            TestPosition(endBoard);
        }
    }
}
