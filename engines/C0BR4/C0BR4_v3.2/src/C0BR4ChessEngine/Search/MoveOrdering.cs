using System;
using System.Collections.Generic;
using System.Linq;
using C0BR4ChessEngine.Core;

namespace C0BR4ChessEngine.Search
{
    /// <summary>
    /// Move ordering utility to improve alpha-beta pruning efficiency
    /// Orders moves by expected strength: captures, promotions, checks, then others
    /// </summary>
    public static class MoveOrdering
    {
        /// <summary>
        /// Order moves for better alpha-beta pruning
        /// Most promising moves first to maximize cutoffs
        /// </summary>
        public static Move[] OrderMoves(Board board, Move[] moves)
        {
            if (moves.Length <= 1) return moves;

            // Create array of moves with their scores for sorting
            var scoredMoves = new (Move move, int score)[moves.Length];
            
            for (int i = 0; i < moves.Length; i++)
            {
                scoredMoves[i] = (moves[i], ScoreMove(board, moves[i]));
            }

            // Sort by score (highest first)
            Array.Sort(scoredMoves, (a, b) => b.score.CompareTo(a.score));

            // Extract the ordered moves
            var orderedMoves = new Move[moves.Length];
            for (int i = 0; i < moves.Length; i++)
            {
                orderedMoves[i] = scoredMoves[i].move;
            }

            return orderedMoves;
        }

        /// <summary>
        /// Score a move for ordering purposes
        /// Higher scores = more promising moves that should be searched first
        /// </summary>
        private static int ScoreMove(Board board, Move move)
        {
            int score = 0;

            // Get piece types
            var movingPiece = board.GetPiece(move.StartSquare);
            var targetPiece = board.GetPiece(move.TargetSquare);

            // 1. Captures - prioritize by value difference (MVV-LVA: Most Valuable Victim - Least Valuable Attacker)
            if (targetPiece.PieceType != PieceType.None)
            {
                int captureValue = GetPieceValue(targetPiece.PieceType) - GetPieceValue(movingPiece.PieceType);
                score += 10000 + captureValue; // Base capture score + value difference
            }

            // 2. Promotions - very valuable
            if (move.PromotionPieceType != PieceType.None)
            {
                score += 9000 + GetPieceValue(move.PromotionPieceType);
            }

            // 3. Checks - often strong moves
            board.MakeMove(move);
            bool givesCheck = board.IsInCheck();
            board.UnmakeMove();
            
            if (givesCheck)
            {
                score += 500;
            }

            // 4. Center control (minor bonus)
            if (IsCenter(move.TargetSquare))
            {
                score += 10;
            }

            // 5. Piece development (minor bonus for knights and bishops)
            if ((movingPiece.PieceType == PieceType.Knight || movingPiece.PieceType == PieceType.Bishop))
            {
                if (IsBackRank(move.StartSquare, movingPiece.IsWhite))
                {
                    score += 5; // Development from back rank
                }
            }

            return score;
        }

        /// <summary>
        /// Get the relative value of a piece type for capture ordering
        /// </summary>
        private static int GetPieceValue(PieceType pieceType)
        {
            return pieceType switch
            {
                PieceType.Pawn => 100,
                PieceType.Knight => 300,
                PieceType.Bishop => 300,
                PieceType.Rook => 500,
                PieceType.Queen => 900,
                PieceType.King => 10000, // Should never be captured, but just in case
                _ => 0
            };
        }

        /// <summary>
        /// Check if a square is in the center (e4, e5, d4, d5)
        /// </summary>
        private static bool IsCenter(Square square)
        {
            int file = square.File;
            int rank = square.Rank;
            return (file == 3 || file == 4) && (rank == 3 || rank == 4); // d4, d5, e4, e5
        }

        /// <summary>
        /// Check if a square is on the back rank for the given color
        /// </summary>
        private static bool IsBackRank(Square square, bool isWhite)
        {
            return isWhite ? square.Rank == 0 : square.Rank == 7;
        }
    }
}
