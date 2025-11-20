using System;
using System.Runtime.CompilerServices;

namespace C0BR4ChessEngine.Core
{
    /// <summary>
    /// Core bitboard operations and utilities for efficient chess position representation
    /// Each bit in a 64-bit integer represents a square on the chess board
    /// </summary>
    public static class Bitboard
    {
        // File masks (columns a-h)
        public static readonly ulong FileA = 0x0101010101010101UL;
        public static readonly ulong FileB = 0x0202020202020202UL;
        public static readonly ulong FileC = 0x0404040404040404UL;
        public static readonly ulong FileD = 0x0808080808080808UL;
        public static readonly ulong FileE = 0x1010101010101010UL;
        public static readonly ulong FileF = 0x2020202020202020UL;
        public static readonly ulong FileG = 0x4040404040404040UL;
        public static readonly ulong FileH = 0x8080808080808080UL;

        // Rank masks (rows 1-8)
        public static readonly ulong Rank1 = 0x00000000000000FFUL;
        public static readonly ulong Rank2 = 0x000000000000FF00UL;
        public static readonly ulong Rank3 = 0x0000000000FF0000UL;
        public static readonly ulong Rank4 = 0x00000000FF000000UL;
        public static readonly ulong Rank5 = 0x000000FF00000000UL;
        public static readonly ulong Rank6 = 0x0000FF0000000000UL;
        public static readonly ulong Rank7 = 0x00FF000000000000UL;
        public static readonly ulong Rank8 = 0xFF00000000000000UL;

        // Edge masks
        public static readonly ulong NotFileA = ~FileA;
        public static readonly ulong NotFileH = ~FileH;
        public static readonly ulong NotFileAB = NotFileA & ~FileB;
        public static readonly ulong NotFileGH = ~FileG & ~FileH;

        // Corner and center masks
        public static readonly ulong Center = 0x0000001818000000UL; // e4, d4, e5, d5
        public static readonly ulong ExtendedCenter = 0x00003C3C3C3C0000UL;
        public static readonly ulong Corners = 0x8100000000000081UL; // a1, h1, a8, h8

        // Castling squares
        public static readonly ulong WhiteKingsideCastleSquares = 0x0000000000000060UL; // f1, g1
        public static readonly ulong WhiteQueensideCastleSquares = 0x000000000000000EUL; // b1, c1, d1
        public static readonly ulong BlackKingsideCastleSquares = 0x6000000000000000UL; // f8, g8
        public static readonly ulong BlackQueensideCastleSquares = 0x0E00000000000000UL; // b8, c8, d8

        /// <summary>
        /// Convert square index (0-63) to bitboard with single bit set
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong SquareToBitboard(int square)
        {
            return 1UL << square;
        }

        /// <summary>
        /// Get square index from file and rank (0-based)
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static int GetSquare(int file, int rank)
        {
            return rank * 8 + file;
        }

        /// <summary>
        /// Get file (0-7) from square index
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static int GetFile(int square)
        {
            return square & 7;
        }

        /// <summary>
        /// Get rank (0-7) from square index
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static int GetRank(int square)
        {
            return square >> 3;
        }

        /// <summary>
        /// Count the number of set bits (population count)
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static int PopCount(ulong bitboard)
        {
            return System.Numerics.BitOperations.PopCount(bitboard);
        }

        /// <summary>
        /// Get index of least significant bit (first set bit from right)
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static int TrailingZeroCount(ulong bitboard)
        {
            return System.Numerics.BitOperations.TrailingZeroCount(bitboard);
        }

        /// <summary>
        /// Get index of most significant bit (first set bit from left)
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static int LeadingZeroCount(ulong bitboard)
        {
            return System.Numerics.BitOperations.LeadingZeroCount(bitboard);
        }

        /// <summary>
        /// Pop least significant bit and return its index
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static int PopLSB(ref ulong bitboard)
        {
            int square = TrailingZeroCount(bitboard);
            bitboard &= bitboard - 1; // Clear LSB
            return square;
        }

        /// <summary>
        /// Get least significant bit index without modifying the bitboard
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static int LSB(ulong bitboard)
        {
            return TrailingZeroCount(bitboard);
        }

        /// <summary>
        /// Shift bitboard north (towards rank 8)
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong ShiftNorth(ulong bitboard)
        {
            return bitboard << 8;
        }

        /// <summary>
        /// Shift bitboard south (towards rank 1)
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong ShiftSouth(ulong bitboard)
        {
            return bitboard >> 8;
        }

