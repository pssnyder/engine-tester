using C0BR4ChessEngine.Core;

namespace C0BR4ChessEngine.Evaluation
{
    /// <summary>
    /// Evaluates castling rights preservation and encourages castling moves
    /// Focuses on maintaining king safety and proper development timing
    /// </summary>
    public static class CastlingRights
    {
        // Evaluation values in centipawns
        private const int PreservationBonus = 15;          // Bonus for maintaining castling rights
        private const int CastlingMoveBonus = 30;          // Strong bonus for actual castling moves
        private const int KingOnBackRankBonus = 10;        // Bonus for keeping king on back rank until endgame
        private const int RookDevelopmentPenalty = 8;      // Penalty for premature rook development
        private const int KingExposurePenalty = 25;        // Penalty for king moving without castling

        // Game phase thresholds for evaluation weighting
        private const double OpeningPhaseMax = 0.9;        // Above this is pure opening
        private const double MiddlegamePhaseMin = 0.3;     // Below this is endgame

        /// <summary>
        /// Evaluate castling rights for both sides
        /// </summary>
        /// <param name="board">Current board position</param>
        /// <param name="gamePhase">Game phase (0.0 = endgame, 1.0 = opening)</param>
        /// <returns>Evaluation from white's perspective</returns>
        public static int Evaluate(Board board, double gamePhase)
        {
            // Castling rights are most important in opening/middlegame
            double rightsWeight = Math.Max(0.1, gamePhase); // 10-100% weight
            
            int whiteEval = EvaluateCastlingRightsForSide(board, true, gamePhase);
            int blackEval = EvaluateCastlingRightsForSide(board, false, gamePhase);
            
            return (int)((whiteEval - blackEval) * rightsWeight);
        }

        /// <summary>
        /// Evaluate castling rights situation for one side
        /// </summary>
        private static int EvaluateCastlingRightsForSide(Board board, bool isWhite, double gamePhase)
        {
            int evaluation = 0;
            var king = FindKing(board, isWhite);
            
            if (king.IsNull)
                return 0;

            var rightsStatus = AnalyzeCastlingRights(board, king);

            // Evaluate based on current castling status
            switch (rightsStatus.Status)
            {
                case CastlingStatus.BothAvailable:
                    evaluation += EvaluateBothRightsAvailable(board, king, gamePhase);
                    break;
                
                case CastlingStatus.KingsideOnly:
                    evaluation += EvaluatePartialRights(board, king, true, gamePhase);
                    break;
                
                case CastlingStatus.QueensideOnly:
                    evaluation += EvaluatePartialRights(board, king, false, gamePhase);
                    break;
                
                case CastlingStatus.AlreadyCastled:
                    evaluation += EvaluateAlreadyCastled(board, king, gamePhase);
                    break;
                
                case CastlingStatus.RightsLost:
                    evaluation += EvaluateRightsLost(board, king, gamePhase);
                    break;
            }

            // Evaluate king positioning relative to castling strategy
            evaluation += EvaluateKingPositioning(king, rightsStatus, gamePhase);

            // Evaluate rook development timing
            evaluation += EvaluateRookDevelopment(board, isWhite, rightsStatus, gamePhase);

            return evaluation;
        }

        /// <summary>
        /// Evaluate when both castling rights are available
        /// </summary>
        private static int EvaluateBothRightsAvailable(Board board, Piece king, double gamePhase)
        {
            int evaluation = 0;
            
            // Strong bonus for preserving both rights
            evaluation += (int)(PreservationBonus * 2 * gamePhase); // More valuable in opening
            
            // Evaluate potential for castling moves
            bool canCastleKingside = CanActuallyCastle(board, king, true);
            bool canCastleQueenside = CanActuallyCastle(board, king, false);
            
            if (canCastleKingside)
            {
                evaluation += (int)(CastlingMoveBonus * 0.6 * gamePhase); // Potential kingside castling
            }
            
            if (canCastleQueenside)
            {
                evaluation += (int)(CastlingMoveBonus * 0.4 * gamePhase); // Potential queenside castling
            }
            
            // Extra bonus if both sides are actually available
            if (canCastleKingside && canCastleQueenside)
            {
                evaluation += (int)(10 * gamePhase); // Flexibility bonus
            }

            return evaluation;
        }

