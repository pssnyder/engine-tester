using C0BR4ChessEngine.Core;
using C0BR4ChessEngine.Evaluation;

namespace C0BR4ChessEngine.Evaluation
{
    /// <summary>
    /// Piece-square tables for positional evaluation
    /// Values are from White's perspective (flip for Black)
    /// </summary>
    public static class PieceSquareTables
    {
        // Pawn piece-square table
        // Middlegame: Safe advance on non-castled side
        // Endgame: Second rank and promotion focused
        private static readonly int[] PawnTableMiddlegame = {
             0,  0,  0,  0,  0,  0,  0,  0, // 8th rank (should never have pawns)
            50, 50, 50, 50, 50, 50, 50, 50, // 7th rank - close to promotion
            10, 10, 20, 30, 30, 20, 10, 10, // 6th rank - advanced pawns
             5,  5, 10, 25, 25, 10,  5,  5, // 5th rank - central control
             0,  0,  0, 20, 20,  0,  0,  0, // 4th rank - center pawns
             5, -5,-10,  0,  0,-10, -5,  5, // 3rd rank - avoid early moves
             5, 10, 10,-20,-20, 10, 10,  5, // 2nd rank - stay protected
             0,  0,  0,  0,  0,  0,  0,  0  // 1st rank (should never have pawns)
        };

        private static readonly int[] PawnTableEndgame = {
             0,  0,  0,  0,  0,  0,  0,  0, // 8th rank
            80, 80, 80, 80, 80, 80, 80, 80, // 7th rank - promotion imminent
            50, 50, 50, 50, 50, 50, 50, 50, // 6th rank - far advanced
            30, 30, 30, 30, 30, 30, 30, 30, // 5th rank
            20, 20, 20, 20, 20, 20, 20, 20, // 4th rank
            10, 10, 10, 10, 10, 10, 10, 10, // 3rd rank
             0,  0,  0,  0,  0,  0,  0,  0, // 2nd rank - king activity matters more
             0,  0,  0,  0,  0,  0,  0,  0  // 1st rank
        };

        // Knight piece-square table
        // Middlegame: Center focused
        // Endgame: Check focused (edge squares for checks)
        private static readonly int[] KnightTableMiddlegame = {
           -50,-40,-30,-30,-30,-30,-40,-50, // 8th rank - poor knight squares
           -40,-20,  0,  0,  0,  0,-20,-40, // 7th rank
           -30,  0, 10, 15, 15, 10,  0,-30, // 6th rank
           -30,  5, 15, 20, 20, 15,  5,-30, // 5th rank - excellent centralization
           -30,  0, 15, 20, 20, 15,  0,-30, // 4th rank
           -30,  5, 10, 15, 15, 10,  5,-30, // 3rd rank
           -40,-20,  0,  5,  5,  0,-20,-40, // 2nd rank
           -50,-40,-30,-30,-30,-30,-40,-50  // 1st rank - poor development
        };

        private static readonly int[] KnightTableEndgame = {
           -20,-10, -5, -5, -5, -5,-10,-20, // 8th rank - edge squares for checks
           -10,  0,  5,  5,  5,  5,  0,-10, // 7th rank
            -5,  5, 10, 10, 10, 10,  5, -5, // 6th rank
            -5,  5, 10, 15, 15, 10,  5, -5, // 5th rank - still centralized
            -5,  5, 10, 15, 15, 10,  5, -5, // 4th rank
            -5,  5, 10, 10, 10, 10,  5, -5, // 3rd rank
           -10,  0,  5,  5,  5,  5,  0,-10, // 2nd rank
           -20,-10, -5, -5, -5, -5,-10,-20  // 1st rank
        };

        // Bishop piece-square table
        // Middlegame: Long diagonal focused
        // Endgame: Check focused
        private static readonly int[] BishopTableMiddlegame = {
           -20,-10,-10,-10,-10,-10,-10,-20, // 8th rank
           -10,  0,  0,  0,  0,  0,  0,-10, // 7th rank
           -10,  0,  5, 10, 10,  5,  0,-10, // 6th rank
           -10,  5,  5, 10, 10,  5,  5,-10, // 5th rank
           -10,  0, 10, 10, 10, 10,  0,-10, // 4th rank - central control
           -10, 10, 10, 10, 10, 10, 10,-10, // 3rd rank - long diagonals
           -10,  5,  0,  0,  0,  0,  5,-10, // 2nd rank
           -20,-10,-10,-10,-10,-10,-10,-20  // 1st rank - avoid corners
        };

        private static readonly int[] BishopTableEndgame = {
           -15, -5, -5, -5, -5, -5, -5,-15, // 8th rank
            -5,  5,  5,  5,  5,  5,  5, -5, // 7th rank
            -5,  5, 10, 10, 10, 10,  5, -5, // 6th rank
            -5,  5, 10, 15, 15, 10,  5, -5, // 5th rank - active centralization
            -5,  5, 10, 15, 15, 10,  5, -5, // 4th rank
            -5,  5, 10, 10, 10, 10,  5, -5, // 3rd rank
            -5,  5,  5,  5,  5,  5,  5, -5, // 2nd rank
           -15, -5, -5, -5, -5, -5, -5,-15  // 1st rank
        };

