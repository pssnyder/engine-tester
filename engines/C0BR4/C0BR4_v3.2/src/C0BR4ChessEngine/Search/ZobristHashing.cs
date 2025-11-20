using System;
using C0BR4ChessEngine.Core;

namespace C0BR4ChessEngine.Search
{
    /// <summary>
    /// Zobrist hashing implementation for fast position comparison
    /// Each piece on each square gets a unique random number
    /// Position hash = XOR of all piece numbers + side to move + castling rights + en passant
    /// </summary>
    public static class ZobristHashing
    {
        // Hash tables for different aspects of the position
        private static readonly ulong[,] PieceSquareHashes = new ulong[12, 64]; // 12 piece types * 64 squares
        private static readonly ulong SideToMoveHash;
        private static readonly ulong[] CastlingRightsHashes = new ulong[16]; // 2^4 possible castling combinations
        private static readonly ulong[] EnPassantFileHashes = new ulong[8]; // 8 files for en passant

        // Piece type indices for the hash table
        private const int WhitePawn = 0, WhiteKnight = 1, WhiteBishop = 2, WhiteRook = 3, WhiteQueen = 4, WhiteKing = 5;
        private const int BlackPawn = 6, BlackKnight = 7, BlackBishop = 8, BlackRook = 9, BlackQueen = 10, BlackKing = 11;

        static ZobristHashing()
        {
            var random = new Random(12345); // Fixed seed for reproducible hashes
            
            // Initialize piece-square hash values
            for (int piece = 0; piece < 12; piece++)
            {
                for (int square = 0; square < 64; square++)
                {
                    PieceSquareHashes[piece, square] = GenerateRandomULong(random);
                }
            }

            // Initialize side to move hash
            SideToMoveHash = GenerateRandomULong(random);

            // Initialize castling rights hashes
            for (int i = 0; i < 16; i++)
            {
                CastlingRightsHashes[i] = GenerateRandomULong(random);
            }

            // Initialize en passant file hashes
            for (int file = 0; file < 8; file++)
            {
                EnPassantFileHashes[file] = GenerateRandomULong(random);
            }
        }

        /// <summary>
        /// Generate a random 64-bit number for Zobrist hashing
        /// </summary>
        private static ulong GenerateRandomULong(Random random)
        {
            byte[] bytes = new byte[8];
            random.NextBytes(bytes);
            return BitConverter.ToUInt64(bytes, 0);
        }

        /// <summary>
        /// Calculate the Zobrist hash for the current board position
        /// </summary>
        public static ulong CalculateHash(Board board)
        {
            ulong hash = 0;

            // Hash all pieces on the board
            for (int square = 0; square < 64; square++)
            {
                var piece = board.GetPiece(new Square(square));
                if (piece.PieceType != PieceType.None)
                {
                    int pieceIndex = GetPieceIndex(piece);
                    hash ^= PieceSquareHashes[pieceIndex, square];
                }
            }

            // Hash side to move
            if (!board.IsWhiteToMove)
            {
                hash ^= SideToMoveHash;
            }

            // TODO: Add castling rights and en passant when Board exposes them
            // For now, we'll skip these since they're not easily accessible
            // This makes the hash less perfect but still very effective

            return hash;
        }

        /// <summary>
        /// Update hash incrementally when a move is made
        /// This is much faster than recalculating the entire hash
        /// </summary>
        public static ulong UpdateHash(ulong currentHash, Move move, Board board)
        {
            ulong newHash = currentHash;

            // Remove the moving piece from its start square
            var movingPiece = board.GetPiece(move.StartSquare);
            int movingPieceIndex = GetPieceIndex(movingPiece);
            newHash ^= PieceSquareHashes[movingPieceIndex, move.StartSquare.Index];

            // Remove captured piece if any
            var capturedPiece = board.GetPiece(move.TargetSquare);
            if (capturedPiece.PieceType != PieceType.None)
            {
                int capturedPieceIndex = GetPieceIndex(capturedPiece);
                newHash ^= PieceSquareHashes[capturedPieceIndex, move.TargetSquare.Index];
            }

            // Add the piece to its target square (handle promotion)
            if (move.PromotionPieceType != PieceType.None)
            {
                var promotedPiece = new Piece(move.PromotionPieceType, movingPiece.IsWhite, move.TargetSquare);
                int promotedPieceIndex = GetPieceIndex(promotedPiece);
                newHash ^= PieceSquareHashes[promotedPieceIndex, move.TargetSquare.Index];
            }
            else
            {
                newHash ^= PieceSquareHashes[movingPieceIndex, move.TargetSquare.Index];
            }

            // Flip side to move
            newHash ^= SideToMoveHash;

            return newHash;
        }

        /// <summary>
        /// Get the piece index for the Zobrist hash table
        /// </summary>
        private static int GetPieceIndex(Piece piece)
        {
            int baseIndex = piece.IsWhite ? 0 : 6;
            return baseIndex + (int)piece.PieceType - 1; // -1 because PieceType.None = 0
        }
    }
}
