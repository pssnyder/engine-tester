using C0BR4ChessEngine.Core;

namespace C0BR4ChessEngine.Evaluation
{
    /// <summary>
    /// Evaluates castling incentives and castling rights
    /// Encourages castling in middlegame and penalizes loss of castling rights
    /// </summary>
    public static class CastlingIncentive
    {
        // Evaluation values in centipawns
        private const int CastlingRightsBonus = 20;        // Having castling rights available
        private const int CastledBonus = 25;               // Successfully castled
        private const int LostCastlingRightsPenalty = 30;  // Lost castling rights without castling
        private const int KingsideCastlingBonus = 5;       // Slight preference for kingside
        private const int EarlyCastlingBonus = 10;         // Bonus for castling early
        private const int DelayedCastlingPenalty = 15;     // Penalty for delaying too long

        // Game phase thresholds
        private const double EarlyGameThreshold = 0.8;     // Above this is early game
        private const double MiddleGameThreshold = 0.3;    // Below this is endgame

        /// <summary>
        /// Evaluate castling incentives for both sides
        /// </summary>
        /// <param name="board">Current board position</param>
        /// <param name="gamePhase">Game phase (0.0 = endgame, 1.0 = opening)</param>
        /// <returns>Evaluation from white's perspective</returns>
        public static int Evaluate(Board board, double gamePhase)
        {
            // Castling is primarily a middlegame concern
            double castlingWeight = Math.Max(0.2, gamePhase); // Minimum 20% weight, up to 100%
            
            int whiteEval = EvaluateCastlingForSide(board, true, gamePhase);
            int blackEval = EvaluateCastlingForSide(board, false, gamePhase);
            
            return (int)((whiteEval - blackEval) * castlingWeight);
        }

        /// <summary>
        /// Evaluate castling situation for one side
        /// </summary>
        private static int EvaluateCastlingForSide(Board board, bool isWhite, double gamePhase)
        {
            int evaluation = 0;
            var king = FindKing(board, isWhite);
            
            if (king.IsNull)
                return 0;

            var castlingStatus = DetermineCastlingStatus(board, king);

            switch (castlingStatus)
            {
                case CastlingStatus.HasRights:
                    evaluation += EvaluateAvailableCastling(board, king, gamePhase);
                    break;
                
                case CastlingStatus.Castled:
                    evaluation += EvaluateCompletedCastling(board, king, gamePhase);
                    break;
                
                case CastlingStatus.LostRights:
                    evaluation += EvaluateLostCastling(board, king, gamePhase);
                    break;
            }

            return evaluation;
        }

        /// <summary>
        /// Evaluate when castling rights are still available
        /// </summary>
        private static int EvaluateAvailableCastling(Board board, Piece king, double gamePhase)
        {
            int evaluation = 0;
            
            // Bonus for maintaining castling rights
            evaluation += CastlingRightsBonus;

            // Encourage early castling in middlegame
            if (gamePhase > EarlyGameThreshold)
            {
                evaluation += EarlyCastlingBonus;
            }
            else if (gamePhase > MiddleGameThreshold)
            {
                // Small penalty for delaying castling too long
                evaluation -= (int)(DelayedCastlingPenalty * (1.0 - gamePhase));
            }

            // Evaluate safety of castling
            evaluation += EvaluateCastlingSafety(board, king);

            return evaluation;
        }

        /// <summary>
        /// Evaluate when king has successfully castled
        /// </summary>
        private static int EvaluateCompletedCastling(Board board, Piece king, double gamePhase)
        {
            int evaluation = CastledBonus;
            
            // Bonus for castling type
            if (IsCastledKingside(king))
            {
                evaluation += KingsideCastlingBonus; // Slight preference for kingside
            }

            // Extra bonus for early castling
            if (gamePhase > EarlyGameThreshold)
            {
                evaluation += EarlyCastlingBonus;
            }

            return evaluation;
        }

        /// <summary>
        /// Evaluate when castling rights have been lost without castling
        /// </summary>
        private static int EvaluateLostCastling(Board board, Piece king, double gamePhase)
        {
            int penalty = 0;
            
            // Penalty for losing castling rights, worse in middlegame
            penalty -= (int)(LostCastlingRightsPenalty * gamePhase);

            // Additional penalty if king is exposed
            if (IsKingExposed(board, king))
            {
                penalty -= (int)(20 * gamePhase); // Extra penalty for exposed king
            }

            return penalty;
        }

        /// <summary>
        /// Evaluate the safety of potential castling positions
        /// </summary>
        private static int EvaluateCastlingSafety(Board board, Piece king)
        {
            int safety = 0;
            bool isWhite = king.IsWhite;

            // Check kingside castling safety
            if (CanCastleKingside(board, king))
            {
                safety += EvaluateCastlingSquareSafety(board, isWhite, true);
            }

            // Check queenside castling safety
            if (CanCastleQueenside(board, king))
            {
                safety += EvaluateCastlingSquareSafety(board, isWhite, false);
            }

            return safety;
        }

