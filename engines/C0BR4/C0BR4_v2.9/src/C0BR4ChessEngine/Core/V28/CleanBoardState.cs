using System;
using System.Text;

namespace C0BR4ChessEngine.Core.V28
{
    /// <summary>
    /// Clean board state representation for C0BR4 v2.8
    /// Simple, reliable bitboard-based position tracking
    /// Built from scratch to eliminate legacy issues
    /// </summary>
    public struct CleanBoardState
    {
        // Piece bitboards by color and type
        public ulong WhitePawns;
        public ulong WhiteRooks;
        public ulong WhiteKnights;
        public ulong WhiteBishops;
        public ulong WhiteQueens;
        public ulong WhiteKing;
        
        public ulong BlackPawns;
        public ulong BlackRooks;
        public ulong BlackKnights;
        public ulong BlackBishops;
        public ulong BlackQueens;
        public ulong BlackKing;
        
        // Game state
        public bool WhiteToMove;
        public bool WhiteCanCastleKingside;
        public bool WhiteCanCastleQueenside;
        public bool BlackCanCastleKingside;
        public bool BlackCanCastleQueenside;
        public int EnPassantSquare; // -1 if no en passant
        public int HalfmoveClock;
        public int FullmoveNumber;
        
        // Cached occupancy bitboards for performance
        public ulong WhitePieces;
        public ulong BlackPieces;
        public ulong AllPieces;
        
        /// <summary>
        /// Initialize board to starting position
        /// </summary>
        public static CleanBoardState StartingPosition()
        {
            var board = new CleanBoardState();
            
            // White pieces
            board.WhitePawns = 0x000000000000FF00UL;    // 2nd rank
            board.WhiteRooks = 0x0000000000000081UL;    // a1, h1
            board.WhiteKnights = 0x0000000000000042UL;  // b1, g1
            board.WhiteBishops = 0x0000000000000024UL;  // c1, f1
            board.WhiteQueens = 0x0000000000000008UL;   // d1
            board.WhiteKing = 0x0000000000000010UL;     // e1
            
            // Black pieces
            board.BlackPawns = 0x00FF000000000000UL;    // 7th rank
            board.BlackRooks = 0x8100000000000000UL;    // a8, h8
            board.BlackKnights = 0x4200000000000000UL;  // b8, g8
            board.BlackBishops = 0x2400000000000000UL;  // c8, f8
            board.BlackQueens = 0x0800000000000000UL;   // d8
            board.BlackKing = 0x1000000000000000UL;     // e8
            
            // Game state
            board.WhiteToMove = true;
            board.WhiteCanCastleKingside = true;
            board.WhiteCanCastleQueenside = true;
            board.BlackCanCastleKingside = true;
            board.BlackCanCastleQueenside = true;
            board.EnPassantSquare = -1;
            board.HalfmoveClock = 0;
            board.FullmoveNumber = 1;
            
            board.UpdateOccupancyBitboards();
            return board;
        }
        
        /// <summary>
        /// Update cached occupancy bitboards
        /// Must be called after any piece movement
        /// </summary>
        public void UpdateOccupancyBitboards()
        {
            WhitePieces = WhitePawns | WhiteRooks | WhiteKnights | WhiteBishops | WhiteQueens | WhiteKing;
            BlackPieces = BlackPawns | BlackRooks | BlackKnights | BlackBishops | BlackQueens | BlackKing;
            AllPieces = WhitePieces | BlackPieces;
        }
        
        /// <summary>
        /// Get piece type at square (0=empty, 1=pawn, 2=rook, 3=knight, 4=bishop, 5=queen, 6=king)
        /// </summary>
        public int GetPieceTypeAt(int square)
        {
            ulong squareBit = CleanBitboard.SquareToBitboard(square);
            
            if ((WhitePawns & squareBit) != 0 || (BlackPawns & squareBit) != 0) return 1;
            if ((WhiteRooks & squareBit) != 0 || (BlackRooks & squareBit) != 0) return 2;
            if ((WhiteKnights & squareBit) != 0 || (BlackKnights & squareBit) != 0) return 3;
            if ((WhiteBishops & squareBit) != 0 || (BlackBishops & squareBit) != 0) return 4;
            if ((WhiteQueens & squareBit) != 0 || (BlackQueens & squareBit) != 0) return 5;
            if ((WhiteKing & squareBit) != 0 || (BlackKing & squareBit) != 0) return 6;
            
            return 0; // Empty square
        }
        
