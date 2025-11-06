using System;
using System.IO;
using System.Linq;
using C0BR4ChessEngine.Core;

namespace C0BR4ChessEngine.Testing
{
    public static class IllegalMoveDebugger
    {
        private static readonly string LogFile = "illegal_moves.log";
        
        public static void AnalyzePosition(Board board)
        {
            Console.WriteLine("=== ILLEGAL MOVE ANALYSIS ===");
            
            // Show current position info
            Console.WriteLine($"White to move: {board.IsWhiteToMove}");
            
            // Check what piece is on c1
            var c1Piece = board.GetPiece(new Square(2)); // c1 = index 2
            Console.WriteLine($"Piece on c1: {c1Piece}");
            
            // Check what piece is on a8
            var a8Piece = board.GetPiece(new Square(56)); // a8 = index 56
            Console.WriteLine($"Piece on a8: {a8Piece}");
            
            // Check diagonal path from c1 to a8
            Console.WriteLine("Diagonal path from c1 to a8:");
            int[] diagonalSquares = { 2, 11, 20, 29, 38, 47, 56 }; // c1, d2, e3, f4, g5, h6, a8
            
            foreach (int square in diagonalSquares)
            {
                var piece = board.GetPiece(new Square(square));
                char file = (char)('a' + (square % 8));
                int rank = (square / 8) + 1;
                Console.WriteLine($"  {file}{rank} (index {square}): {piece}");
            }
            
            // Generate legal moves for bishop on c1 if it exists
            if (!c1Piece.IsNull && c1Piece.PieceType == PieceType.Bishop)
            {
                Console.WriteLine("\nGenerating moves for bishop on c1:");
                var moveGen = new MoveGenerator(board);
                var allMoves = board.GetLegalMoves();
                
                foreach (var move in allMoves)
                {
                    if (move.StartSquare.Index == 2) // c1
                    {
                        char startFile = (char)('a' + (move.StartSquare.Index % 8));
                        int startRank = (move.StartSquare.Index / 8) + 1;
                        char endFile = (char)('a' + (move.TargetSquare.Index % 8));
                        int endRank = (move.TargetSquare.Index / 8) + 1;
                        Console.WriteLine($"  {startFile}{startRank}{endFile}{endRank} (from {move.StartSquare.Index} to {move.TargetSquare.Index})");
                    }
                }
            }
            
            Console.WriteLine("=== END ANALYSIS ===");
        }
        
        public static void LogIllegalMoveAttempt(Board board, Move move, string reason)
        {
            var timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
            var fenPosition = board.GetFEN();
            var logMessage = $"[{timestamp}] ILLEGAL MOVE VALIDATION FAILED: {move} - Reason: {reason} - FEN: {fenPosition}";
            
            Console.WriteLine(logMessage);
            LogToFile(logMessage);
        }
        
        public static void LogUnknownMoveAttempt(Board board, string moveString)
        {
            var timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
            var fenPosition = board.GetFEN();
            var legalMoves = board.GetLegalMoves();
            var legalMovesStr = string.Join(", ", legalMoves);
            
            var logMessage = $"[{timestamp}] UNKNOWN MOVE ATTEMPT: {moveString} - FEN: {fenPosition} - Legal moves: {legalMovesStr}";
            
            Console.WriteLine(logMessage);
            LogToFile(logMessage);
        }
        
        public static void LogMoveException(Board board, string moveString, Exception ex)
        {
            var timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
            var fenPosition = board.GetFEN();
            var logMessage = $"[{timestamp}] MOVE EXCEPTION: {moveString} - Exception: {ex.Message} - FEN: {fenPosition} - Stack: {ex.StackTrace}";
            
            Console.WriteLine(logMessage);
            LogToFile(logMessage);
        }
        
        public static void LogBoardStateAnalysis(Board board, string context = "")
        {
            var timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
            var fenPosition = board.GetFEN();
            var legalMoves = board.GetLegalMoves();
            var moveCount = legalMoves.Length;
            
            var logMessage = $"[{timestamp}] BOARD STATE ANALYSIS {context}: FEN: {fenPosition} - Legal moves: {moveCount} - To move: {(board.IsWhiteToMove ? "White" : "Black")}";
            
            Console.WriteLine(logMessage);
            LogToFile(logMessage);
            
            // Log first few legal moves for context
            if (moveCount > 0)
            {
                var moveStrings = new string[Math.Min(10, moveCount)];
                for (int i = 0; i < moveStrings.Length; i++)
                {
                    moveStrings[i] = legalMoves[i].ToString();
                }
                var firstMoves = string.Join(", ", moveStrings);
                var movesMessage = $"[{timestamp}] First 10 legal moves: {firstMoves}";
                Console.WriteLine(movesMessage);
                LogToFile(movesMessage);
            }
        }
        
        private static void LogToFile(string message)
        {
            try
            {
                File.AppendAllText(LogFile, message + Environment.NewLine);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to write to log file: {ex.Message}");
            }
        }
        
        public static void ClearLogFile()
        {
            try
            {
                if (File.Exists(LogFile))
                {
                    File.Delete(LogFile);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to clear log file: {ex.Message}");
            }
        }
    }
}
