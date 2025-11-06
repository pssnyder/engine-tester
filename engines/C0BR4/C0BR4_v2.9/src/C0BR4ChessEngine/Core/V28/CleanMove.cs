using System;
using System.Collections.Generic;

namespace C0BR4ChessEngine.Core.V28
{
    /// <summary>
    /// Clean, simple move representation for C0BR4 v2.8
    /// Built from scratch to ensure correctness and clarity
    /// </summary>
    public struct CleanMove
    {
        public int FromSquare;
        public int ToSquare;
        public int PieceType;      // 1=pawn, 2=rook, 3=knight, 4=bishop, 5=queen, 6=king
        public bool IsWhite;
        public int CapturedPieceType; // 0 if no capture
        public bool IsEnPassant;
        public bool IsCastling;
        public int PromotionPieceType; // 0 if no promotion
        public bool IsCheck;
        public bool IsCheckmate;
        
        /// <summary>
        /// Create a simple move
        /// </summary>
        public static CleanMove Create(int fromSquare, int toSquare, int pieceType, bool isWhite)
        {
            return new CleanMove
            {
                FromSquare = fromSquare,
                ToSquare = toSquare,
                PieceType = pieceType,
                IsWhite = isWhite,
                CapturedPieceType = 0,
                IsEnPassant = false,
                IsCastling = false,
                PromotionPieceType = 0,
                IsCheck = false,
                IsCheckmate = false
            };
        }
        
        /// <summary>
        /// Create a capture move
        /// </summary>
        public static CleanMove CreateCapture(int fromSquare, int toSquare, int pieceType, bool isWhite, int capturedPieceType)
        {
            return new CleanMove
            {
                FromSquare = fromSquare,
                ToSquare = toSquare,
                PieceType = pieceType,
                IsWhite = isWhite,
                CapturedPieceType = capturedPieceType,
                IsEnPassant = false,
                IsCastling = false,
                PromotionPieceType = 0,
                IsCheck = false,
                IsCheckmate = false
            };
        }
        
        /// <summary>
        /// Create a castling move
        /// </summary>
        public static CleanMove CreateCastling(int fromSquare, int toSquare, bool isWhite)
        {
            return new CleanMove
            {
                FromSquare = fromSquare,
                ToSquare = toSquare,
                PieceType = 6, // King
                IsWhite = isWhite,
                CapturedPieceType = 0,
                IsEnPassant = false,
                IsCastling = true,
                PromotionPieceType = 0,
                IsCheck = false,
                IsCheckmate = false
            };
        }
        
        /// <summary>
        /// Create an en passant move
        /// </summary>
        public static CleanMove CreateEnPassant(int fromSquare, int toSquare, bool isWhite)
        {
            return new CleanMove
            {
                FromSquare = fromSquare,
                ToSquare = toSquare,
                PieceType = 1, // Pawn
                IsWhite = isWhite,
                CapturedPieceType = 1, // Captured pawn
                IsEnPassant = true,
                IsCastling = false,
                PromotionPieceType = 0,
                IsCheck = false,
                IsCheckmate = false
            };
        }
        
        /// <summary>
        /// Create a promotion move
        /// </summary>
        public static CleanMove CreatePromotion(int fromSquare, int toSquare, bool isWhite, int promotionPieceType, int capturedPieceType = 0)
        {
            return new CleanMove
            {
                FromSquare = fromSquare,
                ToSquare = toSquare,
                PieceType = 1, // Pawn
                IsWhite = isWhite,
                CapturedPieceType = capturedPieceType,
                IsEnPassant = false,
                IsCastling = false,
                PromotionPieceType = promotionPieceType,
                IsCheck = false,
                IsCheckmate = false
            };
        }
        
        /// <summary>
        /// Check if this is a valid move (basic validation)
        /// </summary>
        public bool IsValid()
        {
            // Basic bounds checking
            if (FromSquare < 0 || FromSquare > 63 || ToSquare < 0 || ToSquare > 63)
                return false;
                
            // Can't move to same square
            if (FromSquare == ToSquare)
                return false;
                
            // Piece type must be valid
            if (PieceType < 1 || PieceType > 6)
                return false;
                
            // Captured piece type must be valid (0 for no capture is OK)
            if (CapturedPieceType < 0 || CapturedPieceType > 6)
                return false;
                
            // Promotion piece type must be valid (0 for no promotion is OK)
            if (PromotionPieceType < 0 || PromotionPieceType > 6)
                return false;
                
            // En passant must be pawn move
            if (IsEnPassant && PieceType != 1)
                return false;
                
            // Castling must be king move
            if (IsCastling && PieceType != 6)
                return false;
                
            // Promotion must be pawn move
            if (PromotionPieceType > 0 && PieceType != 1)
                return false;
                
            return true;
        }
        
