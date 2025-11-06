using System;

namespace C0BR4ChessEngine.Search
{
    /// <summary>
    /// Manages time allocation for chess engine searches based on time controls
    /// </summary>
    public class TimeManager
    {
        public struct TimeControl
        {
            public int WhiteTime { get; set; }     // Milliseconds remaining for white
            public int BlackTime { get; set; }     // Milliseconds remaining for black
            public int WhiteIncrement { get; set; } // Milliseconds increment per move for white
            public int BlackIncrement { get; set; } // Milliseconds increment per move for black
            public int MovesToGo { get; set; }     // Moves to next time control (0 = no limit)
            public int MoveTime { get; set; }      // Fixed time per move (0 = use time control)
            public int Depth { get; set; }        // Fixed depth (0 = use time control)
            public bool Infinite { get; set; }    // Search until stopped
        }

        /// <summary>
        /// Calculate optimal time allocation for the current move
        /// </summary>
        /// <param name="timeControl">Time control parameters</param>
        /// <param name="isWhiteToMove">Whether white is to move</param>
        /// <param name="gamePhase">Estimated game phase (0.0 = endgame, 1.0 = opening)</param>
        /// <returns>Recommended time allocation in milliseconds</returns>
        public static int CalculateTimeAllocation(TimeControl timeControl, bool isWhiteToMove, double gamePhase = 0.5)
        {
            // Fixed time per move has highest priority
            if (timeControl.MoveTime > 0)
            {
                return Math.Max(100, timeControl.MoveTime - 50); // Reserve 50ms for overhead
            }

            // Fixed depth or infinite search - use generous time
            if (timeControl.Depth > 0 || timeControl.Infinite)
            {
                return 30000; // 30 seconds for analysis
            }

            // Get remaining time for current player
            int remainingTime = isWhiteToMove ? timeControl.WhiteTime : timeControl.BlackTime;
            int increment = isWhiteToMove ? timeControl.WhiteIncrement : timeControl.BlackIncrement;

            // Emergency time - if we have less than 2 seconds, play very quickly
            if (remainingTime < 2000)
            {
                return Math.Max(50, remainingTime / 20); // Use 5% of remaining time, minimum 50ms
            }

            // Low time - if we have less than 10 seconds, be conservative
            if (remainingTime < 10000)
            {
                return Math.Max(100, remainingTime / 15 + increment / 2); // ~7% of time + half increment
            }

            // Calculate base time allocation
            int baseTime;
            
            if (timeControl.MovesToGo > 0)
            {
                // Classical time control - divide remaining time by moves to go
                baseTime = remainingTime / Math.Max(1, timeControl.MovesToGo);
                // Add increment since we'll get it back
                baseTime += increment;
            }
            else
            {
                // Increment-based time control
                // Use a fraction of remaining time plus most of the increment
                int estimatedMovesLeft = EstimateMovesRemaining(gamePhase);
                baseTime = remainingTime / estimatedMovesLeft + (increment * 4) / 5;
            }

            // Apply game phase adjustments
            double phaseMultiplier = CalculatePhaseMultiplier(gamePhase);
            baseTime = (int)(baseTime * phaseMultiplier);

            // Apply safety margins
            baseTime = ApplySafetyMargins(baseTime, remainingTime);

            // Ensure minimum and maximum bounds
            return Math.Max(100, Math.Min(baseTime, remainingTime / 3));
        }

        /// <summary>
        /// Estimate remaining moves based on game phase
        /// </summary>
        private static int EstimateMovesRemaining(double gamePhase)
        {
            // Opening: ~40 moves, Middlegame: ~30 moves, Endgame: ~20 moves
            return (int)(20 + gamePhase * 20);
        }

        /// <summary>
        /// Calculate time multiplier based on game phase
        /// </summary>
        private static double CalculatePhaseMultiplier(double gamePhase)
        {
            // Spend more time in middlegame (complexity peak)
            // Opening: 0.9x, Middlegame: 1.2x, Endgame: 0.8x
            if (gamePhase > 0.7) // Opening
                return 0.9;
            else if (gamePhase > 0.3) // Middlegame
                return 1.2;
            else // Endgame
                return 0.8;
        }

        /// <summary>
        /// Apply safety margins to prevent time troubles
        /// </summary>
        private static int ApplySafetyMargins(int baseTime, int remainingTime)
        {
            // Never use more than 1/3 of remaining time on a single move
            if (baseTime > remainingTime / 3)
                baseTime = remainingTime / 3;

            // Reserve some time for communication overhead
            baseTime = Math.Max(100, baseTime - 50);

            return baseTime;
        }

        /// <summary>
        /// Check if search should be extended due to tactical complexity
        /// </summary>
        public static bool ShouldExtendSearch(int nodes, int timeUsed, int timeAllocated, bool inCheck = false)
        {
            // Don't extend if we're already over time
            if (timeUsed >= timeAllocated * 1.5)
                return false;

            // Extend if we're in check and haven't used much time
            if (inCheck && timeUsed < timeAllocated * 0.8)
                return true;

            // Extend if node count suggests we're in a tactical position
            // (high branching factor indicates complex position)
            double averageNps = nodes / Math.Max(1.0, timeUsed / 1000.0);
            if (averageNps < 10000 && timeUsed < timeAllocated * 0.9) // Low NPS = complex position
                return true;

            return false;
        }

        /// <summary>
        /// Parse UCI time control parameters
        /// </summary>
        public static TimeControl ParseTimeControl(string[] parts)
        {
            var timeControl = new TimeControl();

            for (int i = 0; i < parts.Length - 1; i++)
            {
                switch (parts[i])
                {
                    case "wtime":
                        if (int.TryParse(parts[i + 1], out int wtime))
                            timeControl.WhiteTime = wtime;
                        break;
                    case "btime":
                        if (int.TryParse(parts[i + 1], out int btime))
                            timeControl.BlackTime = btime;
                        break;
                    case "winc":
                        if (int.TryParse(parts[i + 1], out int winc))
                            timeControl.WhiteIncrement = winc;
                        break;
                    case "binc":
                        if (int.TryParse(parts[i + 1], out int binc))
                            timeControl.BlackIncrement = binc;
                        break;
                    case "movestogo":
                        if (int.TryParse(parts[i + 1], out int movestogo))
                            timeControl.MovesToGo = movestogo;
                        break;
                    case "movetime":
                        if (int.TryParse(parts[i + 1], out int movetime))
                            timeControl.MoveTime = movetime;
                        break;
                    case "depth":
                        if (int.TryParse(parts[i + 1], out int depth))
                            timeControl.Depth = depth;
                        break;
                    case "infinite":
                        timeControl.Infinite = true;
                        break;
                }
            }

            return timeControl;
        }
    }
}
