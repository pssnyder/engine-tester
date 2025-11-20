using C0BR4ChessEngine.Core;

namespace C0BR4ChessEngine.Evaluation
{
    /// <summary>
    /// Evaluates king activity and positioning in endgames
    /// In endgames, the king becomes an active piece that should centralize and support pawns
    /// </summary>
    public static class KingEndgame
    {
        // Evaluation bonuses/penalties in centipawns
        private const int CentralizationBonus = 8;         // Bonus per square closer to center
        private const int PawnSupportBonus = 15;           // Supporting passed/advanced pawns
        private const int EnemyPawnOppositionBonus = 10;   // Opposing enemy pawns
        private const int ActivityBonus = 5;               // General activity bonus
        private const int CornerDistanceBonus = 3;         // Bonus for being away from corners

        // Centralization table for king endgame positioning
        private static readonly int[,] CentralizationTable = new int[8, 8]
        {
            { -30, -20, -10,  -5,  -5, -10, -20, -30 },
            { -20,  -5,   5,  10,  10,   5,  -5, -20 },
            { -10,   5,  15,  20,  20,  15,   5, -10 },
            {  -5,  10,  20,  25,  25,  20,  10,  -5 },
            {  -5,  10,  20,  25,  25,  20,  10,  -5 },
            { -10,   5,  15,  20,  20,  15,   5, -10 },
            { -20,  -5,   5,  10,  10,   5,  -5, -20 },
            { -30, -20, -10,  -5,  -5, -10, -20, -30 }
        };

        /// <summary>
        /// Evaluate king endgame activity for both sides
        /// Only applies significant evaluation in endgame phase
        /// </summary>
        /// <param name="board">Current board position</param>
        /// <param name="gamePhase">Game phase (0.0 = endgame, 1.0 = opening)</param>
        /// <returns>Evaluation from white's perspective</returns>
        public static int Evaluate(Board board, double gamePhase)
        {
            // King activity is only important in endgame
            double endgameWeight = 1.0 - gamePhase; // 0-100% weight, strongest in pure endgame
            
            if (endgameWeight < 0.2) // Not enough of an endgame to matter
                return 0;

            int whiteEval = EvaluateKingEndgameForSide(board, true);
            int blackEval = EvaluateKingEndgameForSide(board, false);
            
            return (int)((whiteEval - blackEval) * endgameWeight);
        }

        /// <summary>
        /// Evaluate king endgame activity for one side
        /// </summary>
        private static int EvaluateKingEndgameForSide(Board board, bool isWhite)
        {
            var king = FindKing(board, isWhite);
            if (king.IsNull)
                return -1000; // Huge penalty for missing king

            int evaluation = 0;

            // Centralization bonus
            evaluation += EvaluateCentralization(king);

            // Pawn support evaluation
            evaluation += EvaluatePawnSupport(board, king);

            // Opposition and pawn races
            evaluation += EvaluateOpposition(board, king);

            // General activity (distance from edges)
            evaluation += EvaluateActivity(king);

            return evaluation;
        }

        /// <summary>
        /// Evaluate king centralization using piece-square table
        /// </summary>
        private static int EvaluateCentralization(Piece king)
        {
            int file = GetFile(king);
            int rank = GetRank(king);

            // Use centralization table, but flip for black
            if (king.IsWhite)
            {
                return CentralizationTable[rank, file];
            }
            else
            {
                return CentralizationTable[7 - rank, file];
            }
        }

        /// <summary>
        /// Evaluate king's support of pawns, especially passed pawns
        /// </summary>
        private static int EvaluatePawnSupport(Board board, Piece king)
        {
            int evaluation = 0;
            int kingFile = GetFile(king);
            int kingRank = GetRank(king);
            bool isWhite = king.IsWhite;

            // Find all pawns for this side
            var ownPawns = FindPawns(board, isWhite);
            
            foreach (var pawn in ownPawns)
            {
                int pawnFile = GetFile(pawn);
                int pawnRank = GetRank(pawn);
                
                // Calculate distance between king and pawn
                int distance = Math.Max(Math.Abs(kingFile - pawnFile), Math.Abs(kingRank - pawnRank));
                
                // Check if pawn is passed
                bool isPassed = IsPawnPassed(board, pawn);
                
                // Check if pawn is advanced
                bool isAdvanced = IsAdvancedPawn(pawn);
                
                // Bonus for supporting important pawns
                if (isPassed || isAdvanced)
                {
                    // Closer support gives higher bonus
                    int supportBonus = PawnSupportBonus - (distance * 2);
                    if (supportBonus > 0)
                    {
                        evaluation += supportBonus;
                        
                        // Extra bonus for passed pawns
                        if (isPassed)
                        {
                            evaluation += 5;
                        }
                    }
                }
            }

            return evaluation;
        }

        /// <summary>
        /// Evaluate opposition and coordination with enemy king
        /// </summary>
        private static int EvaluateOpposition(Board board, Piece king)
        {
            int evaluation = 0;
            var enemyKing = FindKing(board, !king.IsWhite);
            
            if (enemyKing.IsNull)
                return 0;

            int kingFile = GetFile(king);
            int kingRank = GetRank(king);
            int enemyFile = GetFile(enemyKing);
            int enemyRank = GetRank(enemyKing);

            // Calculate distance between kings
            int fileDistance = Math.Abs(kingFile - enemyFile);
            int rankDistance = Math.Abs(kingRank - enemyRank);
            int kingDistance = Math.Max(fileDistance, rankDistance);

            // Opposition evaluation (being one square away on same rank/file)
            if (kingDistance == 2)
            {
                if (fileDistance == 0 || rankDistance == 0) // Same file or rank
                {
                    evaluation += EnemyPawnOppositionBonus;
                }
            }

            // Evaluate king positioning relative to enemy pawns
            var enemyPawns = FindPawns(board, !king.IsWhite);
            foreach (var enemyPawn in enemyPawns)
            {
                int pawnFile = GetFile(enemyPawn);
                int pawnRank = GetRank(enemyPawn);
                
                // Bonus for being in front of enemy pawns (blocking)
                if (Math.Abs(kingFile - pawnFile) <= 1)
                {
                    bool isBlockingPath = king.IsWhite ? 
                        kingRank > pawnRank : 
                        kingRank < pawnRank;
                    
                    if (isBlockingPath)
                    {
                        evaluation += EnemyPawnOppositionBonus / 2;
                    }
                }
            }

            return evaluation;
        }

        /// <summary>
        /// Evaluate general king activity (distance from corners and edges)
        /// </summary>
        private static int EvaluateActivity(Piece king)
        {
            int file = GetFile(king);
            int rank = GetRank(king);

            // Bonus for being away from corners
            int cornerDistance = Math.Min(
                Math.Min(file + rank, file + (7 - rank)),
                Math.Min((7 - file) + rank, (7 - file) + (7 - rank))
            );

            return cornerDistance * CornerDistanceBonus;
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
        /// Check if a pawn is advanced (on 6th rank or beyond)
        /// </summary>
        private static bool IsAdvancedPawn(Piece pawn)
        {
            int rank = GetRank(pawn);
            return pawn.IsWhite ? rank >= 5 : rank <= 2; // 6th rank+ for white, 3rd rank- for black
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
    }
}
