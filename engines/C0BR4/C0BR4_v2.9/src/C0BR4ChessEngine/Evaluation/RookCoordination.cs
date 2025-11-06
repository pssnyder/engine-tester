using C0BR4ChessEngine.Core;

namespace C0BR4ChessEngine.Evaluation
{
    /// <summary>
    /// Evaluates rook coordination and positioning
    /// Middlegame: Rank and file alignment, open files
    /// Endgame: Aggressive positioning, second rank control
    /// </summary>
    public static class RookCoordination
    {
        // Bonus values in centipawns
        private const int SameFileBonus = 15;       // Rooks on same file
        private const int SameRankBonus = 10;       // Rooks on same rank
        private const int OpenFileBonus = 20;       // Rook on open file
        private const int SemiOpenFileBonus = 10;   // Rook on semi-open file
        private const int SeventhRankBonus = 25;    // Rook on 7th rank in endgame
        private const int DoubledRooksBonus = 5;    // Additional bonus for doubled rooks

        /// <summary>
        /// Evaluate rook coordination for both sides
        /// </summary>
        /// <param name="board">Current board position</param>
        /// <param name="gamePhase">Game phase (0.0 = endgame, 1.0 = opening)</param>
        /// <returns>Evaluation from white's perspective</returns>
        public static int Evaluate(Board board, double gamePhase)
        {
            int whiteEval = EvaluateRooksForSide(board, true, gamePhase);
            int blackEval = EvaluateRooksForSide(board, false, gamePhase);
            
            return whiteEval - blackEval;
        }

        /// <summary>
        /// Evaluate rook coordination for one side
        /// </summary>
        private static int EvaluateRooksForSide(Board board, bool isWhite, double gamePhase)
        {
            var rooks = FindRooks(board, isWhite);
            if (rooks.Count == 0)
                return 0;

            int evaluation = 0;
            bool hasLostCastlingRights = HasLostCastlingRights(board, isWhite);

            // Evaluate each rook individually
            foreach (var rook in rooks)
            {
                evaluation += EvaluateRookPosition(board, rook, gamePhase, hasLostCastlingRights);
            }

            // Evaluate rook coordination (multiple rooks)
            if (rooks.Count >= 2)
            {
                evaluation += EvaluateRookPairs(rooks, gamePhase);
            }

            return evaluation;
        }

        /// <summary>
        /// Find all rooks for a given side
        /// </summary>
        private static List<Piece> FindRooks(Board board, bool isWhite)
        {
            var rooks = new List<Piece>();
            
            for (int square = 0; square < 64; square++)
            {
                var piece = board.GetPiece(new Square(square));
                if (!piece.IsNull && piece.IsWhite == isWhite && piece.PieceType == PieceType.Rook)
                {
                    rooks.Add(piece);
                }
            }
            
            return rooks;
        }

        /// <summary>
        /// Evaluate individual rook position
        /// </summary>
        private static int EvaluateRookPosition(Board board, Piece rook, double gamePhase, bool hasLostCastlingRights)
        {
            int evaluation = 0;
            int file = rook.Square.Index % 8;
            int rank = rook.Square.Index / 8;

            // Open and semi-open file bonuses (stronger in middlegame)
            var fileStatus = GetFileStatus(board, file, rook.IsWhite);
            switch (fileStatus)
            {
                case FileStatus.Open:
                    evaluation += (int)(OpenFileBonus * (0.7 + gamePhase * 0.3)); // 70-100% of bonus
                    break;
                case FileStatus.SemiOpen:
                    evaluation += (int)(SemiOpenFileBonus * (0.7 + gamePhase * 0.3));
                    break;
            }

            // Seventh rank bonus (stronger in endgame)
            if (IsSeventhRank(rank, rook.IsWhite))
            {
                evaluation += (int)(SeventhRankBonus * (1.3 - gamePhase * 0.3)); // 100-130% of bonus
            }

            // Encourage rook activity after castling rights are lost
            if (hasLostCastlingRights)
            {
                // Bonus for active rook positioning
                if (IsActivePosition(rook, gamePhase))
                {
                    evaluation += (int)(10 * (1.0 - gamePhase)); // Up to 10cp in endgame
                }
            }

            return evaluation;
        }

