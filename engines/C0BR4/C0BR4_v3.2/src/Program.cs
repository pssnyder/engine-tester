using C0BR4ChessEngine.UCI;
using C0BR4ChessEngine.Core;
using System;

namespace C0BR4ChessEngine
{
    /// <summary>
    /// Main entry point for the chess engine
    /// </summary>
    class Program
    {
        static void Main(string[] args)
        {
            // CRITICAL FIX: Always initialize magic bitboards before starting UCI engine
            // This was the root cause of illegal moves - uninitialized lookup tables!
            MagicBitboards.Initialize();
            
            if (args.Length > 0 && args[0] == "debug-queen")
            {
                DebugQueenMoves();
                return;
            }
            
            var engine = new UCIEngine();
            engine.Run();
        }
        
        static void DebugQueenMoves()
        {
            // Create test position: rnbqkbnr/pppp1ppp/8/4p3/Q7/8/PPPPPPPP/RNB1KBNR w KQkq e6 0 2
            var position = BitboardPosition.FromFEN("rnbqkbnr/pppp1ppp/8/4p3/Q7/8/PPPPPPPP/RNB1KBNR w KQkq e6 0 2");
            
            Console.WriteLine($"Position loaded: {position.ToFEN()}");
            Console.WriteLine($"White to move: {position.IsWhiteToMove}");
            
            // Test with actual move generator
            var moveGen = new BitboardMoveGenerator();
            var moves = moveGen.GenerateLegalMoves(position);
            
            Console.WriteLine($"Total moves generated: {moves.Length}");
            Console.WriteLine("All moves:");
            foreach (var move in moves)
            {
                string fromSquare = SquareToString(move.StartSquare.Index);
                string toSquare = SquareToString(move.TargetSquare.Index);
                string moveStr = $"{fromSquare}{toSquare}";
                
                if (move.StartSquare.Index == 24) // Queen moves from a4
                {
                    Console.WriteLine($"  QUEEN MOVE: {moveStr}");
                    if (move.TargetSquare.Index == 0) // a4-a1
                    {
                        Console.WriteLine($"    *** ILLEGAL QUEEN MOVE FOUND: {moveStr} ***");
                    }
                }
                else
                {
                    Console.WriteLine($"  {moveStr}");
                }
            }
            
            // Also test individual queen move generation
            Console.WriteLine("\n=== Manual Queen Move Analysis ===");
            
            // Queen is on a4 (square 24)
            int queenSquare = 24; // a4
            Console.WriteLine($"Queen on square {queenSquare} (a4)");
            
            // Get queen attacks
            ulong queenAttacks = MagicBitboards.GetQueenAttacks(queenSquare, position.AllPieces);
            Console.WriteLine($"Queen attacks bitboard: 0x{queenAttacks:X16}");
            
            // Get friendly pieces
            ulong friendlyPieces = position.GetAllPieces(true); // white pieces
            Console.WriteLine($"Friendly pieces bitboard: 0x{friendlyPieces:X16}");
            
            // Get legal queen moves (attacks minus friendly pieces)
            ulong legalMoves = queenAttacks & ~friendlyPieces;
            Console.WriteLine($"Legal moves bitboard: 0x{legalMoves:X16}");
            
            // Check occupancy on the a-file specifically
            Console.WriteLine("Pieces on a-file (file 0):");
            for (int rank = 0; rank < 8; rank++)
            {
                int square = rank * 8; // a1, a2, a3, a4, a5, a6, a7, a8
                var (piece, color) = position.GetPieceAt(square);
                string squareName = SquareToString(square);
                if (piece != PieceType.None)
                {
                    Console.WriteLine($"  {squareName}: {piece} ({color})");
                }
                else
                {
                    Console.WriteLine($"  {squareName}: empty");
                }
            }
            
            // Convert to square list
            Console.WriteLine("Legal queen moves from a4:");
            ulong moves2 = legalMoves;
            while (moves2 != 0)
            {
                int toSquare = Bitboard.PopLSB(ref moves2);
                string squareName = SquareToString(toSquare);
                var (piece, color) = position.GetPieceAt(toSquare);
                string capture = piece != PieceType.None ? $" (captures {piece})" : "";
                Console.WriteLine($"  a4-{squareName}{capture}");
                
                // Check if this is the illegal move a4-a1
                if (toSquare == 0) // a1
                {
                    Console.WriteLine("    *** This is the illegal move a4-a1! ***");
                    Console.WriteLine("    There should be pieces blocking this path!");
                }
            }
        }
        
        static string SquareToString(int square)
        {
            int file = square % 8;
            int rank = square / 8;
            return $"{(char)('a' + file)}{rank + 1}";
        }
    }
}
