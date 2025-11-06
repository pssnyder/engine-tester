using System;
using System.Collections.Generic;

namespace C0BR4ChessEngine.Core
{
    /// <summary>
    /// Enhanced move generator that bridges the old Board interface with new bitboard system
    /// Provides backward compatibility while using efficient bitboard operations
    /// This replaces the old inefficient piece-by-piece move generation
    /// </summary>
    public class MoveGenerator
    {
        private readonly Board board;
        private readonly BitboardMoveGenerator bitboardGenerator;

        public MoveGenerator(Board board)
        {
            this.board = board;
            this.bitboardGenerator = new BitboardMoveGenerator();
        }

        /// <summary>
        /// Generate all legal moves using the efficient bitboard system
        /// </summary>
        public Move[] GenerateLegalMoves()
        {
            var position = board.GetBitboardPosition();
            return bitboardGenerator.GenerateLegalMoves(position);
        }

        /// <summary>
        /// Generate all pseudo-legal moves using the efficient bitboard system
        /// </summary>
        public Move[] GeneratePseudoLegalMoves()
        {
            var position = board.GetBitboardPosition();
            return bitboardGenerator.GeneratePseudoLegalMoves(position);
        }

        /// <summary>
        /// Check if the current player is in check
        /// </summary>
        public bool IsCurrentPlayerInCheck()
        {
            var position = board.GetBitboardPosition();
            return position.IsInCheck();
        }

        /// <summary>
        /// Check if a move is legal
        /// </summary>
        public bool IsLegalMove(Move move)
        {
            return bitboardGenerator.IsLegalMove(move);
        }
    }
}
