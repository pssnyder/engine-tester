using C0BR4ChessEngine.Core;
using System.Text;

namespace C0BR4ChessEngine.Opening
{
    /// <summary>
    /// Minimal opening book with embedded move sequences for key openings
    /// Covers London System, Vienna Gambit, Caro-Kann, and Dutch Defense
    /// </summary>
    public static class OpeningBook
    {
        // Opening move sequences - each array represents a line of moves
        // Format: [move1, move2, move3, ...] in algebraic notation
        
        #region London System (White with d4)
        private static readonly string[][] LondonSystemLines = new string[][]
        {
            // Main London System lines
            new[] { "d4", "Nf3", "Bf4", "e3", "Bd3" },
            new[] { "d4", "Nf3", "Bf4", "e3", "c3" },
            new[] { "d4", "Bf4", "Nf3", "e3", "Bd3" },
            new[] { "d4", "Bf4", "e3", "Nf3", "Bd3" },
            
            // London vs various black setups
            new[] { "d4", "Nf3", "Bf4", "e3", "Bd3", "Nbd2" }, // vs ...d5
            new[] { "d4", "Nf3", "Bf4", "e3", "Bd3", "h3" },   // vs ...Bg4
        };
        #endregion

        #region Vienna System (Fixed Lines - Less Aggressive)
        private static readonly string[][] ViennaSystemLines = new string[][]
        {
            // Solid Vienna Game (non-gambit) - MUCH SAFER
            new[] { "e4", "Nc3", "Nf3", "Bc4" },      // Vienna Game proper
            new[] { "e4", "Nc3", "Bc4", "Nf3" },      // Bishop first development
            new[] { "e4", "Nc3", "Nf3", "Bb5" },      // Vienna with Bb5
            new[] { "e4", "Nc3", "f4", "Nf3", "Bb5" }, // Vienna Gambit only if absolutely safe
            
            // Safe responses to various Black setups
            new[] { "e4", "Nc3", "Nf3", "Bc4", "d3" },    // vs ...Bc5
            new[] { "e4", "Nc3", "Bb5", "Nf3", "O-O" },   // vs ...Nc6 
            new[] { "e4", "Nc3", "Nf3", "d4" },           // Central control
        };
        #endregion

        #region Caro-Kann Defense (Black vs e4)
        private static readonly string[][] CaroKannLines = new string[][]
        {
            // Main line Caro-Kann
            new[] { "c6", "d5", "Nc6", "Bg4" },
            new[] { "c6", "d5", "Nc6", "e6" },
            new[] { "c6", "d5", "Nc6", "dxe4", "Nxe4" },
            
            // Advance variation response
            new[] { "c6", "d5", "c5", "e6" },
            new[] { "c6", "d5", "c5", "Nc6" },
            
            // Exchange variation
            new[] { "c6", "d5", "cxd5", "Nc6" },
        };
        #endregion

        #region Dutch Defense (Black vs d4)
        private static readonly string[][] DutchDefenseLines = new string[][]
        {
            // Classical Dutch
            new[] { "f5", "Nf6", "e6", "Be7", "O-O" },
            new[] { "f5", "Nf6", "e6", "d6", "Be7" },
            
            // Leningrad Dutch
            new[] { "f5", "Nf6", "g6", "Bg7", "O-O" },
            new[] { "f5", "g6", "Bg7", "Nf6", "O-O" },
            
            // Stonewall Dutch
            new[] { "f5", "e6", "d5", "Bd6", "Nf6" },
        };
        #endregion

        #region Queen's Pawn Game Responses (Coverage Gap Fix)
        private static readonly string[][] QueensPawnGameLines = new string[][]
        {
            // Anti-Torre Defense responses (70.8% accuracy issue)
            new[] { "d5", "Nf6", "e6", "c5" },        // Classical Anti-Torre
            new[] { "d5", "Nf6", "e6", "Ne4" },       // Active Anti-Torre
            new[] { "d5", "Nf6", "c5", "e6" },        // Counter-attacking setup
            
            // Queen's Gambit Declined responses
            new[] { "d5", "e6", "Nf6", "Be7" },       // Classical QGD
            new[] { "d5", "e6", "c6", "Nf6" },        // Solid development
            
            // Semi-Slav responses
            new[] { "d5", "c6", "e6", "Nf6" },        // Semi-Slav setup
            new[] { "d5", "c6", "Nf6", "e6" },        // Flexible order
        };
        #endregion