        /// <summary>
        /// Evaluate safety of castling squares (simplified)
        /// </summary>
        private static int EvaluateCastlingSquareSafety(Board board, bool isWhite, bool kingside)
        {
            int safety = 0;
            int baseRank = isWhite ? 0 : 7;
            
            // Squares the king would pass through
            int[] squaresToCheck = kingside ? 
                new int[] { 5, 6 } :      // f1/f8, g1/g8 for kingside
                new int[] { 2, 3 };       // c1/c8, d1/d8 for queenside

            foreach (int file in squaresToCheck)
            {
                var square = new Square(baseRank * 8 + file);
                
                // Penalty if square is attacked by enemy
                if (IsSquareAttackedByEnemy(board, square, isWhite))
                {
                    safety -= 10;
                }
            }

            return safety;
        }

        /// <summary>
        /// Determine the current castling status
        /// </summary>
        private static CastlingStatus DetermineCastlingStatus(Board board, Piece king)
        {
            int kingSquare = king.Square.Index;
            int startingSquare = king.IsWhite ? 4 : 60; // e1 for white, e8 for black

            // If king is not on starting square
            if (kingSquare != startingSquare)
            {
                // Check if in castled position
                if (IsCastledKingside(king) || IsCastledQueenside(king))
                {
                    return CastlingStatus.Castled;
                }
                else
                {
                    return CastlingStatus.LostRights;
                }
            }

            // King is on starting square - check if castling is still possible
            if (HasCastlingRights(board, king))
            {
                return CastlingStatus.HasRights;
            }
            else
            {
                return CastlingStatus.LostRights;
            }
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
        /// Simplified check for castling rights (checks rook positions)
        /// </summary>
        private static bool HasCastlingRights(Board board, Piece king)
        {
            bool isWhite = king.IsWhite;
            int backRank = isWhite ? 0 : 7;

            // Check if rooks are on starting squares
            bool kingsideRook = CheckRookOnSquare(board, backRank * 8 + 7, isWhite); // h1/h8
            bool queensideRook = CheckRookOnSquare(board, backRank * 8 + 0, isWhite); // a1/a8

            return kingsideRook || queensideRook;
        }

        /// <summary>
        /// Check if specific castling direction is possible (simplified)
        /// </summary>
        private static bool CanCastleKingside(Board board, Piece king)
        {
            bool isWhite = king.IsWhite;
            int backRank = isWhite ? 0 : 7;
            
            // Check rook presence
            if (!CheckRookOnSquare(board, backRank * 8 + 7, isWhite))
                return false;

            // Check if path is clear
            return IsPathClear(board, backRank * 8 + 5, backRank * 8 + 6);
        }

        /// <summary>
        /// Check if queenside castling is possible (simplified)
        /// </summary>
        private static bool CanCastleQueenside(Board board, Piece king)
        {
            bool isWhite = king.IsWhite;
            int backRank = isWhite ? 0 : 7;
            
            // Check rook presence
            if (!CheckRookOnSquare(board, backRank * 8 + 0, isWhite))
                return false;

            // Check if path is clear
            return IsPathClear(board, backRank * 8 + 1, backRank * 8 + 3);
        }

        /// <summary>
        /// Check if there's a rook of the correct color on a specific square
        /// </summary>
        private static bool CheckRookOnSquare(Board board, int square, bool isWhite)
        {
            var piece = board.GetPiece(new Square(square));
            return !piece.IsNull && piece.PieceType == PieceType.Rook && piece.IsWhite == isWhite;
        }

        /// <summary>
        /// Check if path between squares is clear
        /// </summary>
        private static bool IsPathClear(Board board, int startSquare, int endSquare)
        {
            for (int square = startSquare; square <= endSquare; square++)
            {
                var piece = board.GetPiece(new Square(square));
                if (!piece.IsNull)
                    return false;
            }
            return true;
        }

        /// <summary>
        /// Check if king is in an exposed position
        /// </summary>
        private static bool IsKingExposed(Board board, Piece king)
        {
            // Simplified: check if king has moved from back rank without castling
            int rank = GetRank(king);
            int expectedRank = king.IsWhite ? 0 : 7;
            
            return rank != expectedRank && !IsCastledKingside(king) && !IsCastledQueenside(king);
        }

        /// <summary>
        /// Simplified check if square is attacked by enemy (placeholder)
        /// </summary>
        private static bool IsSquareAttackedByEnemy(Board board, Square square, bool byWhite)
        {
            // This is a simplified implementation
            // In a full engine, this would use proper attack detection
            return false; // Placeholder
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

        private static int GetRank(Piece piece) => piece.Square.Index / 8;

        private enum CastlingStatus
        {
            HasRights,   // Still has castling rights
            Castled,     // Successfully castled
            LostRights   // Lost castling rights without castling
        }
    }
}