        /// <summary>
        /// Shift bitboard east (towards h-file)
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong ShiftEast(ulong bitboard)
        {
            return (bitboard & NotFileH) << 1;
        }

        /// <summary>
        /// Shift bitboard west (towards a-file)
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong ShiftWest(ulong bitboard)
        {
            return (bitboard & NotFileA) >> 1;
        }

        /// <summary>
        /// Shift bitboard northeast
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong ShiftNorthEast(ulong bitboard)
        {
            return (bitboard & NotFileH) << 9;
        }

        /// <summary>
        /// Shift bitboard northwest
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong ShiftNorthWest(ulong bitboard)
        {
            return (bitboard & NotFileA) << 7;
        }

        /// <summary>
        /// Shift bitboard southeast
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong ShiftSouthEast(ulong bitboard)
        {
            return (bitboard & NotFileH) >> 7;
        }

        /// <summary>
        /// Shift bitboard southwest
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong ShiftSouthWest(ulong bitboard)
        {
            return (bitboard & NotFileA) >> 9;
        }

        /// <summary>
        /// Generate white pawn attacks from given pawn positions
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong WhitePawnAttacks(ulong pawns)
        {
            return ShiftNorthEast(pawns) | ShiftNorthWest(pawns);
        }

        /// <summary>
        /// Generate black pawn attacks from given pawn positions
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong BlackPawnAttacks(ulong pawns)
        {
            return ShiftSouthEast(pawns) | ShiftSouthWest(pawns);
        }

        /// <summary>
        /// Generate king attacks from a king position
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong KingAttacks(int kingSquare)
        {
            ulong king = SquareToBitboard(kingSquare);
            return ShiftNorth(king) | ShiftSouth(king) | ShiftEast(king) | ShiftWest(king) |
                   ShiftNorthEast(king) | ShiftNorthWest(king) | ShiftSouthEast(king) | ShiftSouthWest(king);
        }

        /// <summary>
        /// Generate knight attacks from a knight position
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong KnightAttacks(int knightSquare)
        {
            ulong knight = SquareToBitboard(knightSquare);
            
            return ((knight & NotFileGH) << 10) | // 2 up, 2 right
                   ((knight & NotFileAB) << 6) |  // 2 up, 2 left
                   ((knight & NotFileH) << 17) |  // 1 up, 2 right
                   ((knight & NotFileA) << 15) |  // 1 up, 2 left
                   ((knight & NotFileGH) >> 6) |  // 2 down, 2 right
                   ((knight & NotFileAB) >> 10) | // 2 down, 2 left
                   ((knight & NotFileH) >> 15) |  // 1 down, 2 right
                   ((knight & NotFileA) >> 17);   // 1 down, 2 left
        }

        /// <summary>
        /// Print bitboard for debugging (shows as chess board)
        /// </summary>
        public static string Print(ulong bitboard)
        {
            var result = new System.Text.StringBuilder();
            result.AppendLine("  a b c d e f g h");
            
            for (int rank = 7; rank >= 0; rank--)
            {
                result.Append($"{rank + 1} ");
                for (int file = 0; file < 8; file++)
                {
                    int square = GetSquare(file, rank);
                    char symbol = ((bitboard >> square) & 1) == 1 ? 'X' : '.';
                    result.Append($"{symbol} ");
                }
                result.AppendLine($"{rank + 1}");
            }
            
            result.AppendLine("  a b c d e f g h");
            return result.ToString();
        }

        /// <summary>
        /// Check if a square is on the edge of the board
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static bool IsEdgeSquare(int square)
        {
            int file = GetFile(square);
            int rank = GetRank(square);
            return file == 0 || file == 7 || rank == 0 || rank == 7;
        }

        /// <summary>
        /// Get distance between two squares (Chebyshev distance)
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static int Distance(int square1, int square2)
        {
            int file1 = GetFile(square1), rank1 = GetRank(square1);
            int file2 = GetFile(square2), rank2 = GetRank(square2);
            return Math.Max(Math.Abs(file1 - file2), Math.Abs(rank1 - rank2));
        }

        /// <summary>
        /// Get Manhattan distance between two squares
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static int ManhattanDistance(int square1, int square2)
        {
            int file1 = GetFile(square1), rank1 = GetRank(square1);
            int file2 = GetFile(square2), rank2 = GetRank(square2);
            return Math.Abs(file1 - file2) + Math.Abs(rank1 - rank2);
        }
    }
}
