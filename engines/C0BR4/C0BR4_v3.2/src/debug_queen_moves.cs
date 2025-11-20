using System;
using C0BR4ChessEngine.Core;

namespace C0BR4ChessEngine.Debug
{
    class DebugQueenMoves
    {
        static void DebugMain(string[] args)
        {
            // Initialize magic bitboards
            MagicBitboards.Initialize();
            
            // Create test position: rnbqkbnr/pppp1ppp/8/4p3/Q7/8/PPPPPPPP/RNB1KBNR w KQkq e6 0 2
            var position = BitboardPosition.FromFEN("rnbqkbnr/pppp1ppp/8/4p3/Q7/8/PPPPPPPP/RNB1KBNR w KQkq e6 0 2");
            
            Console.WriteLine($"Position loaded: {position.ToFEN()}");
            Console.WriteLine($"White to move: {position.IsWhiteToMove}");
            
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
            
            // Convert to square list
            Console.WriteLine("Legal queen moves from a4:");
            ulong moves = legalMoves;
            while (moves != 0)
            {
                int toSquare = Bitboard.PopLSB(ref moves);
                string squareName = SquareToString(toSquare);
                var (piece, color) = position.GetPieceAt(toSquare);
                string capture = piece != PieceType.None ? $" (captures {piece})" : "";
                Console.WriteLine($"  a4-{squareName}{capture}");
                
                // Check if this is the illegal move a4-a1
                if (toSquare == 0) // a1
                {
                    Console.WriteLine("    *** This is the illegal move a4-a1! ***");
                    
                    // Let's check what's between a4 and a1
                    Console.WriteLine("    Checking path from a4 to a1:");
                    for (int sq = 8; sq < 24; sq += 8) // a2, a3
                    {
                        var (pathPiece, pathColor) = position.GetPieceAt(sq);
                        string pathSquare = SquareToString(sq);
                        Console.WriteLine($"      {pathSquare}: {pathPiece} ({pathColor})");
                    }
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
