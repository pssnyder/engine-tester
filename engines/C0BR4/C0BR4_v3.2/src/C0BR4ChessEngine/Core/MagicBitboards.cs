using System;
using System.Runtime.CompilerServices;

namespace C0BR4ChessEngine.Core
{
    /// <summary>
    /// CLEAN Magic Bitboards v2.8 - Simple Ray-Based Attack Generation
    /// Replaces complex magic bitboard lookup with reliable ray casting
    /// Priority: CORRECTNESS over performance to eliminate illegal moves
    /// </summary>
    public static class MagicBitboards
    {
        private static bool _initialized = false;
        
        // Precomputed attack tables for non-sliding pieces
        private static readonly ulong[] KnightAttacks = new ulong[64];
        private static readonly ulong[] KingAttacks = new ulong[64];
        
        /// <summary>
        /// Initialize lookup tables - must be called before using any attack generation
        /// </summary>
        public static void Initialize()
        {
            if (_initialized) return;
            
            InitializeKnightAttacks();
            InitializeKingAttacks();
            
            _initialized = true;
        }
        
        /// <summary>
        /// Get rook attacks using simple ray-based generation
        /// MUCH slower than magic bitboards but guaranteed correct
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong GetRookAttacks(int square, ulong occupancy)
        {
            ulong attacks = 0UL;
            int file = square & 7;
            int rank = square >> 3;
            
            // North (up the file)
            for (int r = rank + 1; r <= 7; r++)
            {
                int targetSquare = (r << 3) | file;
                attacks |= 1UL << targetSquare;
                if ((occupancy & (1UL << targetSquare)) != 0)
                    break; // Blocked by piece
            }
            
            // South (down the file)
            for (int r = rank - 1; r >= 0; r--)
            {
                int targetSquare = (r << 3) | file;
                attacks |= 1UL << targetSquare;
                if ((occupancy & (1UL << targetSquare)) != 0)
                    break; // Blocked by piece
            }
            
            // East (right along rank)
            for (int f = file + 1; f <= 7; f++)
            {
                int targetSquare = (rank << 3) | f;
                attacks |= 1UL << targetSquare;
                if ((occupancy & (1UL << targetSquare)) != 0)
                    break; // Blocked by piece
            }
            
            // West (left along rank)
            for (int f = file - 1; f >= 0; f--)
            {
                int targetSquare = (rank << 3) | f;
                attacks |= 1UL << targetSquare;
                if ((occupancy & (1UL << targetSquare)) != 0)
                    break; // Blocked by piece
            }
            
            return attacks;
        }
        
        /// <summary>
        /// Get bishop attacks using simple ray-based generation
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong GetBishopAttacks(int square, ulong occupancy)
        {
            ulong attacks = 0UL;
            int file = square & 7;
            int rank = square >> 3;
            
            // Northeast diagonal
            for (int f = file + 1, r = rank + 1; f <= 7 && r <= 7; f++, r++)
            {
                int targetSquare = (r << 3) | f;
                attacks |= 1UL << targetSquare;
                if ((occupancy & (1UL << targetSquare)) != 0)
                    break; // Blocked by piece
            }
            
            // Northwest diagonal
            for (int f = file - 1, r = rank + 1; f >= 0 && r <= 7; f--, r++)
            {
                int targetSquare = (r << 3) | f;
                attacks |= 1UL << targetSquare;
                if ((occupancy & (1UL << targetSquare)) != 0)
                    break; // Blocked by piece
            }
            
            // Southeast diagonal
            for (int f = file + 1, r = rank - 1; f <= 7 && r >= 0; f++, r--)
            {
                int targetSquare = (r << 3) | f;
                attacks |= 1UL << targetSquare;
                if ((occupancy & (1UL << targetSquare)) != 0)
                    break; // Blocked by piece
            }
            
            // Southwest diagonal
            for (int f = file - 1, r = rank - 1; f >= 0 && r >= 0; f--, r--)
            {
                int targetSquare = (r << 3) | f;
                attacks |= 1UL << targetSquare;
                if ((occupancy & (1UL << targetSquare)) != 0)
                    break; // Blocked by piece
            }
            
            return attacks;
        }
        
