using System;
using System.Collections.Generic;
using C0BR4ChessEngine.Core;
using C0BR4ChessEngine.Evaluation;

namespace C0BR4ChessEngine.Search
{
    /// <summary>
    /// Alpha-beta search with move ordering and quiescence search
    /// Quiescence search helps avoid the horizon effect by continuing to search
    /// in tactical positions (captures, checks) until a "quiet" position is reached
    /// </summary>
    public class QuiescenceSearchBot : IChessBot
    {
        private readonly SimpleEvaluator evaluator = new();
        private long nodesSearched = 0;
        private long quiescenceNodes = 0;
        private int searchDepth = 4; // Default search depth

        public Move Think(Board board, TimeSpan timeLimit)
        {
            nodesSearched = 0;
            quiescenceNodes = 0;
            var stopwatch = System.Diagnostics.Stopwatch.StartNew();
            
            Move bestMove = SearchBestMove(board, searchDepth);
            
            stopwatch.Stop();
            
            // Report search statistics including quiescence nodes
            Console.WriteLine($"info depth {searchDepth} nodes {nodesSearched} qnodes {quiescenceNodes} time {stopwatch.ElapsedMilliseconds} nps {(long)(nodesSearched / Math.Max(stopwatch.Elapsed.TotalSeconds, 0.001))}");
            
            return bestMove;
        }

        private Move SearchBestMove(Board board, int depth)
        {
            var moves = board.GetLegalMoves();
            if (moves.Length == 0)
                return Move.NullMove;

            // Order moves for better alpha-beta pruning
            moves = MoveOrdering.OrderMoves(board, moves);

            Move bestMove = moves[0];
            int bestScore = -50000; // Start with very low score

            foreach (var move in moves)
            {
                board.MakeMove(move);
                int score = -AlphaBeta(board, depth - 1, -50000, -bestScore);
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
        /// Alpha-beta search with quiescence search at leaf nodes
        /// </summary>
        private int AlphaBeta(Board board, int depth, int alpha, int beta)
        {
            nodesSearched++;

            // Base case: enter quiescence search instead of immediate evaluation
            if (depth == 0)
            {
                return Quiescence(board, alpha, beta);
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

            // Order moves for better pruning
            moves = MoveOrdering.OrderMoves(board, moves);

            int maxScore = alpha; // Start with current alpha

            // Try each move (now in optimal order)
            foreach (var move in moves)
            {
                board.MakeMove(move);
                int score = -AlphaBeta(board, depth - 1, -beta, -maxScore);
                board.UnmakeMove();

                // Update best score found
                if (score > maxScore)
                {
                    maxScore = score;
                }

                // Alpha-beta cutoff
                if (maxScore >= beta)
                {
                    return beta; // Fail-high (beta cutoff)
                }
            }

            return maxScore;
        }

        /// <summary>
        /// Quiescence search - search only captures and checks until position is "quiet"
        /// This helps avoid the horizon effect where tactical sequences are cut off
        /// </summary>
        private int Quiescence(Board board, int alpha, int beta)
        {
            quiescenceNodes++;

            // Stand-pat evaluation - we can always choose to not make any capture
            int standPat = evaluator.Evaluate(board);
            
            // If we're already better than beta, we can cutoff immediately
            if (standPat >= beta)
                return beta;
            
            // Update alpha if our static evaluation is better
            if (standPat > alpha)
                alpha = standPat;

            // Generate and search tactical moves (captures and checks)
            var tacticalMoves = GetTacticalMoves(board);
            
            // If no tactical moves, return the static evaluation
            if (tacticalMoves.Length == 0)
                return standPat;

            // Order tactical moves (best captures first)
            tacticalMoves = MoveOrdering.OrderMoves(board, tacticalMoves);

            foreach (var move in tacticalMoves)
            {
                board.MakeMove(move);
                int score = -Quiescence(board, -beta, -alpha);
                board.UnmakeMove();

                if (score >= beta)
                    return beta; // Beta cutoff

                if (score > alpha)
                    alpha = score;
            }

            return alpha;
        }

        /// <summary>
        /// Get only tactical moves (captures and checks) for quiescence search
        /// </summary>
        private Move[] GetTacticalMoves(Board board)
        {
            var allMoves = board.GetLegalMoves();
            var tacticalMoves = new List<Move>();

            foreach (var move in allMoves)
            {
                // Include captures
                var targetPiece = board.GetPiece(move.TargetSquare);
                if (targetPiece.PieceType != PieceType.None)
                {
                    tacticalMoves.Add(move);
                    continue;
                }

                // Include promotions (usually tactical)
                if (move.PromotionPieceType != PieceType.None)
                {
                    tacticalMoves.Add(move);
                    continue;
                }

                // Include checks (optional - can make quiescence search much slower)
                // Uncomment the following lines to include checking moves:
                /*
                board.MakeMove(move);
                bool givesCheck = board.IsInCheck();
                board.UnmakeMove();
                
                if (givesCheck)
                {
                    tacticalMoves.Add(move);
                }
                */
            }

            return tacticalMoves.ToArray();
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
        
        /// <summary>
        /// Get quiescence search statistics
        /// </summary>
        public long GetQuiescenceNodes() => quiescenceNodes;
    }
}