        /// <summary>
        /// Convert move to UCI notation (e.g., "e2e4", "e7e8q")
        /// </summary>
        public string ToUCI()
        {
            string from = SquareToString(FromSquare);
            string to = SquareToString(ToSquare);
            
            string promotion = "";
            if (PromotionPieceType > 0)
            {
                promotion = PromotionPieceType switch
                {
                    2 => "r",
                    3 => "n",
                    4 => "b",
                    5 => "q",
                    _ => ""
                };
            }
            
            return from + to + promotion;
        }
        
        /// <summary>
        /// Parse UCI notation to move (requires board state for validation)
        /// </summary>
        public static CleanMove FromUCI(string uci, CleanBoardState boardState)
        {
            if (string.IsNullOrEmpty(uci) || uci.Length < 4)
                throw new ArgumentException("Invalid UCI move format");
                
            int fromSquare = StringToSquare(uci.Substring(0, 2));
            int toSquare = StringToSquare(uci.Substring(2, 2));
            
            int pieceType = boardState.GetPieceTypeAt(fromSquare);
            bool isWhite = boardState.IsWhitePiece(fromSquare);
            int capturedPieceType = boardState.GetPieceTypeAt(toSquare);
            
            CleanMove move = new CleanMove
            {
                FromSquare = fromSquare,
                ToSquare = toSquare,
                PieceType = pieceType,
                IsWhite = isWhite,
                CapturedPieceType = capturedPieceType,
                IsEnPassant = false,
                IsCastling = false,
                PromotionPieceType = 0,
                IsCheck = false,
                IsCheckmate = false
            };
            
            // Check for promotion
            if (uci.Length == 5)
            {
                char promotionChar = uci[4];
                move.PromotionPieceType = promotionChar switch
                {
                    'q' => 5,
                    'r' => 2,
                    'b' => 4,
                    'n' => 3,
                    _ => 0
                };
            }
            
            // Check for en passant
            if (pieceType == 1 && capturedPieceType == 0 && 
                CleanBitboard.GetFile(fromSquare) != CleanBitboard.GetFile(toSquare))
            {
                move.IsEnPassant = true;
                move.CapturedPieceType = 1; // Captured pawn
            }
            
            // Check for castling
            if (pieceType == 6)
            {
                int fromFile = CleanBitboard.GetFile(fromSquare);
                int toFile = CleanBitboard.GetFile(toSquare);
                if (Math.Abs(fromFile - toFile) > 1)
                {
                    move.IsCastling = true;
                }
            }
            
            return move;
        }
        
        /// <summary>
        /// Convert square index to algebraic notation
        /// </summary>
        private static string SquareToString(int square)
        {
            int file = CleanBitboard.GetFile(square);
            int rank = CleanBitboard.GetRank(square);
            return $"{(char)('a' + file)}{(char)('1' + rank)}";
        }
        
        /// <summary>
        /// Convert algebraic notation to square index
        /// </summary>
        private static int StringToSquare(string square)
        {
            if (square.Length != 2)
                throw new ArgumentException("Invalid square format");
                
            int file = square[0] - 'a';
            int rank = square[1] - '1';
            
            if (file < 0 || file > 7 || rank < 0 || rank > 7)
                throw new ArgumentException("Square out of bounds");
                
            return CleanBitboard.GetSquare(file, rank);
        }
        
        public override string ToString()
        {
            return ToUCI();
        }
        
        public override bool Equals(object? obj)
        {
            if (obj is not CleanMove other)
                return false;
                
            return FromSquare == other.FromSquare &&
                   ToSquare == other.ToSquare &&
                   PieceType == other.PieceType &&
                   IsWhite == other.IsWhite &&
                   PromotionPieceType == other.PromotionPieceType;
        }
        
        public override int GetHashCode()
        {
            return HashCode.Combine(FromSquare, ToSquare, PieceType, IsWhite, PromotionPieceType);
        }
        
        public static bool operator ==(CleanMove left, CleanMove right)
        {
            return left.Equals(right);
        }
        
        public static bool operator !=(CleanMove left, CleanMove right)
        {
            return !left.Equals(right);
        }
    }
}