        /// <summary>
        /// Evaluate coordination between pairs of rooks
        /// </summary>
        private static int EvaluateRookPairs(List<Piece> rooks, double gamePhase)
        {
            int evaluation = 0;

            for (int i = 0; i < rooks.Count; i++)
            {
                for (int j = i + 1; j < rooks.Count; j++)
                {
                    var rook1 = rooks[i];
                    var rook2 = rooks[j];

                    // Same file coordination
                    if (GetFile(rook1) == GetFile(rook2))
                    {
                        evaluation += (int)(SameFileBonus * (0.8 + gamePhase * 0.2)); // More valuable in middlegame
                        evaluation += DoubledRooksBonus; // Additional bonus for doubled rooks
                    }

                    // Same rank coordination (more valuable in endgame)
                    if (GetRank(rook1) == GetRank(rook2))
                    {
                        evaluation += (int)(SameRankBonus * (1.2 - gamePhase * 0.2)); // More valuable in endgame
                    }
                }
            }

            return evaluation;
        }

        /// <summary>
        /// Check if rook is on the seventh rank (relative to its color)
        /// </summary>
        private static bool IsSeventhRank(int rank, bool isWhite)
        {
            return isWhite ? rank == 6 : rank == 1; // 7th rank for white, 2nd rank for black
        }

        /// <summary>
        /// Check if rook is in an active position
        /// </summary>
        private static bool IsActivePosition(Piece rook, double gamePhase)
        {
            int file = GetFile(rook);
            int rank = GetRank(rook);

            // In middlegame, central files are more active
            if (gamePhase > 0.5)
            {
                return file >= 2 && file <= 5; // c, d, e, f files
            }
            // In endgame, advanced ranks are more active
            else
            {
                return IsSeventhRank(rank, rook.IsWhite) || 
                       (rook.IsWhite ? rank >= 4 : rank <= 3); // Advanced positions
            }
        }

        /// <summary>
        /// Determine the status of a file (open, semi-open, closed)
        /// </summary>
        private static FileStatus GetFileStatus(Board board, int file, bool forWhite)
        {
            bool hasOwnPawn = false;
            bool hasEnemyPawn = false;

            for (int rank = 0; rank < 8; rank++)
            {
                var piece = board.GetPiece(new Square(rank * 8 + file));
                if (!piece.IsNull && piece.PieceType == PieceType.Pawn)
                {
                    if (piece.IsWhite == forWhite)
                        hasOwnPawn = true;
                    else
                        hasEnemyPawn = true;
                }
            }

            if (!hasOwnPawn && !hasEnemyPawn)
                return FileStatus.Open;
            else if (!hasOwnPawn)
                return FileStatus.SemiOpen;
            else
                return FileStatus.Closed;
        }

        /// <summary>
        /// Check if side has lost castling rights
        /// </summary>
        private static bool HasLostCastlingRights(Board board, bool isWhite)
        {
            // This is a simplified check - in a full implementation, we'd check the actual castling rights
            // For now, we'll assume castling rights are lost if the king is not on its starting square
            // or if we're in the endgame
            var king = FindKing(board, isWhite);
            if (king.IsNull)
                return true;

            int expectedKingSquare = isWhite ? 4 : 60; // e1 for white, e8 for black
            return king.Square.Index != expectedKingSquare;
        }

        /// <summary>
        /// Find the king for a given side
        /// </summary>
        private static Piece FindKing(Board board, bool isWhite)
        {
            for (int square = 0; square < 64; square++)
            {
                var piece = board.GetPiece(new Square(square));
                if (!piece.IsNull && piece.IsWhite == isWhite && piece.PieceType == PieceType.King)
                {
                    return piece;
                }
            }
            return new Piece(); // Null piece
        }

        private static int GetFile(Piece piece) => piece.Square.Index % 8;
        private static int GetRank(Piece piece) => piece.Square.Index / 8;

        private enum FileStatus
        {
            Closed,    // Has own pawns
            SemiOpen,  // No own pawns, has enemy pawns
            Open       // No pawns at all
        }
    }
}
