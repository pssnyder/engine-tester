using System;
using System.Collections.Generic;
using C0BR4ChessEngine.Core;

namespace C0BR4ChessEngine.Search
{
    /// <summary>
    /// Entry stored in the transposition table
    /// Contains evaluation, best move, and search metadata
    /// </summary>
    public struct TranspositionEntry
    {
        public int Depth;           // Search depth this entry was computed at
        public int Score;           // Evaluation score
        public Move BestMove;       // Best move found at this position
        public EntryType Type;      // Type of bound (exact, lower, upper)
        
        public TranspositionEntry(int depth, int score, Move bestMove, EntryType type)
        {
            Depth = depth;
            Score = score;
            BestMove = bestMove;
            Type = type;
        }
    }

    /// <summary>
    /// Type of transposition table entry
    /// </summary>
    public enum EntryType
    {
        Exact,      // Exact score (search completed normally)
        LowerBound, // Score is at least this value (alpha cutoff)
        UpperBound  // Score is at most this value (beta cutoff)
    }

    /// <summary>
    /// Zobrist hash-keyed transposition table for caching search results
    /// Much faster than string-based keys and more memory efficient
    /// </summary>
    public class TranspositionTable
    {
        private readonly Dictionary<ulong, TranspositionEntry> table;
        private readonly int maxEntries;
        private int hits = 0;
        private int stores = 0;

        public TranspositionTable(int maxEntries = 100000)
        {
            this.maxEntries = maxEntries;
            this.table = new Dictionary<ulong, TranspositionEntry>(maxEntries);
        }

        /// <summary>
        /// Try to retrieve a cached result for this position
        /// </summary>
        public bool TryGetEntry(Board board, int depth, int alpha, int beta, out TranspositionEntry entry)
        {
            ulong hash = ZobristHashing.CalculateHash(board);
            
            if (table.TryGetValue(hash, out entry))
            {
                // Only use the entry if it was searched to at least the same depth
                if (entry.Depth >= depth)
                {
                    hits++;
                    
                    // Check if we can use this score based on the bound type
                    switch (entry.Type)
                    {
                        case EntryType.Exact:
                            return true; // Exact score, always usable
                        
                        case EntryType.LowerBound:
                            if (entry.Score >= beta)
                                return true; // Score is at least beta, causes cutoff
                            break;
                        
                        case EntryType.UpperBound:
                            if (entry.Score <= alpha)
                                return true; // Score is at most alpha, causes cutoff
                            break;
                    }
                }
            }

            entry = default;
            return false;
        }

        /// <summary>
        /// Store a search result in the transposition table
        /// </summary>
        public void StoreEntry(Board board, int depth, int score, Move bestMove, int alpha, int beta)
        {
            // Clear table if it gets too large (simple replacement strategy)
            if (table.Count >= maxEntries)
            {
                table.Clear();
            }

            ulong hash = ZobristHashing.CalculateHash(board);
            
            // Determine the type of bound
            EntryType entryType;
            if (score <= alpha)
            {
                entryType = EntryType.UpperBound; // Failed low
            }
            else if (score >= beta)
            {
                entryType = EntryType.LowerBound; // Failed high
            }
            else
            {
                entryType = EntryType.Exact; // Exact score
            }

            var entry = new TranspositionEntry(depth, score, bestMove, entryType);
            table[hash] = entry; // Overwrite any existing entry
            stores++;
        }

        /// <summary>
        /// Get statistics about table usage
        /// </summary>
        public (int hits, int stores, int entries) GetStatistics()
        {
            return (hits, stores, table.Count);
        }

        /// <summary>
        /// Clear the transposition table
        /// </summary>
        public void Clear()
        {
            table.Clear();
            hits = 0;
            stores = 0;
        }
    }
}
