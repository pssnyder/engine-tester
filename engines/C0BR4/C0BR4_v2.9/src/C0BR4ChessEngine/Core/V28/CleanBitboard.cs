using System;
using System.Runtime.CompilerServices;

namespace C0BR4ChessEngine.Core.V28
{
    /// <summary>
    /// Clean, simplified bitboard implementation for C0BR4 v2.8
    /// Prioritizes correctness and clarity over performance
    /// Built from scratch to eliminate all legacy magic bitboard issues
    /// </summary>
    public static class CleanBitboard
    {
        // Basic bitboard masks
        public static readonly ulong[] FileMasks = new ulong[8];
        public static readonly ulong[] RankMasks = new ulong[8];
        public static readonly ulong NotAFile = 0xfefefefefefefefe;
        public static readonly ulong NotHFile = 0x7f7f7f7f7f7f7f7f;
        
        // Precomputed attack tables - simple and reliable
        public static readonly ulong[] KnightAttacks = new ulong[64];
        public static readonly ulong[] KingAttacks = new ulong[64];
        public static readonly ulong[] PawnAttacksWhite = new ulong[64];
        public static readonly ulong[] PawnAttacksBlack = new ulong[64];
        
        // Simple sliding piece attacks - no magic bitboards initially
        private static bool _initialized = false;
        
        /// <summary>
        /// Initialize all bitboard lookup tables
        /// MUCH simpler than magic bitboards - focuses on correctness
        /// </summary>
        public static void Initialize()
        {
            if (_initialized) return;
            
            InitializeFilesAndRanks();
            InitializeKnightAttacks();
            InitializeKingAttacks();
            InitializePawnAttacks();
            
            _initialized = true;
        }
        
