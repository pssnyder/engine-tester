using System;
using C0BR4ChessEngine.Core;
using C0BR4ChessEngine.Evaluation;

namespace C0BR4ChessEngine.Search
{
    /// <summary>
    /// Simple negamax search engine with evaluation
    /// This will be expanded with alpha-beta pruning and move ordering
    /// </summary>
    public class SimpleSearchBot : IChessBot
    {
        private readonly SimpleEvaluator evaluator = new();
        private long nodesSearched = 0;
        private int searchDepth = 4; // Default search depth

        public Move Think(Board board, TimeSpan timeLimit)
        {
            nodesSearched = 0;
            var stopwatch = System.Diagnostics.Stopwatch.StartNew();
            
            Move bestMove = SearchBestMove(board, searchDepth);
            
            stopwatch.Stop();
            
            // Report search statistics
            Console.WriteLine($"info depth {searchDepth} nodes {nodesSearched} time {stopwatch.ElapsedMilliseconds} nps {(long)(nodesSearched / Math.Max(stopwatch.Elapsed.TotalSeconds, 0.001))}");
            
            return bestMove;
        }

        private Move SearchBestMove(Board board, int depth)
        {
            var moves = board.GetLegalMoves();
            if (moves.Length == 0)
                return Move.NullMove;

            Move bestMove = moves[0];
            int bestScore = int.MinValue;

            foreach (var move in moves)
            {
                board.MakeMove(move);
                int score = -Negamax(board, depth - 1);
                board.UnmakeMove();

                if (score > bestScore)
                {
                    bestScore = score;
                    bestMove = move;
                }
            }

            Console.WriteLine($"info score cp {bestScore} pv {bestMove}");
            return bestMove;
        }

        /// <summary>
        /// Negamax search algorithm
        /// Returns the evaluation from the perspective of the side to move
        /// </summary>
        private int Negamax(Board board, int depth)
        {
            nodesSearched++;

            // Base case: evaluate position
            if (depth == 0)
            {
                return evaluator.Evaluate(board);
            }

            var moves = board.GetLegalMoves();
            
            // Check for terminal positions
            if (moves.Length == 0)
            {
                if (board.IsInCheck())
                {
                    // Checkmate - return very negative score, adjusted for depth to prefer quicker mates
                    return -30000 + (searchDepth - depth);
                }
                else
                {
                    // Stalemate
                    return 0;
                }
            }

            int maxScore = int.MinValue;

            foreach (var move in moves)
            {
                board.MakeMove(move);
                int score = -Negamax(board, depth - 1);
                board.UnmakeMove();

                if (score > maxScore)
                {
                    maxScore = score;
                }
            }

            return maxScore;
        }

        /// <summary>
        /// Set the search depth for the engine
        /// </summary>
        public void SetDepth(int depth)
        {
            searchDepth = Math.Max(1, Math.Min(depth, 10)); // Limit between 1 and 10
        }

        /// <summary>
        /// Get current search statistics
        /// </summary>
        public long GetNodesSearched() => nodesSearched;
    }
}