        /// <summary>
        /// Check if square contains white piece
        /// </summary>
        public bool IsWhitePiece(int square)
        {
            ulong squareBit = CleanBitboard.SquareToBitboard(square);
            return (WhitePieces & squareBit) != 0;
        }
        
        /// <summary>
        /// Check if square contains black piece
        /// </summary>
        public bool IsBlackPiece(int square)
        {
            ulong squareBit = CleanBitboard.SquareToBitboard(square);
            return (BlackPieces & squareBit) != 0;
        }
        
        /// <summary>
        /// Check if square is empty
        /// </summary>
        public bool IsEmpty(int square)
        {
            ulong squareBit = CleanBitboard.SquareToBitboard(square);
            return (AllPieces & squareBit) == 0;
        }
        
        /// <summary>
        /// Get bitboard for specific piece type and color
        /// </summary>
        public ulong GetPieceBitboard(int pieceType, bool isWhite)
        {
            return pieceType switch
            {
                1 => isWhite ? WhitePawns : BlackPawns,
                2 => isWhite ? WhiteRooks : BlackRooks,
                3 => isWhite ? WhiteKnights : BlackKnights,
                4 => isWhite ? WhiteBishops : BlackBishops,
                5 => isWhite ? WhiteQueens : BlackQueens,
                6 => isWhite ? WhiteKing : BlackKing,
                _ => 0UL
            };
        }
        
        /// <summary>
        /// Set piece bitboard for specific piece type and color
        /// </summary>
        public void SetPieceBitboard(int pieceType, bool isWhite, ulong bitboard)
        {
            switch (pieceType)
            {
                case 1:
                    if (isWhite) WhitePawns = bitboard;
                    else BlackPawns = bitboard;
                    break;
                case 2:
                    if (isWhite) WhiteRooks = bitboard;
                    else BlackRooks = bitboard;
                    break;
                case 3:
                    if (isWhite) WhiteKnights = bitboard;
                    else BlackKnights = bitboard;
                    break;
                case 4:
                    if (isWhite) WhiteBishops = bitboard;
                    else BlackBishops = bitboard;
                    break;
                case 5:
                    if (isWhite) WhiteQueens = bitboard;
                    else BlackQueens = bitboard;
                    break;
                case 6:
                    if (isWhite) WhiteKing = bitboard;
                    else BlackKing = bitboard;
                    break;
            }
        }
        
        /// <summary>
        /// Remove piece from square
        /// </summary>
        public void RemovePiece(int square)
        {
            ulong clearMask = ~CleanBitboard.SquareToBitboard(square);
            
            WhitePawns &= clearMask;
            WhiteRooks &= clearMask;
            WhiteKnights &= clearMask;
            WhiteBishops &= clearMask;
            WhiteQueens &= clearMask;
            WhiteKing &= clearMask;
            
            BlackPawns &= clearMask;
            BlackRooks &= clearMask;
            BlackKnights &= clearMask;
            BlackBishops &= clearMask;
            BlackQueens &= clearMask;
            BlackKing &= clearMask;
        }
        
        /// <summary>
        /// Add piece to square
        /// </summary>
        public void AddPiece(int square, int pieceType, bool isWhite)
        {
            ulong squareBit = CleanBitboard.SquareToBitboard(square);
            
            switch (pieceType)
            {
                case 1:
                    if (isWhite) WhitePawns |= squareBit;
                    else BlackPawns |= squareBit;
                    break;
                case 2:
                    if (isWhite) WhiteRooks |= squareBit;
                    else BlackRooks |= squareBit;
                    break;
                case 3:
                    if (isWhite) WhiteKnights |= squareBit;
                    else BlackKnights |= squareBit;
                    break;
                case 4:
                    if (isWhite) WhiteBishops |= squareBit;
                    else BlackBishops |= squareBit;
                    break;
                case 5:
                    if (isWhite) WhiteQueens |= squareBit;
                    else BlackQueens |= squareBit;
                    break;
                case 6:
                    if (isWhite) WhiteKing |= squareBit;
                    else BlackKing |= squareBit;
                    break;
            }
        }
        
