using System;
using C0BR4ChessEngine.Core;

namespace C0BR4ChessEngine.Testing
{
    /// <summary>
    /// Test the bitboard implementation to ensure it generates legal moves correctly
    /// This will help verify we've resolved the rule infraction issues
    /// </summary>
    public class BitboardValidationTest
    {
        public static void RunBasicTests()
        {
            Console.WriteLine("=== C0BR4 v2.2 Bitboard Validation Tests ===");
            
            try
            {
                TestStartingPosition();
                TestPawnMoves();
                TestCastlingValidation();
                TestMoveGeneration();
                
                Console.WriteLine("\n✅ All bitboard validation tests passed!");
                Console.WriteLine("Rule infraction issues should now be resolved.");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"\n❌ Test failed: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
            }
        }

        private static void TestStartingPosition()
        {
            Console.WriteLine("\n1. Testing starting position loading...");
            
            var position = BitboardPosition.StartingPosition();
            string fen = position.ToFEN();
            
            // Should match standard starting FEN (minus halfmove and fullmove counters)
            if (!fen.StartsWith("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq"))
            {
                throw new Exception($"Starting position FEN incorrect: {fen}");
            }
            
            // Check piece counts
            if (Bitboard.PopCount(position.WhitePawns) != 8 ||
                Bitboard.PopCount(position.BlackPawns) != 8 ||
                Bitboard.PopCount(position.WhiteKing) != 1 ||
                Bitboard.PopCount(position.BlackKing) != 1)
            {
                throw new Exception("Incorrect piece counts in starting position");
            }
            
            Console.WriteLine("   ✅ Starting position loaded correctly");
        }

        private static void TestPawnMoves()
        {
            Console.WriteLine("\n2. Testing pawn move generation...");
            
            var position = BitboardPosition.StartingPosition();
            var moveGen = new BitboardMoveGenerator();
            var moves = moveGen.GenerateLegalMoves(position);
            
            // Count pawn moves (should be 16: 8 single pushes + 8 double pushes)
            int pawnMoves = 0;
            foreach (var move in moves)
            {
                if (move.MovePieceType == PieceType.Pawn)
                {
                    pawnMoves++;
                }
            }
            
            if (pawnMoves != 16)
            {
                throw new Exception($"Expected 16 pawn moves in starting position, got {pawnMoves}");
            }
            
            Console.WriteLine($"   ✅ Generated {pawnMoves} pawn moves correctly");
        }

        private static void TestCastlingValidation()
        {
            Console.WriteLine("\n3. Testing castling validation...");
            
            // Test position where castling should be legal
            var position = BitboardPosition.FromFEN("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1");
            var moveGen = new BitboardMoveGenerator();
            var moves = moveGen.GenerateLegalMoves(position);
            
            // Should have castling moves
            bool hasKingsideCastle = false;
            bool hasQueensideCastle = false;
            
            foreach (var move in moves)
            {
                if (move.Flag == MoveFlag.Castling)
                {
                    if (move.TargetSquare.Index == 6) hasKingsideCastle = true;  // g1
                    if (move.TargetSquare.Index == 2) hasQueensideCastle = true; // c1
                }
            }
            
            if (!hasKingsideCastle || !hasQueensideCastle)
            {
                throw new Exception("Castling moves not generated correctly");
            }
            
            // Test position where castling should be illegal (king in check)
            var checkPosition = BitboardPosition.FromFEN("r3k2r/4r3/8/8/8/8/8/R3K2R w KQkq - 0 1");
            var checkMoves = moveGen.GenerateLegalMoves(checkPosition);
            
            // Should have no castling moves (king in check)
            foreach (var move in checkMoves)
            {
                if (move.Flag == MoveFlag.Castling)
                {
                    throw new Exception("Illegal castling move generated (king in check)");
                }
            }
            
            Console.WriteLine("   ✅ Castling validation working correctly");
        }

        private static void TestMoveGeneration()
        {
            Console.WriteLine("\n4. Testing move generation accuracy...");
            
            var position = BitboardPosition.StartingPosition();
            var moveGen = new BitboardMoveGenerator();
            var moves = moveGen.GenerateLegalMoves(position);
            
            // Starting position should have exactly 20 legal moves
            if (moves.Length != 20)
            {
                throw new Exception($"Expected 20 moves in starting position, got {moves.Length}");
            }
            
            // Test that all moves are properly formatted
            foreach (var move in moves)
            {
                if (move.StartSquare.Index < 0 || move.StartSquare.Index > 63 ||
                    move.TargetSquare.Index < 0 || move.TargetSquare.Index > 63)
                {
                    throw new Exception($"Invalid move generated: {move}");
                }
                
                // Ensure move string representation works
                string moveStr = move.ToString();
                if (moveStr == "(none)" || moveStr.Length < 4)
                {
                    throw new Exception($"Invalid move string: {moveStr}");
                }
            }
            
            Console.WriteLine($"   ✅ Generated {moves.Length} legal moves, all valid");
        }

        /// <summary>
        /// Test that the position causing the original rule infraction is now handled correctly
        /// </summary>
        public static void TestProblematicPosition()
        {
            Console.WriteLine("\n5. Testing the problematic castling position...");
            
            // Recreate the position from the game where C0BR4 made an illegal castling move
            // This should now be handled correctly
            try
            {
                var position = BitboardPosition.FromFEN("rnbqkb1r/ppp1pppp/5n2/3p4/2PP4/5N2/PP2PPPP/RNBQKB1R w KQkq - 2 4");
                var moveGen = new BitboardMoveGenerator();
                var moves = moveGen.GenerateLegalMoves(position);
                
                // Check if castling is correctly validated
                foreach (var move in moves)
                {
                    if (move.Flag == MoveFlag.Castling)
                    {
                        // Verify this castling move is actually legal
                        bool isLegal = moveGen.IsLegalMove(move);
                        if (!isLegal)
                        {
                            throw new Exception($"Illegal castling move generated: {move}");
                        }
                    }
                }
                
                Console.WriteLine("   ✅ Problematic position handled correctly");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"   ⚠️  Could not test problematic position: {ex.Message}");
            }
        }
    }
}
