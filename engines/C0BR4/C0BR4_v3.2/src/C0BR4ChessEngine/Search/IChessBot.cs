using C0BR4ChessEngine.Core;

namespace C0BR4ChessEngine.Search
{
    public interface IChessBot
    {
        Move Think(Board board, TimeSpan timeLimit);
    }
}
