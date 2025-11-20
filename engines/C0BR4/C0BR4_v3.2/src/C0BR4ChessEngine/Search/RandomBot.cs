using C0BR4ChessEngine.Core;

namespace C0BR4ChessEngine.Search
{
    /// <summary>
    /// Simple random bot implementation - our starting point
    /// </summary>
    public class RandomBot : IChessBot
    {
        private readonly Random random = new();

        public Move Think(Board board, TimeSpan timeLimit)
        {
            var moves = board.GetLegalMoves();
            if (moves.Length == 0)
                return Move.NullMove;
            
            return moves[random.Next(moves.Length)];
        }
    }
}