        /// <summary>
        /// Get queen attacks (combination of rook and bishop)
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong GetQueenAttacks(int square, ulong occupancy)
        {
            return GetRookAttacks(square, occupancy) | GetBishopAttacks(square, occupancy);
        }
        
        /// <summary>
        /// Get precomputed knight attacks
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong GetKnightAttacks(int square)
        {
            return KnightAttacks[square];
        }
        
        /// <summary>
        /// Get precomputed king attacks
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong GetKingAttacks(int square)
        {
            return KingAttacks[square];
        }
        
        /// <summary>
        /// Initialize knight attack lookup table
        /// </summary>
        private static void InitializeKnightAttacks()
        {
            int[] knightMoves = { -17, -15, -10, -6, 6, 10, 15, 17 };
            
            for (int square = 0; square < 64; square++)
            {
                ulong attacks = 0UL;
                int file = square & 7;
                int rank = square >> 3;
                
                foreach (int move in knightMoves)
                {
                    int targetSquare = square + move;
                    
                    // Bounds check
                    if (targetSquare < 0 || targetSquare > 63)
                        continue;
                        
                    int targetFile = targetSquare & 7;
                    int targetRank = targetSquare >> 3;
                    
                    // Knight move validation - ensure it's actually a valid L-shape
                    int fileDiff = Math.Abs(file - targetFile);
                    int rankDiff = Math.Abs(rank - targetRank);
                    
                    if ((fileDiff == 2 && rankDiff == 1) || (fileDiff == 1 && rankDiff == 2))
                    {
                        attacks |= 1UL << targetSquare;
                    }
                }
                
                KnightAttacks[square] = attacks;
            }
        }
        
        /// <summary>
        /// Initialize king attack lookup table
        /// </summary>
        private static void InitializeKingAttacks()
        {
            for (int square = 0; square < 64; square++)
            {
                ulong attacks = 0UL;
                int file = square & 7;
                int rank = square >> 3;
                
                // All 8 directions around the king
                for (int fileOffset = -1; fileOffset <= 1; fileOffset++)
                {
                    for (int rankOffset = -1; rankOffset <= 1; rankOffset++)
                    {
                        if (fileOffset == 0 && rankOffset == 0)
                            continue; // Skip the king's own square
                            
                        int targetFile = file + fileOffset;
                        int targetRank = rank + rankOffset;
                        
                        // Bounds check
                        if (targetFile >= 0 && targetFile <= 7 && 
                            targetRank >= 0 && targetRank <= 7)
                        {
                            int targetSquare = (targetRank << 3) | targetFile;
                            attacks |= 1UL << targetSquare;
                        }
                    }
                }
                
                KingAttacks[square] = attacks;
            }
        }
        
        /// <summary>
        /// Get attacks for any piece type
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong GetAttacks(PieceType pieceType, int square, ulong occupancy)
        {
            return pieceType switch
            {
                PieceType.Rook => GetRookAttacks(square, occupancy),
                PieceType.Bishop => GetBishopAttacks(square, occupancy),
                PieceType.Queen => GetQueenAttacks(square, occupancy),
                PieceType.Knight => GetKnightAttacks(square),
                PieceType.King => GetKingAttacks(square),
                _ => 0UL
            };
        }
        
        /// <summary>
        /// Check if a square is attacked by the given piece type and color
        /// </summary>
        public static bool IsSquareAttackedBy(int square, PieceType pieceType, bool isWhite, ulong occupancy, ulong pieceBitboard)
        {
            ulong attacks = GetAttacks(pieceType, square, occupancy);
            return (attacks & pieceBitboard) != 0;
        }
    }
}