        /// <summary>
        /// Convert square index (0-63) to bitboard
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong SquareToBitboard(int square)
        {
            return 1UL << square;
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
        /// Get square index from file and rank
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static int GetSquare(int file, int rank)
        {
            return rank * 8 + file;
        }
        
        /// <summary>
        /// Pop least significant bit and return its index
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static int PopLSB(ref ulong bitboard)
        {
            int index = System.Numerics.BitOperations.TrailingZeroCount(bitboard);
            bitboard &= bitboard - 1; // Clear the LSB
            return index;
        }
        
        /// <summary>
        /// Count set bits in bitboard
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static int PopCount(ulong bitboard)
        {
            return System.Numerics.BitOperations.PopCount(bitboard);
        }
        
        /// <summary>
        /// Generate rook attacks using simple ray-based approach
        /// Much slower than magic bitboards but guaranteed correct
        /// </summary>
        public static ulong GetRookAttacks(int square, ulong occupancy)
        {
            ulong attacks = 0UL;
            int file = GetFile(square);
            int rank = GetRank(square);
            
            // North (up the file)
            for (int r = rank + 1; r <= 7; r++)
            {
                int targetSquare = GetSquare(file, r);
                attacks |= SquareToBitboard(targetSquare);
                if ((occupancy & SquareToBitboard(targetSquare)) != 0)
                    break; // Blocked by piece
            }
            
            // South (down the file)
            for (int r = rank - 1; r >= 0; r--)
            {
                int targetSquare = GetSquare(file, r);
                attacks |= SquareToBitboard(targetSquare);
                if ((occupancy & SquareToBitboard(targetSquare)) != 0)
                    break; // Blocked by piece
            }
            
            // East (right along rank)
            for (int f = file + 1; f <= 7; f++)
            {
                int targetSquare = GetSquare(f, rank);
                attacks |= SquareToBitboard(targetSquare);
                if ((occupancy & SquareToBitboard(targetSquare)) != 0)
                    break; // Blocked by piece
            }
            
            // West (left along rank)
            for (int f = file - 1; f >= 0; f--)
            {
                int targetSquare = GetSquare(f, rank);
                attacks |= SquareToBitboard(targetSquare);
                if ((occupancy & SquareToBitboard(targetSquare)) != 0)
                    break; // Blocked by piece
            }
            
            return attacks;
        }
        
        /// <summary>
        /// Generate bishop attacks using simple ray-based approach
        /// </summary>
        public static ulong GetBishopAttacks(int square, ulong occupancy)
        {
            ulong attacks = 0UL;
            int file = GetFile(square);
            int rank = GetRank(square);
            
            // Northeast diagonal
            for (int f = file + 1, r = rank + 1; f <= 7 && r <= 7; f++, r++)
            {
                int targetSquare = GetSquare(f, r);
                attacks |= SquareToBitboard(targetSquare);
                if ((occupancy & SquareToBitboard(targetSquare)) != 0)
                    break; // Blocked by piece
            }
            
            // Northwest diagonal
            for (int f = file - 1, r = rank + 1; f >= 0 && r <= 7; f--, r++)
            {
                int targetSquare = GetSquare(f, r);
                attacks |= SquareToBitboard(targetSquare);
                if ((occupancy & SquareToBitboard(targetSquare)) != 0)
                    break; // Blocked by piece
            }
            
            // Southeast diagonal
            for (int f = file + 1, r = rank - 1; f <= 7 && r >= 0; f++, r--)
            {
                int targetSquare = GetSquare(f, r);
                attacks |= SquareToBitboard(targetSquare);
                if ((occupancy & SquareToBitboard(targetSquare)) != 0)
                    break; // Blocked by piece
            }
            
            // Southwest diagonal
            for (int f = file - 1, r = rank - 1; f >= 0 && r >= 0; f--, r--)
            {
                int targetSquare = GetSquare(f, r);
                attacks |= SquareToBitboard(targetSquare);
                if ((occupancy & SquareToBitboard(targetSquare)) != 0)
                    break; // Blocked by piece
            }
            
            return attacks;
        }
        
        /// <summary>
        /// Generate queen attacks (combination of rook and bishop)
        /// </summary>
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
        /// Get precomputed pawn attacks
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong GetPawnAttacks(int square, bool isWhite)
        {
            return isWhite ? PawnAttacksWhite[square] : PawnAttacksBlack[square];
        }
        
        private static void InitializeFilesAndRanks()
        {
            for (int i = 0; i < 8; i++)
            {
                // File masks (vertical columns)
                FileMasks[i] = 0UL;
                for (int rank = 0; rank < 8; rank++)
                {
                    FileMasks[i] |= SquareToBitboard(GetSquare(i, rank));
                }
                
                // Rank masks (horizontal rows)
                RankMasks[i] = 0UL;
                for (int file = 0; file < 8; file++)
                {
                    RankMasks[i] |= SquareToBitboard(GetSquare(file, i));
                }
            }
        }
        
        private static void InitializeKnightAttacks()
        {
            int[] knightMoves = { -17, -15, -10, -6, 6, 10, 15, 17 };
            
            for (int square = 0; square < 64; square++)
            {
                ulong attacks = 0UL;
                int file = GetFile(square);
                int rank = GetRank(square);
                
                foreach (int move in knightMoves)
                {
                    int targetSquare = square + move;
                    
                    // Bounds check
                    if (targetSquare < 0 || targetSquare > 63)
                        continue;
                        
                    int targetFile = GetFile(targetSquare);
                    int targetRank = GetRank(targetSquare);
                    
                    // Knight move validation - ensure it's actually a valid L-shape
                    int fileDiff = Math.Abs(file - targetFile);
                    int rankDiff = Math.Abs(rank - targetRank);
                    
                    if ((fileDiff == 2 && rankDiff == 1) || (fileDiff == 1 && rankDiff == 2))
                    {
                        attacks |= SquareToBitboard(targetSquare);
                    }
                }
                
                KnightAttacks[square] = attacks;
            }
        }
        
        private static void InitializeKingAttacks()
        {
            for (int square = 0; square < 64; square++)
            {
                ulong attacks = 0UL;
                int file = GetFile(square);
                int rank = GetRank(square);
                
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
                            int targetSquare = GetSquare(targetFile, targetRank);
                            attacks |= SquareToBitboard(targetSquare);
                        }
                    }
                }
                
                KingAttacks[square] = attacks;
            }
        }
        
        private static void InitializePawnAttacks()
        {
            for (int square = 0; square < 64; square++)
            {
                int file = GetFile(square);
                int rank = GetRank(square);
                
                // White pawn attacks (moving up the board, rank increases)
                PawnAttacksWhite[square] = 0UL;
                if (rank < 7) // Not on 8th rank
                {
                    // Diagonal left
                    if (file > 0)
                    {
                        int targetSquare = GetSquare(file - 1, rank + 1);
                        PawnAttacksWhite[square] |= SquareToBitboard(targetSquare);
                    }
                    // Diagonal right
                    if (file < 7)
                    {
                        int targetSquare = GetSquare(file + 1, rank + 1);
                        PawnAttacksWhite[square] |= SquareToBitboard(targetSquare);
                    }
                }
                
                // Black pawn attacks (moving down the board, rank decreases)
                PawnAttacksBlack[square] = 0UL;
                if (rank > 0) // Not on 1st rank
                {
                    // Diagonal left (from black's perspective)
                    if (file > 0)
                    {
                        int targetSquare = GetSquare(file - 1, rank - 1);
                        PawnAttacksBlack[square] |= SquareToBitboard(targetSquare);
                    }
                    // Diagonal right (from black's perspective)
                    if (file < 7)
                    {
                        int targetSquare = GetSquare(file + 1, rank - 1);
                        PawnAttacksBlack[square] |= SquareToBitboard(targetSquare);
                    }
                }
            }
        }
    }
}
