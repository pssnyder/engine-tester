using C0BR4ChessEngine.Core;

namespace C0BR4ChessEngine.Evaluation
{
    /// <summary>
    /// Evaluates king safety based on pawn shelter, piece attacks, and positioning
    /// More important in middlegame when pieces are active
    /// </summary>
    public static class KingSafety
    {
        // Safety penalties in centipawns
        private const int ExposedKingPenalty = 20;        // King without pawn shelter
        private const int WeakPawnShieldPenalty = 10;     // Damaged pawn shield
        private const int OpenFileNearKingPenalty = 15;   // Open file adjacent to king
        private const int EnemyPieceNearKingPenalty = 5;  // Enemy piece attacking near king
        private const int CastlingBonus = 15;             // Bonus for having castled
        private const int AdvancedPawnShieldPenalty = 8;  // Pawns too far advanced

        // Attack weights by piece type
        private static readonly Dictionary<PieceType, int> AttackWeights = new()
        {
            { PieceType.Pawn, 1 },
            { PieceType.Knight, 2 },
            { PieceType.Bishop, 2 },
            { PieceType.Rook, 3 },
            { PieceType.Queen, 4 }
        };

        /// <summary>
        /// Evaluate king safety for both sides
        /// </summary>
        /// <param name="board">Current board position</param>
        /// <param name="gamePhase">Game phase (0.0 = endgame, 1.0 = opening)</param>
        /// <returns>Evaluation from white's perspective</returns>
        public static int Evaluate(Board board, double gamePhase)
        {
            // King safety is much more important in middlegame
            double safetyWeight = 0.3 + gamePhase * 0.7; // 30-100% weight

            int whiteEval = EvaluateKingSafetyForSide(board, true, gamePhase);
            int blackEval = EvaluateKingSafetyForSide(board, false, gamePhase);
            
            return (int)((whiteEval - blackEval) * safetyWeight);
        }

        /// <summary>
        /// Evaluate king safety for one side
        /// </summary>
        private static int EvaluateKingSafetyForSide(Board board, bool isWhite, double gamePhase)
        {
            var king = FindKing(board, isWhite);
            if (king.IsNull)
                return -1000; // Huge penalty for missing king

            int safety = 0;

            // Evaluate pawn shield
            safety += EvaluatePawnShield(board, king, gamePhase);

            // Evaluate nearby file status
            safety += EvaluateNearbyFiles(board, king);

            // Evaluate enemy attacks near king
            safety += EvaluateEnemyAttacks(board, king, gamePhase);

            // Evaluate castling status
            safety += EvaluateCastlingStatus(board, king);

            // King position relative to center (more important in middlegame)
            safety += EvaluateKingPosition(king, gamePhase);

            return safety;
        }

        /// <summary>
        /// Evaluate the pawn shield around the king
        /// </summary>
        private static int EvaluatePawnShield(Board board, Piece king, double gamePhase)
        {
            int evaluation = 0;
            int kingFile = GetFile(king);
            int kingRank = GetRank(king);
            bool isWhite = king.IsWhite;

            // Check pawns in front of king (and diagonally)
            int[] filesToCheck = { kingFile - 1, kingFile, kingFile + 1 };
            int pawnDirection = isWhite ? 1 : -1;

            int shieldPawns = 0;
            int advancedPawns = 0;

            foreach (int file in filesToCheck)
            {
                if (file < 0 || file > 7) continue;

                // Check for pawn shield (1-2 ranks ahead)
                for (int rankOffset = 1; rankOffset <= 2; rankOffset++)
                {
                    int checkRank = kingRank + (pawnDirection * rankOffset);
                    if (checkRank < 0 || checkRank > 7) continue;

                    var piece = board.GetPiece(new Square(checkRank * 8 + file));
                    if (!piece.IsNull && piece.PieceType == PieceType.Pawn && piece.IsWhite == isWhite)
                    {
                        shieldPawns++;
                        
                        // Penalty for pawns advanced too far
                        if (rankOffset > 1)
                        {
                            advancedPawns++;
                        }
                        break; // Found pawn on this file
                    }
                }
            }

            // Bonus for having pawn shield
            if (shieldPawns >= 2)
            {
                evaluation += (int)(CastlingBonus * gamePhase); // More valuable in middlegame
            }
            else if (shieldPawns == 0)
            {
                evaluation -= (int)(ExposedKingPenalty * gamePhase);
            }
            else
            {
                evaluation -= (int)(WeakPawnShieldPenalty * gamePhase);
            }

            // Penalty for advanced shield pawns
            evaluation -= (int)(advancedPawns * AdvancedPawnShieldPenalty * gamePhase);

            return evaluation;
        }