        /// <summary>
        /// Evaluate when only one castling right remains
        /// </summary>
        private static int EvaluatePartialRights(Board board, Piece king, bool kingsideAvailable, double gamePhase)
        {
            int evaluation = 0;
            
            // Moderate bonus for preserving one right
            evaluation += (int)(PreservationBonus * gamePhase);
            
            // Check if the remaining option is actually usable
            if (CanActuallyCastle(board, king, kingsideAvailable))
            {
                // Strong bonus for having a viable castling option
                evaluation += (int)(CastlingMoveBonus * 0.8 * gamePhase);
                
                // Slight preference for kingside castling
                if (kingsideAvailable)
                {
                    evaluation += (int)(5 * gamePhase);
                }
            }
            else
            {
                // Small penalty if the remaining right is blocked/unusable
                evaluation -= (int)(5 * gamePhase);
            }

            return evaluation;
        }

        /// <summary>
        /// Evaluate when king has already castled
        /// </summary>
        private static int EvaluateAlreadyCastled(Board board, Piece king, double gamePhase)
        {
            int evaluation = 0;
            
            // Bonus for having completed castling
            evaluation += CastlingMoveBonus;
            
            // Additional bonus based on timing
            if (gamePhase > OpeningPhaseMax)
            {
                evaluation += 10; // Early castling bonus
            }
            
            // Bonus for appropriate castling choice
            if (IsCastledKingside(king))
            {
                evaluation += 5; // Slight preference for kingside
            }

            return evaluation;
        }

        /// <summary>
        /// Evaluate when castling rights have been lost
        /// </summary>
        private static int EvaluateRightsLost(Board board, Piece king, double gamePhase)
        {
            int evaluation = 0;
            
            // Penalty for losing castling rights, worse in opening/middlegame
            evaluation -= (int)(KingExposurePenalty * gamePhase);
            
            // Additional penalty based on king safety
            if (IsKingExposed(board, king))
            {
                evaluation -= (int)(15 * gamePhase); // Extra exposure penalty
            }
            
            // Slightly less penalty if we're approaching endgame
            if (gamePhase < MiddlegamePhaseMin)
            {
                evaluation += (int)(10 * (1.0 - gamePhase)); // Endgame mitigation
            }

            return evaluation;
        }

        /// <summary>
        /// Evaluate king positioning relative to castling strategy
        /// </summary>
        private static int EvaluateKingPositioning(Piece king, CastlingRightsStatus rightsStatus, double gamePhase)
        {
            int evaluation = 0;
            int kingRank = GetRank(king);
            int expectedRank = king.IsWhite ? 0 : 7; // Back rank
            
            // Bonus for keeping king on back rank until endgame (unless already castled)
            if (rightsStatus.Status != CastlingStatus.AlreadyCastled)
            {
                if (kingRank == expectedRank)
                {
                    evaluation += (int)(KingOnBackRankBonus * gamePhase);
                }
                else
                {
                    // Penalty for moving king off back rank without castling
                    evaluation -= (int)(KingExposurePenalty * gamePhase);
                }
            }
            
            // In endgame, king activity becomes more important than safety
            if (gamePhase < MiddlegamePhaseMin && rightsStatus.Status == CastlingStatus.RightsLost)
            {
                // Encourage king activity in endgame
                int centralDistance = Math.Abs(3 - GetFile(king)) + Math.Abs(3 - kingRank);
                evaluation += (int)(5 * (1.0 - gamePhase) * (7 - centralDistance)); // Centralization bonus
            }

            return evaluation;
        }

        /// <summary>
        /// Evaluate rook development timing relative to castling
        /// </summary>
        private static int EvaluateRookDevelopment(Board board, bool isWhite, CastlingRightsStatus rightsStatus, double gamePhase)
        {
            int evaluation = 0;
            
            // Only evaluate if castling rights might still be relevant
            if (rightsStatus.Status == CastlingStatus.RightsLost || gamePhase < 0.5)
                return 0;
            
            // Check for premature rook development that might hinder castling
            var rooks = FindRooks(board, isWhite);
            int backRank = isWhite ? 0 : 7;
            
            foreach (var rook in rooks)
            {
                int rookRank = GetRank(rook);
                int rookFile = GetFile(rook);
                
                // Penalty for moving corner rooks too early if castling rights exist
                if (rookRank != backRank)
                {
                    bool isCornerRook = rookFile == 0 || rookFile == 7; // a-file or h-file
                    
                    if (isCornerRook)
                    {
                        // Check if this rook movement lost castling rights
                        if ((rookFile == 0 && rightsStatus.QueensideAvailable) ||
                            (rookFile == 7 && rightsStatus.KingsideAvailable))
                        {
                            // This shouldn't happen if rights are available, but check anyway
                            evaluation -= (int)(RookDevelopmentPenalty * gamePhase);
                        }
                    }
                }
            }

            return evaluation;
        }