        #region Sicilian Defense Responses (Coverage Gap Fix)
        private static readonly string[][] SicilianDefenseLines = new string[][]
        {
            // Open Sicilian responses (when Black plays 1...c5)
            new[] { "Nf3", "d6", "d4", "cxd4", "Nxd4" },    // Open Sicilian
            new[] { "Nf3", "Nc6", "d4", "cxd4", "Nxd4" },   // Accelerated Dragon
            new[] { "Nf3", "g6", "d4", "cxd4", "Nxd4" },    // Hyperaccelerated Dragon
            
            // Closed Sicilian alternative
            new[] { "Nc3", "Nc6", "g3", "g6", "Bg2" },      // Closed Sicilian system
            new[] { "Nc3", "d6", "g3", "g6", "Bg2" },       // Fianchetto system
        };
        #endregion

        #region Position-based opening knowledge
        // Key position hashes mapped to preferred moves
        private static readonly Dictionary<string, string[]> PositionMoves = new()
        {
            // Starting position - choose e4 or d4 randomly
            ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"] = new[] { "e4", "d4" },
            
            // After 1.e4
            ["rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"] = new[] { "e5", "c6", "c5" },
            
            // After 1.d4
            ["rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1"] = new[] { "d5", "Nf6", "f5" },
            
            // After 1.e4 e5 - go into Vienna
            ["rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"] = new[] { "Nc3" },
            
            // After 1.e4 c6 - Caro-Kann
            ["rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"] = new[] { "d4" },
            
            // After 1.d4 d5 - go into London
            ["rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq d6 0 2"] = new[] { "Nf3", "Bf4" },
            
            // After 1.d4 f5 - Dutch Defense
            ["rnbqkbnr/ppppp1pp/8/5p2/3P4/8/PPP1PPPP/RNBQKBNR w KQkq f6 0 2"] = new[] { "Nf3", "c4" },
        };
        #endregion

        private static readonly Random random = new Random();

        /// <summary>
        /// Try to get an opening move for the current position
        /// </summary>
        /// <param name="board">Current board position</param>
        /// <returns>Opening move in algebraic notation, or null if not in book</returns>
        public static string? GetOpeningMove(Board board)
        {
            // Only use opening book in first 8 moves (16 half-moves)
            int halfMoves = (board.FullMoveNumber - 1) * 2 + (board.IsWhiteToMove ? 0 : 1);
            if (halfMoves > 16) // 8 moves per side
                return null;

            // For now, use simple move-based logic since FEN generation isn't implemented
            return GetMoveByCount(board, halfMoves);
        }

        /// <summary>
        /// Get opening move based on move count (simplified approach)
        /// </summary>
        private static string? GetMoveByCount(Board board, int halfMoves)
        {
            return halfMoves switch
            {
                0 => board.IsWhiteToMove ? (random.Next(2) == 0 ? "e4" : "d4") : null, // First move for white
                1 => !board.IsWhiteToMove ? GetBlackResponse() : null, // First move for black
                2 => board.IsWhiteToMove ? GetWhiteSecondMove() : null, // Second move for white
                3 => !board.IsWhiteToMove ? GetBlackSecondMove() : null, // Second move for black
                _ => null // Fall back to engine after move 2
            };
        }

        /// <summary>
        /// Get Black's response to White's first move
        /// </summary>
        private static string GetBlackResponse()
        {
            // Simplified: respond to e4 with e5 or c6, to d4 with d5 or f5
            string[] responses = { "e5", "c6", "d5", "f5" };
            return responses[random.Next(responses.Length)];
        }

        /// <summary>
        /// Get White's second move
        /// </summary>
        private static string GetWhiteSecondMove()
        {
            // After e4: develop knight or bishop, after d4: develop pieces
            string[] moves = { "Nf3", "Nc3", "Bf4", "Bc4" };
            return moves[random.Next(moves.Length)];
        }

        /// <summary>
        /// Get Black's second move
        /// </summary>
        private static string GetBlackSecondMove()
        {
            // Develop pieces
            string[] moves = { "Nf6", "Nc6", "Be7", "Bg4" };
            return moves[random.Next(moves.Length)];
        }

        /// <summary>
        /// Extract the game history from the current position
        /// </summary>
        private static List<string> GetGameHistory(Board board)
        {
            // This is a simplified implementation
            // In a full implementation, we'd track the actual move history
            var history = new List<string>();
            
            // For now, we'll work with the limited position information we have
            // This is a placeholder - in practice, you'd maintain move history
            
            return history;
        }