        /// <summary>
        /// Evaluate open/semi-open files near the king
        /// </summary>
        private static int EvaluateNearbyFiles(Board board, Piece king)
        {
            int evaluation = 0;
            int kingFile = GetFile(king);

            // Check files adjacent to king
            for (int fileOffset = -1; fileOffset <= 1; fileOffset++)
            {
                int file = kingFile + fileOffset;
                if (file < 0 || file > 7) continue;

                var fileStatus = GetFileStatus(board, file);
                if (fileStatus == FileStatus.Open)
                {
                    evaluation -= OpenFileNearKingPenalty;
                }
            }

            return evaluation;
        }

        /// <summary>
        /// Evaluate enemy attacks in the king's vicinity
        /// </summary>
        private static int EvaluateEnemyAttacks(Board board, Piece king, double gamePhase)
        {
            int evaluation = 0;
            int kingFile = GetFile(king);
            int kingRank = GetRank(king);
            bool isWhite = king.IsWhite;

            // Check squares around the king (3x3 area)
            for (int rankOffset = -1; rankOffset <= 1; rankOffset++)
            {
                for (int fileOffset = -1; fileOffset <= 1; fileOffset++)
                {
                    int checkRank = kingRank + rankOffset;
                    int checkFile = kingFile + fileOffset;
                    
                    if (checkRank < 0 || checkRank > 7 || checkFile < 0 || checkFile > 7)
                        continue;

                    var square = new Square(checkRank * 8 + checkFile);
                    int attackCount = CountEnemyAttacks(board, square, isWhite);
                    
                    if (attackCount > 0)
                    {
                        evaluation -= (int)(EnemyPieceNearKingPenalty * attackCount * gamePhase);
                    }
                }
            }

            return evaluation;
        }

        /// <summary>
        /// Count enemy attacks on a square (simplified)
        /// </summary>
        private static int CountEnemyAttacks(Board board, Square square, bool forWhite)
        {
            int attacks = 0;

            // Check all enemy pieces for attacks on this square
            for (int sq = 0; sq < 64; sq++)
            {
                var piece = board.GetPiece(new Square(sq));
                if (piece.IsNull || piece.IsWhite == forWhite)
                    continue;

                // Simplified attack check - in a full implementation, this would use move generation
                if (CanAttackSquare(piece, square))
                {
                    if (AttackWeights.TryGetValue(piece.PieceType, out int weight))
                    {
                        attacks += weight;
                    }
                }
            }

            return attacks;
        }

        /// <summary>
        /// Simplified check if a piece can attack a square
        /// </summary>
        private static bool CanAttackSquare(Piece piece, Square target)
        {
            int fromFile = GetFile(piece);
            int fromRank = GetRank(piece);
            int toFile = target.Index % 8;
            int toRank = target.Index / 8;

            int fileDiff = Math.Abs(toFile - fromFile);
            int rankDiff = Math.Abs(toRank - fromRank);

            return piece.PieceType switch
            {
                PieceType.Pawn => IsPawnAttack(piece, target),
                PieceType.Knight => (fileDiff == 2 && rankDiff == 1) || (fileDiff == 1 && rankDiff == 2),
                PieceType.Bishop => fileDiff == rankDiff && fileDiff > 0,
                PieceType.Rook => (fileDiff == 0) != (rankDiff == 0), // Either same file or same rank
                PieceType.Queen => (fileDiff == rankDiff && fileDiff > 0) || ((fileDiff == 0) != (rankDiff == 0)),
                PieceType.King => fileDiff <= 1 && rankDiff <= 1 && (fileDiff + rankDiff) > 0,
                _ => false
            };
        }

