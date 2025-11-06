using System;

namespace C0BR4ChessEngine.Core
{
    public readonly struct Move : IEquatable<Move>
    {
        public readonly Square StartSquare;
        public readonly Square TargetSquare;
        public readonly PieceType MovePieceType;
        public readonly PieceType CapturePieceType;
        public readonly PieceType PromotionPieceType;
        public readonly MoveFlag Flag;

        public bool IsCapture => CapturePieceType != PieceType.None;
        public bool IsEnPassant => Flag == MoveFlag.EnPassant;
        public bool IsPromotion => PromotionPieceType != PieceType.None;
        public bool IsCastles => Flag == MoveFlag.Castling;
        public bool IsNull => StartSquare.Index == TargetSquare.Index && MovePieceType == PieceType.None;

        public static readonly Move NullMove = new();

        /// <summary>
        /// Create a null/invalid move.
        /// </summary>
        public Move()
        {
            StartSquare = new Square(0);
            TargetSquare = new Square(0);
            MovePieceType = PieceType.None;
            CapturePieceType = PieceType.None;
            PromotionPieceType = PieceType.None;
            Flag = MoveFlag.None;
        }

        /// <summary>
        /// Create a move
        /// </summary>
        public Move(Square startSquare, Square targetSquare, PieceType movePieceType, 
                   PieceType capturePieceType = PieceType.None, PieceType promotionPieceType = PieceType.None, 
                   MoveFlag flag = MoveFlag.None)
        {
            StartSquare = startSquare;
            TargetSquare = targetSquare;
            MovePieceType = movePieceType;
            CapturePieceType = capturePieceType;
            PromotionPieceType = promotionPieceType;
            Flag = flag;
        }

        /// <summary>
        /// [DEPRECATED] Create a move from UCI notation, for example: "e2e4"
        /// WARNING: This constructor creates incomplete moves without board context!
        /// Use Board.FindLegalMove() or UCI ParseUciMove() instead for proper move creation.
        /// This method should only be used for testing/debugging purposes.
        /// </summary>
        [Obsolete("Use Board.FindLegalMove() or ParseUciMove() instead - this creates incomplete moves")]
        public Move(string moveString)
        {
            if (moveString.Length < 4)
            {
                this = NullMove;
                return;
            }

            StartSquare = new Square(moveString.Substring(0, 2));
            TargetSquare = new Square(moveString.Substring(2, 2));
            MovePieceType = PieceType.None; // Will need board context to determine
            CapturePieceType = PieceType.None;
            Flag = MoveFlag.None;

            // Handle promotion
            if (moveString.Length == 5)
            {
                PromotionPieceType = moveString[4] switch
                {
                    'q' => PieceType.Queen,
                    'r' => PieceType.Rook,
                    'b' => PieceType.Bishop,
                    'n' => PieceType.Knight,
                    _ => PieceType.None
                };
            }
            else
            {
                PromotionPieceType = PieceType.None;
            }
        }

        public override string ToString()
        {
            if (IsNull) return "(none)";
            
            // Validate square indices
            if (StartSquare.Index < 0 || StartSquare.Index > 63 ||
                TargetSquare.Index < 0 || TargetSquare.Index > 63)
            {
                return "(none)"; // Invalid square indices
            }
            
            string result = $"{StartSquare.Name}{TargetSquare.Name}";
            if (IsPromotion)
            {
                result += PromotionPieceType switch
                {
                    PieceType.Queen => "q",
                    PieceType.Rook => "r",
                    PieceType.Bishop => "b",
                    PieceType.Knight => "n",
                    _ => ""
                };
            }
            return result;
        }

        public bool Equals(Move other)
        {
            return StartSquare == other.StartSquare && 
                   TargetSquare == other.TargetSquare && 
                   MovePieceType == other.MovePieceType &&
                   CapturePieceType == other.CapturePieceType &&
                   PromotionPieceType == other.PromotionPieceType &&
                   Flag == other.Flag;
        }

        public static bool operator ==(Move lhs, Move rhs) => lhs.Equals(rhs);
        public static bool operator !=(Move lhs, Move rhs) => !lhs.Equals(rhs);
        public override bool Equals(object? obj) => obj is Move move && Equals(move);
        public override int GetHashCode() => HashCode.Combine(StartSquare, TargetSquare, MovePieceType, CapturePieceType, PromotionPieceType, Flag);
    }

    public enum MoveFlag
    {
        None,
        EnPassant,
        Castling,
        PawnTwoForward
    }
}
