using System;
using System.Collections.Generic;

namespace C0BR4ChessEngine.Core.V28
{
    /// <summary>
    /// Clean FEN parser for C0BR4 v2.8
    /// Simple, reliable FEN string parsing
    /// Built from scratch to eliminate legacy issues
    /// </summary>
    public static class CleanFenParser
    {
        /// <summary>
        /// Parse FEN string to board state
        /// </summary>
        public static CleanBoardState ParseFen(string fen)
        {
            if (string.IsNullOrWhiteSpace(fen))
                throw new ArgumentException("FEN string cannot be null or empty");
            
            string[] parts = fen.Trim().Split(' ');
            if (parts.Length < 4)
                throw new ArgumentException("Invalid FEN format - insufficient parts");
            
            var boardState = new CleanBoardState();
            
            // Parse piece placement
            ParsePiecePlacement(parts[0], ref boardState);
            
            // Parse active color
            boardState.WhiteToMove = parts[1] == "w";
            
            // Parse castling rights
            ParseCastlingRights(parts[2], ref boardState);
            
            // Parse en passant square
            ParseEnPassantSquare(parts[3], ref boardState);
            
            // Parse halfmove clock (optional)
            if (parts.Length > 4)
            {
                if (int.TryParse(parts[4], out int halfmove))
                    boardState.HalfmoveClock = halfmove;
            }
            
            // Parse fullmove number (optional)
            if (parts.Length > 5)
            {
                if (int.TryParse(parts[5], out int fullmove))
                    boardState.FullmoveNumber = Math.Max(1, fullmove);
            }
            else
            {
                boardState.FullmoveNumber = 1;
            }
            
            // Update occupancy bitboards
            boardState.UpdateOccupancyBitboards();
            
            // Validate the resulting position
            if (!boardState.IsValid())
                throw new ArgumentException("FEN results in invalid board state");
            
            return boardState;
        }
        
        /// <summary>
        /// Parse piece placement part of FEN
        /// </summary>
        private static void ParsePiecePlacement(string piecePlacement, ref CleanBoardState boardState)
        {
            // Clear all piece bitboards
            boardState.WhitePawns = 0UL;
            boardState.WhiteRooks = 0UL;
            boardState.WhiteKnights = 0UL;
            boardState.WhiteBishops = 0UL;
            boardState.WhiteQueens = 0UL;
            boardState.WhiteKing = 0UL;
            boardState.BlackPawns = 0UL;
            boardState.BlackRooks = 0UL;
            boardState.BlackKnights = 0UL;
            boardState.BlackBishops = 0UL;
            boardState.BlackQueens = 0UL;
            boardState.BlackKing = 0UL;
            
            string[] ranks = piecePlacement.Split('/');
            if (ranks.Length != 8)
                throw new ArgumentException("Invalid FEN - must have 8 ranks");
            
            for (int rank = 7; rank >= 0; rank--) // FEN starts from 8th rank
            {
                int file = 0;
                string rankString = ranks[7 - rank];
                
                foreach (char c in rankString)
                {
                    if (char.IsDigit(c))
                    {
                        // Empty squares
                        int emptySquares = c - '0';
                        if (emptySquares < 1 || emptySquares > 8)
                            throw new ArgumentException($"Invalid FEN - invalid empty square count: {emptySquares}");
                        file += emptySquares;
                    }
                    else
                    {
                        // Piece
                        if (file >= 8)
                            throw new ArgumentException("Invalid FEN - too many pieces in rank");
                        
                        int square = CleanBitboard.GetSquare(file, rank);
                        bool isWhite = char.IsUpper(c);
                        char piece = char.ToLower(c);
                        
                        int pieceType = piece switch
                        {
                            'p' => 1,
                            'r' => 2,
                            'n' => 3,
                            'b' => 4,
                            'q' => 5,
                            'k' => 6,
                            _ => throw new ArgumentException($"Invalid FEN - unknown piece: {c}")
                        };
                        
                        boardState.AddPiece(square, pieceType, isWhite);
                        file++;
                    }
                }
                
                if (file != 8)
                    throw new ArgumentException($"Invalid FEN - rank {rank + 1} has {file} squares instead of 8");
            }
        }
        
        /// <summary>
        /// Parse castling rights part of FEN
        /// </summary>
        private static void ParseCastlingRights(string castlingRights, ref CleanBoardState boardState)
        {
            boardState.WhiteCanCastleKingside = false;
            boardState.WhiteCanCastleQueenside = false;
            boardState.BlackCanCastleKingside = false;
            boardState.BlackCanCastleQueenside = false;
            
            if (castlingRights == "-")
                return;
            
            foreach (char c in castlingRights)
            {
                switch (c)
                {
                    case 'K':
                        boardState.WhiteCanCastleKingside = true;
                        break;
                    case 'Q':
                        boardState.WhiteCanCastleQueenside = true;
                        break;
                    case 'k':
                        boardState.BlackCanCastleKingside = true;
                        break;
                    case 'q':
                        boardState.BlackCanCastleQueenside = true;
                        break;
                    default:
                        throw new ArgumentException($"Invalid FEN - unknown castling right: {c}");
                }
            }
        }
        
        /// <summary>
        /// Parse en passant square part of FEN
        /// </summary>
        private static void ParseEnPassantSquare(string enPassantSquare, ref CleanBoardState boardState)
        {
            boardState.EnPassantSquare = -1;
            
            if (enPassantSquare == "-")
                return;
            
            if (enPassantSquare.Length != 2)
                throw new ArgumentException("Invalid FEN - en passant square must be 2 characters or '-'");
            
            char fileChar = enPassantSquare[0];
            char rankChar = enPassantSquare[1];
            
            if (fileChar < 'a' || fileChar > 'h' || rankChar < '1' || rankChar > '8')
                throw new ArgumentException("Invalid FEN - en passant square out of bounds");
            
            int file = fileChar - 'a';
            int rank = rankChar - '1';
            
            boardState.EnPassantSquare = CleanBitboard.GetSquare(file, rank);
        }
        
        /// <summary>
        /// Get starting position FEN
        /// </summary>
        public static string StartingPositionFen => "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
        
        /// <summary>
        /// Validate FEN string format (basic check)
        /// </summary>
        public static bool IsValidFenFormat(string fen)
        {
            try
            {
                ParseFen(fen);
                return true;
            }
            catch
            {
                return false;
            }
        }
    }
}