        /// <summary>
        /// Analyze current castling rights status
        /// </summary>
        private static CastlingRightsStatus AnalyzeCastlingRights(Board board, Piece king)
        {
            var status = new CastlingRightsStatus();
            int kingSquare = king.Square.Index;
            int startingSquare = king.IsWhite ? 4 : 60; // e1 for white, e8 for black
            
            // Check if king has moved
            if (kingSquare != startingSquare)
            {
                // King has moved - check if it castled
                if (IsCastledKingside(king) || IsCastledQueenside(king))
                {
                    status.Status = CastlingStatus.AlreadyCastled;
                }
                else
                {
                    status.Status = CastlingStatus.RightsLost;
                }
                return status;
            }
            
            // King is on starting square - check rook positions
            bool kingsideRookPresent = CheckRookOnStartingSquare(board, king.IsWhite, true);
            bool queensideRookPresent = CheckRookOnStartingSquare(board, king.IsWhite, false);
            
            status.KingsideAvailable = kingsideRookPresent;
            status.QueensideAvailable = queensideRookPresent;
            
            if (kingsideRookPresent && queensideRookPresent)
            {
                status.Status = CastlingStatus.BothAvailable;
            }
            else if (kingsideRookPresent)
            {
                status.Status = CastlingStatus.KingsideOnly;
            }
            else if (queensideRookPresent)
            {
                status.Status = CastlingStatus.QueensideOnly;
            }
            else
            {
                status.Status = CastlingStatus.RightsLost;
            }
            
            return status;
        }

        /// <summary>
        /// Check if castling is actually possible (not just rights available)
        /// </summary>
        private static bool CanActuallyCastle(Board board, Piece king, bool kingside)
        {
            int backRank = king.IsWhite ? 0 : 7;
            
            // Check if path is clear
            if (kingside)
            {
                // Check f and g squares are empty
                return IsSquareEmpty(board, backRank * 8 + 5) && IsSquareEmpty(board, backRank * 8 + 6);
            }
            else
            {
                // Check b, c, and d squares are empty
                return IsSquareEmpty(board, backRank * 8 + 1) && 
                       IsSquareEmpty(board, backRank * 8 + 2) && 
                       IsSquareEmpty(board, backRank * 8 + 3);
            }
        }

        /// <summary>
        /// Check if a rook is on its starting square
        /// </summary>
        private static bool CheckRookOnStartingSquare(Board board, bool isWhite, bool kingside)
        {
            int backRank = isWhite ? 0 : 7;
            int rookFile = kingside ? 7 : 0; // h-file or a-file
            int square = backRank * 8 + rookFile;
            
            var piece = board.GetPiece(new Square(square));
            return !piece.IsNull && piece.PieceType == PieceType.Rook && piece.IsWhite == isWhite;
        }

        /// <summary>
        /// Check if king has castled kingside
        /// </summary>
        private static bool IsCastledKingside(Piece king)
        {
            int expectedSquare = king.IsWhite ? 6 : 62; // g1 for white, g8 for black
            return king.Square.Index == expectedSquare;
        }

        /// <summary>
        /// Check if king has castled queenside
        /// </summary>
        private static bool IsCastledQueenside(Piece king)
        {
            int expectedSquare = king.IsWhite ? 2 : 58; // c1 for white, c8 for black
            return king.Square.Index == expectedSquare;
        }

        /// <summary>
        /// Check if king is in an exposed position
        /// </summary>
        private static bool IsKingExposed(Board board, Piece king)
        {
            // Simplified: king not on back rank and not castled
            int rank = GetRank(king);
            int expectedRank = king.IsWhite ? 0 : 7;
            
            return rank != expectedRank && !IsCastledKingside(king) && !IsCastledQueenside(king);
        }

        /// <summary>
        /// Check if a square is empty
        /// </summary>
        private static bool IsSquareEmpty(Board board, int squareIndex)
        {
            var piece = board.GetPiece(new Square(squareIndex));
            return piece.IsNull;
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

        /// <summary>
        /// Represents the current castling rights status
        /// </summary>
        private class CastlingRightsStatus
        {
            public CastlingStatus Status { get; set; }
            public bool KingsideAvailable { get; set; }
            public bool QueensideAvailable { get; set; }
        }

        private enum CastlingStatus
        {
            BothAvailable,      // Both kingside and queenside available
            KingsideOnly,       // Only kingside available
            QueensideOnly,      // Only queenside available
            AlreadyCastled,     // King has castled
            RightsLost          // All castling rights lost
        }
    }
}
