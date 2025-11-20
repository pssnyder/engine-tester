using C0BR4ChessEngine.Core;

namespace C0BR4ChessEngine.Evaluation
{
    /// <summary>
    /// Specialized evaluation for pure pawn endgames
    /// Provides aggressive pawn pushing bonuses to avoid threefold repetition in winning positions
    /// </summary>
    public static class PawnEndgame
    {
        // Aggressive bonuses for pawn endgames in centipawns
        private const int PassedPawnBonus = 50;              // Base bonus for passed pawns
        private const int AdvancedPawnMultiplier = 40;       // Bonus per rank advanced (exponential)
        private const int ProtectedPawnBonus = 30;           // Bonus for pawns protected by king
        private const int ConnectedPassedPawnBonus = 40;     // Extra bonus for connected passed pawns
        private const int UnstoppablePawnBonus = 500;        // Massive bonus for unstoppable pawns
        private const int PawnRaceBonus = 100;               // Bonus when ahead in pawn race
        private const int KingSupportBonus = 25;             // Bonus for king near passed pawns

        /// <summary>
        /// Evaluate pawn endgame positions with aggressive pawn pushing incentives
        /// Only applies when position is a pure pawn endgame (kings + pawns only)
        /// </summary>
        public static int Evaluate(Board board, double gamePhase)
        {
            // Only evaluate if we're in a pawn endgame
            if (!IsPawnEndgame(board))
                return 0;

            // Pure pawn endgames are always heavily weighted
            int whiteEval = EvaluatePawnEndgameForSide(board, true);
            int blackEval = EvaluatePawnEndgameForSide(board, false);

            return whiteEval - blackEval;
        }

        /// <summary>
        /// Check if position is a pure pawn endgame (only kings and pawns)
        /// </summary>
        private static bool IsPawnEndgame(Board board)
        {
            for (int square = 0; square < 64; square++)
            {
                var piece = board.GetPiece(new Square(square));
                if (!piece.IsNull)
                {
                    var type = piece.PieceType;
                    // If we find any piece that's not a king or pawn, it's not a pawn endgame
                    if (type != PieceType.King && type != PieceType.Pawn)
                        return false;
                }
            }
            return true;
        }

        /// <summary>
        /// Evaluate pawn endgame for one side with aggressive pushing incentives
        /// </summary>
        private static int EvaluatePawnEndgameForSide(Board board, bool isWhite)
        {
            int evaluation = 0;
            var king = FindKing(board, isWhite);
            var pawns = FindPawns(board, isWhite);
            var enemyKing = FindKing(board, !isWhite);
            var enemyPawns = FindPawns(board, !isWhite);

            if (king.IsNull || pawns.Count == 0)
                return 0;

            // Evaluate each pawn
            foreach (var pawn in pawns)
            {
                int pawnFile = GetFile(pawn);
                int pawnRank = GetRank(pawn);
                
                // Check if pawn is passed
                bool isPassed = IsPawnPassed(board, pawn);
                
                if (isPassed)
                {
                    // Base passed pawn bonus
                    evaluation += PassedPawnBonus;
                    
                    // Exponential bonus for advanced passed pawns
                    int advancementRank = isWhite ? pawnRank : (7 - pawnRank);
                    evaluation += advancementRank * advancementRank * AdvancedPawnMultiplier;
                    
                    // Check if pawn is protected by king
                    int kingDistance = GetDistance(king, pawn);
                    if (kingDistance <= 1)
                    {
                        evaluation += ProtectedPawnBonus;
                    }
                    
                    // Bonus for king supporting the pawn push
                    if (kingDistance <= 2)
                    {
                        evaluation += KingSupportBonus;
                    }
                    
                    // Check if pawn is unstoppable
                    if (IsUnstoppable(pawn, king, enemyKing))
                    {
                        evaluation += UnstoppablePawnBonus;
                    }
                    
                    // Check for connected passed pawns
                    if (HasConnectedPassedPawn(pawns, pawn))
                    {
                        evaluation += ConnectedPassedPawnBonus;
                    }
                }
                else
                {
                    // Even non-passed pawns should advance in pure pawn endgames
                    int advancementRank = isWhite ? pawnRank : (7 - pawnRank);
                    evaluation += advancementRank * 10; // Moderate bonus for advancement
                }
            }

            // Evaluate pawn races
            if (enemyPawns.Count > 0)
            {
                evaluation += EvaluatePawnRace(board, pawns, enemyPawns, king, enemyKing, isWhite);
            }

            return evaluation;
        }

