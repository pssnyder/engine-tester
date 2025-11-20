using C0BR4ChessEngine.Core;

namespace C0BR4ChessEngine.Opening
{
    /// <summary>
    /// Simple algebraic notation parser for opening book moves
    /// Handles basic move notation like e4, Nf3, O-O, etc.
    /// </summary>
    public static class AlgebraicNotation
    {
        /// <summary>
        /// Parse an algebraic notation move and find the corresponding legal move
        /// </summary>
        /// <param name="board">Current board position</param>
        /// <param name="algebraic">Move in algebraic notation (e.g., "e4", "Nf3", "O-O")</param>
        /// <returns>Matching Move object, or null if not found</returns>
        public static Move? ParseMove(Board board, string algebraic)
        {
            if (string.IsNullOrEmpty(algebraic))
                return null;

            var legalMoves = board.GetLegalMoves();
            
            // Handle castling
            if (algebraic == "O-O" || algebraic == "0-0")
            {
                return FindCastlingMove(legalMoves, true); // Kingside
            }
            if (algebraic == "O-O-O" || algebraic == "0-0-0")
            {
                return FindCastlingMove(legalMoves, false); // Queenside
            }

            // Clean up the notation
            string clean = algebraic.Replace("+", "").Replace("#", "").Replace("x", "");
            
            // Handle pawn moves (no piece prefix)
            if (char.IsLower(clean[0]) && clean.Length >= 2)
            {
                return FindPawnMove(board, legalMoves, clean);
            }
            
            // Handle piece moves (piece prefix)
            if (clean.Length >= 3 && char.IsUpper(clean[0]))
            {
                return FindPieceMove(board, legalMoves, clean);
            }

            return null;
        }

        /// <summary>
        /// Find castling move in legal moves
        /// </summary>
        private static Move? FindCastlingMove(Move[] legalMoves, bool kingside)
        {
            foreach (var move in legalMoves)
            {
                // Check if this is a king move that looks like castling
                if (move.MovePieceType == PieceType.King)
                {
                    int fromFile = move.StartSquare.Index % 8;
                    int toFile = move.TargetSquare.Index % 8;
                    
                    // King starting from e-file (4)
                    if (fromFile == 4)
                    {
                        if (kingside && toFile == 6) // King to g-file
                            return move;
                        if (!kingside && toFile == 2) // King to c-file
                            return move;
                    }
                }
            }
            return null;
        }

        /// <summary>
        /// Find pawn move in legal moves
        /// </summary>
        private static Move? FindPawnMove(Board board, Move[] legalMoves, string notation)
        {
            // Parse destination square
            if (notation.Length < 2)
                return null;

            string destSquare = notation.Substring(notation.Length - 2);
            if (!TryParseSquare(destSquare, out int targetSquare))
                return null;

            foreach (var move in legalMoves)
            {
                if (move.MovePieceType == PieceType.Pawn && move.TargetSquare.Index == targetSquare)
                {
                    // If capture notation (like exd4), check source file
                    if (notation.Length >= 3 && char.IsLetter(notation[0]))
                    {
                        int sourceFile = notation[0] - 'a';
                        int moveSourceFile = move.StartSquare.Index % 8;
                        if (sourceFile == moveSourceFile)
                            return move;
                    }
                    else
                    {
                        // Simple pawn move (like e4)
                        return move;
                    }
                }
            }
            return null;
        }

        /// <summary>
        /// Find piece move in legal moves
        /// </summary>
        private static Move? FindPieceMove(Board board, Move[] legalMoves, string notation)
        {
            if (notation.Length < 3)
                return null;

            // Parse piece type
            PieceType pieceType = notation[0] switch
            {
                'N' => PieceType.Knight,
                'B' => PieceType.Bishop,
                'R' => PieceType.Rook,
                'Q' => PieceType.Queen,
                'K' => PieceType.King,
                _ => PieceType.None
            };

            if (pieceType == PieceType.None)
                return null;

            // Parse destination square (last 2 characters)
            string destSquare = notation.Substring(notation.Length - 2);
            if (!TryParseSquare(destSquare, out int targetSquare))
                return null;

            // Find matching moves
            var candidates = new List<Move>();
            foreach (var move in legalMoves)
            {
                if (move.MovePieceType == pieceType && move.TargetSquare.Index == targetSquare)
                {
                    candidates.Add(move);
                }
            }

            if (candidates.Count == 1)
                return candidates[0];

            // Handle disambiguation if multiple candidates
            if (candidates.Count > 1 && notation.Length >= 4)
            {
                char disambig = notation[1];
                
                // File disambiguation (like Nbd2)
                if (char.IsLetter(disambig))
                {
                    int sourceFile = disambig - 'a';
                    foreach (var move in candidates)
                    {
                        if (move.StartSquare.Index % 8 == sourceFile)
                            return move;
                    }
                }
                
                // Rank disambiguation (like N1d2)
                if (char.IsDigit(disambig))
                {
                    int sourceRank = disambig - '1';
                    foreach (var move in candidates)
                    {
                        if (move.StartSquare.Index / 8 == sourceRank)
                            return move;
                    }
                }
            }

            // Return first candidate if no disambiguation worked
            return candidates.Count > 0 ? candidates[0] : null;
        }

        /// <summary>
        /// Parse square notation like "e4" into square index
        /// </summary>
        private static bool TryParseSquare(string square, out int index)
        {
            index = 0;
            
            if (string.IsNullOrEmpty(square) || square.Length != 2)
                return false;

            char file = square[0];
            char rank = square[1];

            if (file < 'a' || file > 'h' || rank < '1' || rank > '8')
                return false;

            int fileIndex = file - 'a';
            int rankIndex = rank - '1';
            
            index = rankIndex * 8 + fileIndex;
            return true;
        }

        /// <summary>
        /// Convert a Move to basic algebraic notation
        /// </summary>
        public static string ToAlgebraic(Move move)
        {
            // Simple conversion - just return the move's string representation for now
            return move.ToString();
        }
    }
}
