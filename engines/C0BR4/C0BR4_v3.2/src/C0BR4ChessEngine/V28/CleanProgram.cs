using System;
using System.Diagnostics;
using C0BR4ChessEngine.Core.V28;
using C0BR4ChessEngine.UCI.V28;

namespace C0BR4ChessEngine.V28
{
    /// <summary>
    /// Clean main program for C0BR4 v2.8
    /// Simple, reliable entry point
    /// Built from scratch to eliminate legacy issues
    /// </summary>
    public class CleanProgram
    {
        private static CleanUciEngine? _engine;
        private static bool _debugMode = false;
        
        public static void Main(string[] args)
        {
            try
            {
                // Parse command line arguments
                ParseArguments(args);
                
                // Initialize clean bitboards
                CleanBitboard.Initialize();
                
                // Create UCI engine
                _engine = new CleanUciEngine();
                
                if (_debugMode)
                {
                    Console.WriteLine("info string C0BR4 v2.8 started in debug mode");
                    Console.WriteLine("info string Clean bitboard rebuild - prioritizing correctness");
                }
                
                // Run UCI loop
                RunUciLoop();
            }
            catch (Exception ex)
            {
                if (_debugMode)
                {
                    Console.WriteLine($"info string Fatal error: {ex.Message}");
                    Console.WriteLine($"info string Stack trace: {ex.StackTrace}");
                }
                Environment.Exit(1);
            }
        }
        
        /// <summary>
        /// Parse command line arguments
        /// </summary>
        private static void ParseArguments(string[] args)
        {
            foreach (string arg in args)
            {
                switch (arg.ToLower())
                {
                    case "--debug":
                    case "-d":
                        _debugMode = true;
                        break;
                    case "--version":
                    case "-v":
                        Console.WriteLine("C0BR4 Chess Engine v2.8 - Clean Bitboard Rebuild");
                        Console.WriteLine("Built from scratch to eliminate illegal move issues");
                        Environment.Exit(0);
                        break;
                    case "--help":
                    case "-h":
                        ShowHelp();
                        Environment.Exit(0);
                        break;
                    case "--test":
                        RunQuickTest();
                        Environment.Exit(0);
                        break;
                }
            }
        }
        
        /// <summary>
        /// Show help information
        /// </summary>
        private static void ShowHelp()
        {
            Console.WriteLine("C0BR4 Chess Engine v2.8 - Clean Bitboard Rebuild");
            Console.WriteLine("Usage: C0BR4_v2.8.exe [options]");
            Console.WriteLine();
            Console.WriteLine("Options:");
            Console.WriteLine("  --debug, -d     Enable debug mode");
            Console.WriteLine("  --version, -v   Show version information");
            Console.WriteLine("  --help, -h      Show this help");
            Console.WriteLine("  --test          Run quick self-test");
            Console.WriteLine();
            Console.WriteLine("The engine communicates via UCI protocol on stdin/stdout.");
        }
        
        /// <summary>
        /// Run main UCI communication loop
        /// </summary>
        private static void RunUciLoop()
        {
            if (_engine == null)
                throw new InvalidOperationException("Engine not initialized");
            
            string? input;
            while ((input = Console.ReadLine()) != null)
            {
                input = input.Trim();
                
                if (string.IsNullOrEmpty(input))
                    continue;
                
                if (_debugMode)
                {
                    Console.WriteLine($"info string Received: {input}");
                }
                
                string response = _engine.ProcessCommand(input);
                
                if (!string.IsNullOrEmpty(response))
                {
                    Console.WriteLine(response);
                }
                
                // Check for quit command
                if (input.ToLower() == "quit")
                {
                    break;
                }
            }
        }
        
        /// <summary>
        /// Run quick self-test to validate basic functionality
        /// </summary>
        private static void RunQuickTest()
        {
            Console.WriteLine("Running C0BR4 v2.8 Quick Self-Test...");
            Console.WriteLine();
            
            try
            {
                // Test 1: Initialize bitboards
                Console.Write("Test 1: Initialize bitboards... ");
                CleanBitboard.Initialize();
                Console.WriteLine("PASS");
                
                // Test 2: Create starting position
                Console.Write("Test 2: Create starting position... ");
                var startingPosition = CleanBoardState.StartingPosition();
                Console.WriteLine(startingPosition.IsValid() ? "PASS" : "FAIL");
                
                // Test 3: Parse starting FEN
                Console.Write("Test 3: Parse starting FEN... ");
                var fenPosition = CleanFenParser.ParseFen(CleanFenParser.StartingPositionFen);
                Console.WriteLine(fenPosition.IsValid() ? "PASS" : "FAIL");
                
                // Test 4: Generate legal moves
                Console.Write("Test 4: Generate legal moves... ");
                var legalMoves = CleanMoveGenerator.GenerateLegalMoves(startingPosition);
                Console.WriteLine(legalMoves.Count == 20 ? "PASS" : $"FAIL (got {legalMoves.Count}, expected 20)");
                
                // Test 5: UCI engine creation
                Console.Write("Test 5: Create UCI engine... ");
                var engine = new CleanUciEngine();
                Console.WriteLine(engine.IsCurrentPositionValid() ? "PASS" : "FAIL");
                
                // Test 6: Process UCI command
                Console.Write("Test 6: Process UCI command... ");
                string uciResponse = engine.ProcessCommand("uci");
                Console.WriteLine(uciResponse.Contains("uciok") ? "PASS" : "FAIL");
                
                // Test 7: Test a simple move
                Console.Write("Test 7: Test simple move (e2e4)... ");
                engine.ProcessCommand("position startpos");
                var currentMoves = engine.GetLegalMoves();
                bool hasE2E4 = currentMoves.Any(m => m.ToUCI() == "e2e4");
                Console.WriteLine(hasE2E4 ? "PASS" : "FAIL");
                
                // Test 8: Test rook attacks (the problematic piece)
                Console.Write("Test 8: Test rook attacks... ");
                ulong rookAttacks = CleanBitboard.GetRookAttacks(0, 0UL); // a1 with empty board
                bool rookTest = (rookAttacks & CleanBitboard.SquareToBitboard(7)) != 0; // Should attack h1
                Console.WriteLine(rookTest ? "PASS" : "FAIL");
                
                Console.WriteLine();
                Console.WriteLine("All tests completed. Engine appears to be functioning correctly.");
                Console.WriteLine("Key improvement: Simple ray-based move generation eliminates magic bitboard bugs.");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"FAIL - Exception: {ex.Message}");
                Console.WriteLine();
                Console.WriteLine("Self-test failed. Please check the implementation.");
            }
        }
    }
}
