using System;
using System.Diagnostics;
using C0BR4ChessEngine.Core;

namespace C0BR4ChessEngine.Testing
{
    /// <summary>
    /// Performance benchmarking for chess engine components
    /// </summary>
    public static class PerformanceBenchmark
    {
        /// <summary>
        /// Benchmark move generation performance
        /// </summary>
        public static void BenchmarkMoveGeneration(int iterations = 10000)
        {
            Console.WriteLine("=== Move Generation Benchmark ===");
            
            // Test positions
            var testPositions = new[]
            {
                ("Starting Position", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
                ("Middle Game", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1"),
                ("Endgame", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1")
            };

            foreach (var (name, fen) in testPositions)
            {
                BenchmarkPosition(name, fen, iterations);
                Console.WriteLine();
            }
        }

        private static void BenchmarkPosition(string positionName, string fen, int iterations)
        {
            Console.WriteLine($"Position: {positionName}");
            Console.WriteLine($"FEN: {fen}");
            
            var board = new Board(fen);
            
            // Warmup
            for (int i = 0; i < 100; i++)
            {
                board.GetPseudoLegalMoves();
            }

            // Benchmark pseudo-legal move generation
            var stopwatch = Stopwatch.StartNew();
            int totalMoves = 0;
            
            for (int i = 0; i < iterations; i++)
            {
                var moves = board.GetPseudoLegalMoves();
                totalMoves += moves.Length;
            }
            
            stopwatch.Stop();
            
            double movesPerSecond = (totalMoves / stopwatch.Elapsed.TotalSeconds);
            double avgMoves = (double)totalMoves / iterations;
            
            Console.WriteLine($"Pseudo-legal moves: {avgMoves:F1} average per position");
            Console.WriteLine($"Time: {stopwatch.ElapsedMilliseconds}ms for {iterations} iterations");
            Console.WriteLine($"Rate: {movesPerSecond:F0} moves/sec");
            Console.WriteLine($"Performance: {iterations / stopwatch.Elapsed.TotalSeconds:F0} positions/sec");
        }

        /// <summary>
        /// Simple perft test (performance test) for move generation verification
        /// </summary>
        public static long Perft(Board board, int depth)
        {
            if (depth == 0) return 1;
            
            var moves = board.GetPseudoLegalMoves();
            long nodes = 0;
            
            foreach (var move in moves)
            {
                // TODO: Implement make/unmake move for accurate perft
                // For now, just count leaf nodes
                if (depth == 1)
                {
                    nodes++;
                }
                else
                {
                    // Can't go deeper without make/unmake - placeholder
                    nodes++;
                }
            }
            
            return nodes;
        }

        /// <summary>
        /// Run perft tests for known positions
        /// </summary>
        public static void RunPerftTests()
        {
            Console.WriteLine("=== Perft Tests ===");
            
            var board = new Board(); // Starting position
            
            for (int depth = 1; depth <= 3; depth++)
            {
                var stopwatch = Stopwatch.StartNew();
                long nodes = Perft(board, depth);
                stopwatch.Stop();
                
                Console.WriteLine($"Depth {depth}: {nodes} nodes in {stopwatch.ElapsedMilliseconds}ms");
            }
            
            // Expected results for starting position:
            // Depth 1: 20 nodes
            // Depth 2: 400 nodes  
            // Depth 3: 8902 nodes (when make/unmake is implemented)
            Console.WriteLine("\nExpected results for starting position:");
            Console.WriteLine("Depth 1: 20 nodes");
            Console.WriteLine("Depth 2: 400 nodes");
            Console.WriteLine("Depth 3: 8902 nodes");
        }
    }
}
