using C0BR4ChessEngine.Core;

namespace C0BR4ChessEngine.Evaluation
{
    /// <summary>
    /// Detects and evaluates the current game phase for strategic decision making
    /// </summary>
    public static class GamePhase
    {
        // Standard piece values for phase calculation
        private const int PawnPhaseValue = 0;
        private const int KnightPhaseValue = 1;
        private const int BishopPhaseValue = 1;
        private const int RookPhaseValue = 2;
        private const int QueenPhaseValue = 4;

        // Total phase value for starting position (not counting pawns and kings)
        private const int TotalPhaseValue = 
            (KnightPhaseValue + BishopPhaseValue + RookPhaseValue + QueenPhaseValue) * 2; // 16

        /// <summary>
        /// Calculate game phase as a value between 0.0 (endgame) and 1.0 (opening)
        /// </summary>
        /// <param name="board">Current board position</param>
        /// <returns>Phase value: 1.0 = opening, 0.5 = middlegame, 0.0 = endgame</returns>
        public static double CalculatePhase(Board board)
        {
            int currentPhaseValue = 0;

            // Count phase values for all pieces on the board
            for (int square = 0; square < 64; square++)
            {
                var piece = board.GetPiece(new Square(square));
                if (!piece.IsNull)
                {
                    currentPhaseValue += GetPiecePhaseValue(piece.PieceType);
                }
            }

            // Convert to 0.0-1.0 scale
            double phase = (double)currentPhaseValue / TotalPhaseValue;
            
            // Clamp to valid range
            return Math.Max(0.0, Math.Min(1.0, phase));
        }

        /// <summary>
        /// Determine if position is in endgame (14 or fewer pieces total)
        /// </summary>
        /// <param name="board">Current board position</param>
        /// <returns>True if in endgame phase</returns>
        public static bool IsEndgame(Board board)
        {
            int pieceCount = CountTotalPieces(board);
            return pieceCount <= 14;
        }

        /// <summary>
        /// Determine if position is in opening (most pieces still on board)
        /// </summary>
        /// <param name="board">Current board position</param>
        /// <returns>True if in opening phase</returns>
        public static bool IsOpening(Board board)
        {
            double phase = CalculatePhase(board);
            return phase > 0.7;
        }

        /// <summary>
        /// Determine if position is in middlegame
        /// </summary>
        /// <param name="board">Current board position</param>
        /// <returns>True if in middlegame phase</returns>
        public static bool IsMiddlegame(Board board)
        {
            double phase = CalculatePhase(board);
            return phase >= 0.3 && phase <= 0.7;
        }

        /// <summary>
        /// Get descriptive name for current game phase
        /// </summary>
        /// <param name="board">Current board position</param>
        /// <returns>Phase name as string</returns>
        public static string GetPhaseName(Board board)
        {
            double phase = CalculatePhase(board);
            
            if (phase > 0.7)
                return "Opening";
            else if (phase > 0.3)
                return "Middlegame";
            else
                return "Endgame";
        }

        /// <summary>
        /// Calculate material imbalance factor for time management
        /// When ahead in material, spend more time to convert advantage
        /// When behind in material, play faster to create complications
        /// </summary>
        /// <param name="board">Current board position</param>
        /// <returns>Time multiplier: >1.0 when ahead, <1.0 when behind</returns>
        public static double GetMaterialTimeMultiplier(Board board)
        {
            int materialBalance = CalculateMaterialBalance(board);
            
            // Convert centipawn advantage to time multiplier
            // +200cp = 1.2x time, -200cp = 0.8x time
            double advantage = materialBalance / 200.0;
            double multiplier = 1.0 + advantage * 0.2;
            
            // Clamp to reasonable range
            return Math.Max(0.7, Math.Min(1.3, multiplier));
        }

        /// <summary>
        /// Count total pieces on the board
        /// </summary>
        private static int CountTotalPieces(Board board)
        {
            int count = 0;
            for (int square = 0; square < 64; square++)
            {
                var piece = board.GetPiece(new Square(square));
                if (!piece.IsNull)
                    count++;
            }
            return count;
        }

        /// <summary>
        /// Get phase value for a piece type
        /// </summary>
        private static int GetPiecePhaseValue(PieceType pieceType)
        {
            return pieceType switch
            {
                PieceType.Pawn => PawnPhaseValue,
                PieceType.Knight => KnightPhaseValue,
                PieceType.Bishop => BishopPhaseValue,
                PieceType.Rook => RookPhaseValue,
                PieceType.Queen => QueenPhaseValue,
                PieceType.King => 0, // King doesn't affect phase
                _ => 0
            };
        }

        /// <summary>
        /// Calculate material balance from current player's perspective
        /// </summary>
        private static int CalculateMaterialBalance(Board board)
        {
            int whiteValue = 0;
            int blackValue = 0;

            for (int square = 0; square < 64; square++)
            {
                var piece = board.GetPiece(new Square(square));
                if (!piece.IsNull)
                {
                    int value = GetPieceValue(piece.PieceType);
                    if (piece.IsWhite)
                        whiteValue += value;
                    else
                        blackValue += value;
                }
            }

            // Return balance from current player's perspective
            if (board.IsWhiteToMove)
                return whiteValue - blackValue;
            else
                return blackValue - whiteValue;
        }

        /// <summary>
        /// Get standard material value for a piece
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
                PieceType.King => 0, // King has no material value
                _ => 0
            };
        }
    }
}