        /// <summary>
        /// Find a book move based on the current game history
        /// </summary>
        private static string? FindBookMove(List<string> gameHistory)
        {
            // If no history, return starting moves
            if (gameHistory.Count == 0)
            {
                return random.Next(2) == 0 ? "e4" : "d4";
            }

            // Try to match against our opening lines
            var allLines = GetAllOpeningLines();
            
            foreach (var line in allLines)
            {
                if (MatchesHistory(line, gameHistory))
                {
                    // Return the next move in this line
                    if (gameHistory.Count < line.Length)
                    {
                        return line[gameHistory.Count];
                    }
                }
            }

            return null;
        }

        /// <summary>
        /// Get all opening lines combined
        /// </summary>
        private static string[][] GetAllOpeningLines()
        {
            var allLines = new List<string[]>();
            allLines.AddRange(LondonSystemLines);
            allLines.AddRange(ViennaSystemLines);
            allLines.AddRange(CaroKannLines);
            allLines.AddRange(DutchDefenseLines);
            allLines.AddRange(QueensPawnGameLines);
            allLines.AddRange(SicilianDefenseLines);
            return allLines.ToArray();
        }

        /// <summary>
        /// Check if a line matches the current game history
        /// </summary>
        private static bool MatchesHistory(string[] line, List<string> history)
        {
            if (history.Count > line.Length)
                return false;

            for (int i = 0; i < history.Count; i++)
            {
                if (!string.Equals(line[i], history[i], StringComparison.OrdinalIgnoreCase))
                {
                    return false;
                }
            }

            return true;
        }

        /// <summary>
        /// Check if current position is likely still in opening phase
        /// </summary>
        public static bool IsInOpeningPhase(Board board)
        {
            // Simple heuristics for opening phase
            int halfMoves = (board.FullMoveNumber - 1) * 2 + (board.IsWhiteToMove ? 0 : 1);
            if (halfMoves > 20) // 10 moves per side
                return false;

            // Count developed pieces (not on starting squares)
            int developedPieces = CountDevelopedPieces(board);
            
            // If too many pieces developed, we're past opening
            return developedPieces < 8;
        }

        /// <summary>
        /// Count how many pieces have been developed from starting positions
        /// </summary>
        private static int CountDevelopedPieces(Board board)
        {
            int developed = 0;
            
            // Starting positions for pieces we care about
            int[] startingSquares = { 1, 2, 5, 6, 57, 58, 61, 62 }; // Knights and bishops
            
            foreach (int square in startingSquares)
            {
                var piece = board.GetPiece(new Square(square));
                
                // If square is empty or has different piece type, it's been developed
                if (piece.IsNull || !IsOnStartingSquare(piece, square))
                {
                    developed++;
                }
            }
            
            return developed;
        }

        /// <summary>
        /// Check if a piece is on its expected starting square
        /// </summary>
        private static bool IsOnStartingSquare(Piece piece, int square)
        {
            // Map expected piece types to starting squares
            return square switch
            {
                1 or 57 => piece.PieceType == PieceType.Knight,  // b1, b8
                2 or 58 => piece.PieceType == PieceType.Bishop,  // c1, c8  
                5 or 61 => piece.PieceType == PieceType.Bishop,  // f1, f8
                6 or 62 => piece.PieceType == PieceType.Knight,  // g1, g8
                _ => false
            };
        }

        /// <summary>
        /// Get statistics about the opening book
        /// </summary>
        public static string GetBookStats()
        {
            var stats = new StringBuilder();
            stats.AppendLine($"Opening Book Statistics:");
            stats.AppendLine($"London System lines: {LondonSystemLines.Length}");
            stats.AppendLine($"Vienna System lines: {ViennaSystemLines.Length}");
            stats.AppendLine($"Caro-Kann lines: {CaroKannLines.Length}");
            stats.AppendLine($"Dutch Defense lines: {DutchDefenseLines.Length}");
            stats.AppendLine($"Queen's Pawn Game lines: {QueensPawnGameLines.Length}");
            stats.AppendLine($"Sicilian Defense lines: {SicilianDefenseLines.Length}");
            stats.AppendLine($"Position-specific moves: {PositionMoves.Count}");
            
            int totalMoves = LondonSystemLines.Sum(line => line.Length) +
                           ViennaSystemLines.Sum(line => line.Length) +
                           CaroKannLines.Sum(line => line.Length) +
                           DutchDefenseLines.Sum(line => line.Length) +
                           QueensPawnGameLines.Sum(line => line.Length) +
                           SicilianDefenseLines.Sum(line => line.Length);
            
            stats.AppendLine($"Total book moves: {totalMoves}");
            
            return stats.ToString();
        }
    }
}
