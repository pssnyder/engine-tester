using C0BR4ChessEngine.Core;

namespace C0BR4ChessEngine.Evaluation
{
    /// <summary>
    /// Enhanced position evaluation with material counting, piece-square tables, 
    /// game phase detection, and advanced evaluation features for improved play
    /// </summary>
    public class SimpleEvaluator
    {
        // Material values in centipawns
        private static readonly int[] PieceValues = { 0, 100, 300, 300, 500, 900, 0 }; // None, Pawn, Knight, Bishop, Rook, Queen, King

        /// <summary>
        /// Evaluate the position from the perspective of the side to move
        /// Positive = good for side to move, Negative = bad for side to move
        /// </summary>
        public int Evaluate(Board board)
        {
            int evaluation = 0;
            
            // Calculate game phase for PST interpolation and feature weighting
            double gamePhase = GamePhase.CalculatePhase(board);
            
            // Core evaluation components
            evaluation += EvaluateMaterial(board);
            evaluation += PieceSquareTables.EvaluatePosition(board, gamePhase);
            
            // Advanced evaluation features
            evaluation += RookCoordination.Evaluate(board, gamePhase);
            evaluation += KingSafety.Evaluate(board, gamePhase);
            evaluation += KingEndgame.Evaluate(board, gamePhase);
            evaluation += CastlingIncentive.Evaluate(board, gamePhase);
            evaluation += CastlingRights.Evaluate(board, gamePhase);
            
            // Return from perspective of side to move
            return board.IsWhiteToMove ? evaluation : -evaluation;
        }

        /// <summary>
        /// Calculate material difference from white's perspective
        /// </summary>
        private int EvaluateMaterial(Board board)
        {
            int whiteValue = 0;
            int blackValue = 0;
            
            for (int square = 0; square < 64; square++)
            {
                var piece = board.GetPiece(new Square(square));
                if (piece.IsNull)
                    continue;
                
                int value = PieceValues[(int)piece.PieceType];
                if (piece.IsWhite)
                    whiteValue += value;
                else
                    blackValue += value;
            }
            
            return whiteValue - blackValue;
        }
    }
}