        // Queen piece-square table
        // Middlegame: Safe piece attacks
        // Endgame: Check focused
        private static readonly int[] QueenTableMiddlegame = {
           -20,-10,-10, -5, -5,-10,-10,-20, // 8th rank
           -10,  0,  0,  0,  0,  0,  0,-10, // 7th rank
           -10,  0,  5,  5,  5,  5,  0,-10, // 6th rank
            -5,  0,  5,  5,  5,  5,  0, -5, // 5th rank
             0,  0,  5,  5,  5,  5,  0, -5, // 4th rank
           -10,  5,  5,  5,  5,  5,  0,-10, // 3rd rank
           -10,  0,  5,  0,  0,  0,  0,-10, // 2nd rank - avoid early development
           -20,-10,-10, -5, -5,-10,-10,-20  // 1st rank
        };

        private static readonly int[] QueenTableEndgame = {
           -10, -5, -5, -5, -5, -5, -5,-10, // 8th rank
            -5,  0,  5,  5,  5,  5,  0, -5, // 7th rank
            -5,  5, 10, 10, 10, 10,  5, -5, // 6th rank
            -5,  5, 10, 15, 15, 10,  5, -5, // 5th rank - active queen
            -5,  5, 10, 15, 15, 10,  5, -5, // 4th rank
            -5,  5, 10, 10, 10, 10,  5, -5, // 3rd rank
            -5,  0,  5,  5,  5,  5,  0, -5, // 2nd rank
           -10, -5, -5, -5, -5, -5, -5,-10  // 1st rank
        };

        // King middlegame table - focused on safety
        private static readonly int[] KingTableMiddlegame = {
           -30,-40,-40,-50,-50,-40,-40,-30, // 8th rank
           -30,-40,-40,-50,-50,-40,-40,-30, // 7th rank
           -30,-40,-40,-50,-50,-40,-40,-30, // 6th rank
           -30,-40,-40,-50,-50,-40,-40,-30, // 5th rank
           -20,-30,-30,-40,-40,-30,-30,-20, // 4th rank
           -10,-20,-20,-20,-20,-20,-20,-10, // 3rd rank
            20, 20,  0,  0,  0,  0, 20, 20, // 2nd rank - encouraged to stay
            20, 30, 10,  0,  0, 10, 30, 20  // 1st rank - castling positions
        };

        // King endgame table - focused on activity
        private static readonly int[] KingTableEndgame = {
           -50,-40,-30,-20,-20,-30,-40,-50, // 8th rank
           -30,-20,-10,  0,  0,-10,-20,-30, // 7th rank
           -30,-10, 20, 30, 30, 20,-10,-30, // 6th rank - active king
           -30,-10, 30, 40, 40, 30,-10,-30, // 5th rank - centralized
           -30,-10, 30, 40, 40, 30,-10,-30, // 4th rank
           -30,-10, 20, 30, 30, 20,-10,-30, // 3rd rank
           -30,-30,  0,  0,  0,  0,-30,-30, // 2nd rank
           -50,-30,-30,-30,-30,-30,-30,-50  // 1st rank
        };

        /// <summary>
        /// Get piece-square table value for a piece at a given square
        /// </summary>
        /// <param name="piece">The piece to evaluate</param>
        /// <param name="gamePhase">Game phase (0.0 = endgame, 1.0 = opening)</param>
        /// <returns>Positional value in centipawns</returns>
        public static int GetPieceSquareValue(Piece piece, double gamePhase)
        {
            if (piece.IsNull)
                return 0;

            int square = piece.Square.Index;
            
            // Flip square for black pieces (black sees board from opposite perspective)
            if (!piece.IsWhite)
            {
                square = 63 - square; // Flip vertically
            }

            int mgValue = GetMiddlegameValue(piece.PieceType, square);
            int egValue = GetEndgameValue(piece.PieceType, square);

            // Interpolate between middlegame and endgame values
            int value = (int)(mgValue * gamePhase + egValue * (1.0 - gamePhase));
            
            // Return from perspective of piece color
            return piece.IsWhite ? value : -value;
        }

        /// <summary>
        /// Get total piece-square table evaluation for the position
        /// </summary>
        /// <param name="board">Current board position</param>
        /// <param name="gamePhase">Game phase (0.0 = endgame, 1.0 = opening)</param>
        /// <returns>Total PST evaluation from white's perspective</returns>
        public static int EvaluatePosition(Board board, double gamePhase)
        {
            int totalValue = 0;

            for (int square = 0; square < 64; square++)
            {
                var piece = board.GetPiece(new Square(square));
                if (!piece.IsNull)
                {
                    totalValue += GetPieceSquareValue(piece, gamePhase);
                }
            }

            return totalValue;
        }

        private static int GetMiddlegameValue(PieceType pieceType, int square)
        {
            return pieceType switch
            {
                PieceType.Pawn => PawnTableMiddlegame[square],
                PieceType.Knight => KnightTableMiddlegame[square],
                PieceType.Bishop => BishopTableMiddlegame[square],
                PieceType.Rook => 0, // No rook PST yet (to be implemented later)
                PieceType.Queen => QueenTableMiddlegame[square],
                PieceType.King => KingTableMiddlegame[square],
                _ => 0
            };
        }

        private static int GetEndgameValue(PieceType pieceType, int square)
        {
            return pieceType switch
            {
                PieceType.Pawn => PawnTableEndgame[square],
                PieceType.Knight => KnightTableEndgame[square],
                PieceType.Bishop => BishopTableEndgame[square],
                PieceType.Rook => 0, // No rook PST yet (to be implemented later)
                PieceType.Queen => QueenTableEndgame[square],
                PieceType.King => KingTableEndgame[square],
                _ => 0
            };
        }
    }
}