        /// <summary>
        /// Convert board state to FEN string
        /// </summary>
        public string ToFEN()
        {
            var sb = new StringBuilder();
            
            // Piece placement
            for (int rank = 7; rank >= 0; rank--)
            {
                int emptyCount = 0;
                for (int file = 0; file < 8; file++)
                {
                    int square = CleanBitboard.GetSquare(file, rank);
                    int pieceType = GetPieceTypeAt(square);
                    
                    if (pieceType == 0)
                    {
                        emptyCount++;
                    }
                    else
                    {
                        if (emptyCount > 0)
                        {
                            sb.Append(emptyCount);
                            emptyCount = 0;
                        }
                        
                        char piece = pieceType switch
                        {
                            1 => 'p',
                            2 => 'r',
                            3 => 'n',
                            4 => 'b',
                            5 => 'q',
                            6 => 'k',
                            _ => '?'
                        };
                        
                        if (IsWhitePiece(square))
                            piece = char.ToUpper(piece);
                            
                        sb.Append(piece);
                    }
                }
                
                if (emptyCount > 0)
                    sb.Append(emptyCount);
                    
                if (rank > 0)
                    sb.Append('/');
            }
            
            sb.Append(' ');
            
            // Active color
            sb.Append(WhiteToMove ? 'w' : 'b');
            sb.Append(' ');
            
            // Castling rights
            string castling = "";
            if (WhiteCanCastleKingside) castling += "K";
            if (WhiteCanCastleQueenside) castling += "Q";
            if (BlackCanCastleKingside) castling += "k";
            if (BlackCanCastleQueenside) castling += "q";
            if (castling == "") castling = "-";
            sb.Append(castling);
            sb.Append(' ');
            
            // En passant
            if (EnPassantSquare >= 0)
            {
                int file = CleanBitboard.GetFile(EnPassantSquare);
                int rank = CleanBitboard.GetRank(EnPassantSquare);
                sb.Append((char)('a' + file));
                sb.Append((char)('1' + rank));
            }
            else
            {
                sb.Append('-');
            }
            sb.Append(' ');
            
            // Halfmove clock and fullmove number
            sb.Append(HalfmoveClock);
            sb.Append(' ');
            sb.Append(FullmoveNumber);
            
            return sb.ToString();
        }
        
        /// <summary>
        /// Validate board state for correctness
        /// </summary>
        public bool IsValid()
        {
            // Check exactly one king per side
            if (CleanBitboard.PopCount(WhiteKing) != 1 || CleanBitboard.PopCount(BlackKing) != 1)
                return false;
                
            // Check no piece overlaps
            ulong[] allBitboards = { WhitePawns, WhiteRooks, WhiteKnights, WhiteBishops, WhiteQueens, WhiteKing,
                                   BlackPawns, BlackRooks, BlackKnights, BlackBishops, BlackQueens, BlackKing };
            
            for (int i = 0; i < allBitboards.Length; i++)
            {
                for (int j = i + 1; j < allBitboards.Length; j++)
                {
                    if ((allBitboards[i] & allBitboards[j]) != 0)
                        return false; // Piece overlap
                }
            }
            
            // Check occupancy bitboards match
            ulong expectedWhite = WhitePawns | WhiteRooks | WhiteKnights | WhiteBishops | WhiteQueens | WhiteKing;
            ulong expectedBlack = BlackPawns | BlackRooks | BlackKnights | BlackBishops | BlackQueens | BlackKing;
            ulong expectedAll = expectedWhite | expectedBlack;
            
            if (WhitePieces != expectedWhite || BlackPieces != expectedBlack || AllPieces != expectedAll)
                return false;
                
            return true;
        }
    }
}