        /// <summary>
        /// Check if pawn can attack target square
        /// </summary>
        private static bool IsPawnAttack(Piece pawn, Square target)
        {
            int fromFile = GetFile(pawn);
            int fromRank = GetRank(pawn);
            int toFile = target.Index % 8;
            int toRank = target.Index / 8;

            int fileDiff = Math.Abs(toFile - fromFile);
            int rankDiff = toRank - fromRank;

            // Pawn attacks diagonally forward
            if (pawn.IsWhite)
            {
                return fileDiff == 1 && rankDiff == 1;
            }
            else
            {
                return fileDiff == 1 && rankDiff == -1;
            }
        }

        /// <summary>
        /// Evaluate castling status
        /// </summary>
        private static int EvaluateCastlingStatus(Board board, Piece king)
        {
            int evaluation = 0;
            int expectedKingSquare = king.IsWhite ? 4 : 60; // e1 for white, e8 for black

            // If king has moved from starting position, assume castling has occurred or rights lost
            if (king.Square.Index != expectedKingSquare)
            {
                // Check if king is in a castled position
                if (IsCastledPosition(king))
                {
                    evaluation += CastlingBonus;
                }
                // If not castled and not on starting square, penalty for losing castling rights
                else
                {
                    evaluation -= WeakPawnShieldPenalty;
                }
            }

            return evaluation;
        }

        /// <summary>
        /// Check if king is in a typical castled position
        /// </summary>
        private static bool IsCastledPosition(Piece king)
        {
            int kingSquare = king.Square.Index;
            
            if (king.IsWhite)
            {
                return kingSquare == 6 || kingSquare == 2; // g1 or c1 (kingside/queenside)
            }
            else
            {
                return kingSquare == 62 || kingSquare == 58; // g8 or c8
            }
        }

        /// <summary>
        /// Evaluate king position relative to center (safety vs activity trade-off)
        /// </summary>
        private static int EvaluateKingPosition(Piece king, double gamePhase)
        {
            int file = GetFile(king);
            int rank = GetRank(king);

            // Distance from corner (safety in middlegame)
            int distanceFromNearestCorner = Math.Min(
                Math.Min(file, 7 - file), 
                Math.Min(rank, 7 - rank)
            );

            // In middlegame, prefer king away from center
            // In endgame, king activity becomes more important
            if (gamePhase > 0.5) // Middlegame
            {
                return distanceFromNearestCorner * 2; // Bonus for being near edges
            }
            else // Endgame
            {
                // In endgame, king activity is more important than safety
                return 0; // Neutral evaluation for position
            }
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

        /// <summary>
        /// Determine the status of a file
        /// </summary>
        private static FileStatus GetFileStatus(Board board, int file)
        {
            bool hasPawn = false;

            for (int rank = 0; rank < 8; rank++)
            {
                var piece = board.GetPiece(new Square(rank * 8 + file));
                if (!piece.IsNull && piece.PieceType == PieceType.Pawn)
                {
                    hasPawn = true;
                    break;
                }
            }

            return hasPawn ? FileStatus.Closed : FileStatus.Open;
        }

        private static int GetFile(Piece piece) => piece.Square.Index % 8;
        private static int GetRank(Piece piece) => piece.Square.Index / 8;

        private enum FileStatus
        {
            Closed,    // Has pawns
            Open       // No pawns
        }
    }
}