        /// <summary>
        /// Evaluate pawn race situations
        /// </summary>
        private static int EvaluatePawnRace(Board board, List<Piece> ourPawns, List<Piece> enemyPawns, 
            Piece ourKing, Piece enemyKing, bool isWhite)
        {
            // Find our most advanced passed pawn
            Piece mostAdvanced = new Piece();
            int bestRank = isWhite ? -1 : 8;
            
            foreach (var pawn in ourPawns)
            {
                if (IsPawnPassed(board, pawn))
                {
                    int rank = GetRank(pawn);
                    bool isBetter = isWhite ? rank > bestRank : rank < bestRank;
                    if (isBetter)
                    {
                        bestRank = rank;
                        mostAdvanced = pawn;
                    }
                }
            }

            if (mostAdvanced.IsNull)
                return 0;

            // Find enemy's most advanced passed pawn
            Piece enemyMostAdvanced = new Piece();
            int enemyBestRank = isWhite ? 8 : -1;
            
            foreach (var pawn in enemyPawns)
            {
                if (IsPawnPassed(board, pawn))
                {
                    int rank = GetRank(pawn);
                    bool isBetter = isWhite ? rank < enemyBestRank : rank > enemyBestRank;
                    if (isBetter)
                    {
                        enemyBestRank = rank;
                        enemyMostAdvanced = pawn;
                    }
                }
            }

            if (enemyMostAdvanced.IsNull)
                return PawnRaceBonus; // We have passed pawn, they don't

            // Calculate race: how many moves to promotion?
            int ourDistance = isWhite ? (7 - bestRank) : bestRank;
            int enemyDistance = isWhite ? enemyBestRank : (7 - enemyBestRank);

            // Adjust for king blocking
            int enemyKingDist = GetDistance(enemyKing, mostAdvanced);
            int ourKingDist = GetDistance(ourKing, enemyMostAdvanced);

            if (enemyKingDist > ourDistance + 1)
            {
                // Our pawn can't be caught
                return PawnRaceBonus * 2;
            }

            if (ourDistance < enemyDistance)
            {
                // We're ahead in the race
                return PawnRaceBonus;
            }
            else if (ourDistance == enemyDistance && ourKingDist < enemyKingDist)
            {
                // Equal race, but our king is better positioned
                return PawnRaceBonus / 2;
            }

            return 0;
        }

        /// <summary>
        /// Check if a pawn is unstoppable (enemy king can't catch it)
        /// </summary>
        private static bool IsUnstoppable(Piece pawn, Piece ourKing, Piece enemyKing)
        {
            bool isWhite = pawn.IsWhite;
            int pawnRank = GetRank(pawn);
            int pawnFile = GetFile(pawn);
            
            // Distance to promotion
            int promotionRank = isWhite ? 7 : 0;
            int distanceToPromotion = Math.Abs(promotionRank - pawnRank);
            
            // Enemy king's distance to the promotion square
            int promotionSquare = promotionRank * 8 + pawnFile;
            int enemyKingFile = GetFile(enemyKing);
            int enemyKingRank = GetRank(enemyKing);
            int enemyKingDistance = Math.Max(
                Math.Abs(enemyKingFile - pawnFile),
                Math.Abs(enemyKingRank - promotionRank)
            );
            
            // If enemy king is too far away to catch the pawn
            // Rule: pawn needs distanceToPromotion moves, king needs enemyKingDistance moves
            // If king can't reach promotion square or queening path, pawn is unstoppable
            return enemyKingDistance > distanceToPromotion + 1;
        }

        /// <summary>
        /// Check if pawn has a connected passed pawn nearby
        /// </summary>
        private static bool HasConnectedPassedPawn(List<Piece> pawns, Piece pawn)
        {
            int file = GetFile(pawn);
            int rank = GetRank(pawn);
            
            foreach (var otherPawn in pawns)
            {
                if (otherPawn.Square.Index == pawn.Square.Index)
                    continue;
                    
                int otherFile = GetFile(otherPawn);
                int otherRank = GetRank(otherPawn);
                
                // Check if on adjacent file and similar rank
                if (Math.Abs(file - otherFile) == 1 && Math.Abs(rank - otherRank) <= 1)
                {
                    return true;
                }
            }
            
            return false;
        }

        /// <summary>
        /// Check if a pawn is passed (no enemy pawns blocking its path)
        /// </summary>
        private static bool IsPawnPassed(Board board, Piece pawn)
        {
            int pawnFile = GetFile(pawn);
            int pawnRank = GetRank(pawn);
            bool isWhite = pawn.IsWhite;

            // Check files: pawn's file and adjacent files
            for (int fileOffset = -1; fileOffset <= 1; fileOffset++)
            {
                int checkFile = pawnFile + fileOffset;
                if (checkFile < 0 || checkFile > 7) continue;

                // Check squares in front of the pawn
                int startRank = isWhite ? pawnRank + 1 : pawnRank - 1;
                int endRank = isWhite ? 8 : -1;
                int direction = isWhite ? 1 : -1;

                for (int rank = startRank; rank != endRank; rank += direction)
                {
                    if (rank < 0 || rank > 7) break;

                    var piece = board.GetPiece(new Square(rank * 8 + checkFile));
                    if (!piece.IsNull && piece.PieceType == PieceType.Pawn && piece.IsWhite != isWhite)
                    {
                        return false; // Found enemy pawn blocking
                    }
                }
            }

            return true; // No blocking pawns found
        }

        /// <summary>
        /// Find all pawns for a given side
        /// </summary>
        private static List<Piece> FindPawns(Board board, bool isWhite)
        {
            var pawns = new List<Piece>();
            
            for (int square = 0; square < 64; square++)
            {
                var piece = board.GetPiece(new Square(square));
                if (!piece.IsNull && piece.IsWhite == isWhite && piece.PieceType == PieceType.Pawn)
                {
                    pawns.Add(piece);
                }
            }
            
            return pawns;
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
        
        private static int GetDistance(Piece piece1, Piece piece2)
        {
            int file1 = GetFile(piece1);
            int rank1 = GetRank(piece1);
            int file2 = GetFile(piece2);
            int rank2 = GetRank(piece2);
            
            return Math.Max(Math.Abs(file1 - file2), Math.Abs(rank1 - rank2));
        }
    }
}
