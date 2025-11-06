using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;

namespace C0BR4ChessEngine.Core
{
    /// <summary>
    /// Efficient bitboard-based move generator
    /// Eliminates illegal move generation that caused rule infractions
    /// </summary>
    public class BitboardMoveGenerator
    {
        private readonly List<Move> moves = new();
        private BitboardPosition position;

        public BitboardMoveGenerator()
        {
            // Initialize magic bitboards on first use
            MagicBitboards.Initialize();
        }

        /// <summary>
        /// Generate all legal moves for the current position
        /// </summary>
        public Move[] GenerateLegalMoves(BitboardPosition pos)
        {
            position = pos;
            moves.Clear();

            // Generate pseudo-legal moves first
            GeneratePseudoLegalMoves();

            // Filter out moves that leave king in check
            return FilterLegalMoves();
        }

        /// <summary>
        /// Generate all pseudo-legal moves (may include moves that leave king in check)
        /// </summary>
        public Move[] GeneratePseudoLegalMoves(BitboardPosition pos)
        {
            position = pos;
            moves.Clear();
            GeneratePseudoLegalMoves();
            return moves.ToArray();
        }

        private void GeneratePseudoLegalMoves()
        {
            bool isWhite = position.IsWhiteToMove;
            
            GeneratePawnMoves(isWhite);
            GenerateKnightMoves(isWhite);
            GenerateBishopMoves(isWhite);
            GenerateRookMoves(isWhite);
            GenerateQueenMoves(isWhite);
            GenerateKingMoves(isWhite);
            GenerateCastlingMoves(isWhite);
        }

        private void GeneratePawnMoves(bool isWhite)
        {
            ulong pawns = position.GetPieces(PieceType.Pawn, isWhite);
            ulong enemyPieces = position.GetAllPieces(!isWhite);
            ulong emptySquares = ~position.AllPieces;

            if (isWhite)
            {
                // White pawn single push
                ulong singlePush = Bitboard.ShiftNorth(pawns) & emptySquares;
                GeneratePawnPushMoves(singlePush, -8, isWhite);

                // White pawn double push
                ulong doublePush = Bitboard.ShiftNorth(singlePush) & emptySquares & Bitboard.Rank4;
                GeneratePawnDoublePushMoves(doublePush, -16);

                // White pawn captures
                ulong capturesLeft = Bitboard.ShiftNorthWest(pawns) & enemyPieces;
                ulong capturesRight = Bitboard.ShiftNorthEast(pawns) & enemyPieces;
                GeneratePawnCaptureMoves(capturesLeft, -7, isWhite);
                GeneratePawnCaptureMoves(capturesRight, -9, isWhite);
            }
            else
            {
                // Black pawn single push
                ulong singlePush = Bitboard.ShiftSouth(pawns) & emptySquares;
                GeneratePawnPushMoves(singlePush, 8, isWhite);

                // Black pawn double push
                ulong doublePush = Bitboard.ShiftSouth(singlePush) & emptySquares & Bitboard.Rank5;
                GeneratePawnDoublePushMoves(doublePush, 16);

                // Black pawn captures
                ulong capturesLeft = Bitboard.ShiftSouthWest(pawns) & enemyPieces;
                ulong capturesRight = Bitboard.ShiftSouthEast(pawns) & enemyPieces;
                GeneratePawnCaptureMoves(capturesLeft, 9, isWhite);
                GeneratePawnCaptureMoves(capturesRight, 7, isWhite);
            }

            // En passant captures
            if (position.EnPassantSquare != -1)
            {
                GenerateEnPassantMoves(isWhite);
            }
        }

        private void GeneratePawnPushMoves(ulong targets, int offset, bool isWhite)
        {
            while (targets != 0)
            {
                int toSquare = Bitboard.PopLSB(ref targets);
                int fromSquare = toSquare + offset;
                
                // Check for promotion
                int toRank = Bitboard.GetRank(toSquare);
                if ((isWhite && toRank == 7) || (!isWhite && toRank == 0))
                {
                    AddPromotionMoves(fromSquare, toSquare);
                }
                else
                {
                    AddMove(fromSquare, toSquare, PieceType.Pawn);
                }
            }
        }

        private void GeneratePawnDoublePushMoves(ulong targets, int offset)
        {
            while (targets != 0)
            {
                int toSquare = Bitboard.PopLSB(ref targets);
                int fromSquare = toSquare + offset;
                AddMove(fromSquare, toSquare, PieceType.Pawn, PieceType.None, MoveFlag.PawnTwoForward);
            }
        }

        private void GeneratePawnCaptureMoves(ulong targets, int offset, bool isWhite)
        {
            while (targets != 0)
            {
                int toSquare = Bitboard.PopLSB(ref targets);
                int fromSquare = toSquare + offset;
                var (capturedPiece, _) = position.GetPieceAt(toSquare);
                
                // Check for promotion
                int toRank = Bitboard.GetRank(toSquare);
                if ((isWhite && toRank == 7) || (!isWhite && toRank == 0))
                {
                    AddPromotionMoves(fromSquare, toSquare, capturedPiece);
                }
                else
                {
                    AddMove(fromSquare, toSquare, PieceType.Pawn, capturedPiece);
                }
            }
        }

        private void GenerateEnPassantMoves(bool isWhite)
        {
            int epSquare = position.EnPassantSquare;
            ulong pawns = position.GetPieces(PieceType.Pawn, isWhite);
            
            // Check if any of our pawns can capture en passant
            ulong attackingPawns = 0UL;
            if (isWhite)
            {
                attackingPawns = Bitboard.BlackPawnAttacks(Bitboard.SquareToBitboard(epSquare)) & pawns;
            }
            else
            {
                attackingPawns = Bitboard.WhitePawnAttacks(Bitboard.SquareToBitboard(epSquare)) & pawns;
            }

            while (attackingPawns != 0)
            {
                int fromSquare = Bitboard.PopLSB(ref attackingPawns);
                AddMove(fromSquare, epSquare, PieceType.Pawn, PieceType.Pawn, MoveFlag.EnPassant);
            }
        }

        private void GenerateKnightMoves(bool isWhite)
        {
            ulong knights = position.GetPieces(PieceType.Knight, isWhite);
            ulong friendlyPieces = position.GetAllPieces(isWhite);

            while (knights != 0)
            {
                int fromSquare = Bitboard.PopLSB(ref knights);
                ulong attacks = Bitboard.KnightAttacks(fromSquare) & ~friendlyPieces;
                
                while (attacks != 0)
                {
                    int toSquare = Bitboard.PopLSB(ref attacks);
                    var (capturedPiece, _) = position.GetPieceAt(toSquare);
                    AddMove(fromSquare, toSquare, PieceType.Knight, capturedPiece);
                }
            }
        }

        private void GenerateBishopMoves(bool isWhite)
        {
            ulong bishops = position.GetPieces(PieceType.Bishop, isWhite);
            ulong friendlyPieces = position.GetAllPieces(isWhite);

            while (bishops != 0)
            {
                int fromSquare = Bitboard.PopLSB(ref bishops);
                ulong attacks = MagicBitboards.GetBishopAttacks(fromSquare, position.AllPieces) & ~friendlyPieces;
                
                while (attacks != 0)
                {
                    int toSquare = Bitboard.PopLSB(ref attacks);
                    var (capturedPiece, _) = position.GetPieceAt(toSquare);
                    AddMove(fromSquare, toSquare, PieceType.Bishop, capturedPiece);
                }
            }
        }

        private void GenerateRookMoves(bool isWhite)
        {
            ulong rooks = position.GetPieces(PieceType.Rook, isWhite);
            ulong friendlyPieces = position.GetAllPieces(isWhite);

            while (rooks != 0)
            {
                int fromSquare = Bitboard.PopLSB(ref rooks);
                ulong attacks = MagicBitboards.GetRookAttacks(fromSquare, position.AllPieces) & ~friendlyPieces;
                
                while (attacks != 0)
                {
                    int toSquare = Bitboard.PopLSB(ref attacks);
                    var (capturedPiece, _) = position.GetPieceAt(toSquare);
                    AddMove(fromSquare, toSquare, PieceType.Rook, capturedPiece);
                }
            }
        }

        private void GenerateQueenMoves(bool isWhite)
        {
            ulong queens = position.GetPieces(PieceType.Queen, isWhite);
            ulong friendlyPieces = position.GetAllPieces(isWhite);

            while (queens != 0)
            {
                int fromSquare = Bitboard.PopLSB(ref queens);
                ulong attacks = MagicBitboards.GetQueenAttacks(fromSquare, position.AllPieces) & ~friendlyPieces;
                
                while (attacks != 0)
                {
                    int toSquare = Bitboard.PopLSB(ref attacks);
                    var (capturedPiece, _) = position.GetPieceAt(toSquare);
                    AddMove(fromSquare, toSquare, PieceType.Queen, capturedPiece);
                }
            }
        }

        private void GenerateKingMoves(bool isWhite)
        {
            int kingSquare = position.GetKingSquare(isWhite);
            if (kingSquare == -1) return;
            
            ulong attacks = Bitboard.KingAttacks(kingSquare) & ~position.GetAllPieces(isWhite);
            
            while (attacks != 0)
            {
                int toSquare = Bitboard.PopLSB(ref attacks);
                var (capturedPiece, _) = position.GetPieceAt(toSquare);
                AddMove(kingSquare, toSquare, PieceType.King, capturedPiece);
            }
        }

        private void GenerateCastlingMoves(bool isWhite)
        {
            if (position.IsInCheck()) return; // Can't castle when in check

            if (isWhite)
            {
                // White kingside castling
                if (position.WhiteCanCastleKingside && 
                    (position.AllPieces & Bitboard.WhiteKingsideCastleSquares) == 0 &&
                    !position.IsSquareAttacked(5, false) && // f1
                    !position.IsSquareAttacked(6, false))   // g1
                {
                    AddMove(4, 6, PieceType.King, PieceType.None, MoveFlag.Castling); // e1-g1
                }

                // White queenside castling
                if (position.WhiteCanCastleQueenside && 
                    (position.AllPieces & Bitboard.WhiteQueensideCastleSquares) == 0 &&
                    !position.IsSquareAttacked(3, false) && // d1
                    !position.IsSquareAttacked(2, false))   // c1
                {
                    AddMove(4, 2, PieceType.King, PieceType.None, MoveFlag.Castling); // e1-c1
                }
            }
            else
            {
                // Black kingside castling
                if (position.BlackCanCastleKingside && 
                    (position.AllPieces & Bitboard.BlackKingsideCastleSquares) == 0 &&
                    !position.IsSquareAttacked(61, true) && // f8
                    !position.IsSquareAttacked(62, true))   // g8
                {
                    AddMove(60, 62, PieceType.King, PieceType.None, MoveFlag.Castling); // e8-g8
                }

                // Black queenside castling
                if (position.BlackCanCastleQueenside && 
                    (position.AllPieces & Bitboard.BlackQueensideCastleSquares) == 0 &&
                    !position.IsSquareAttacked(59, true) && // d8
                    !position.IsSquareAttacked(58, true))   // c8
                {
                    AddMove(60, 58, PieceType.King, PieceType.None, MoveFlag.Castling); // e8-c8
                }
            }
        }

        private void AddMove(int fromSquare, int toSquare, PieceType movePiece, 
                           PieceType capturePiece = PieceType.None, MoveFlag flag = MoveFlag.None)
        {
            moves.Add(new Move(new Square(fromSquare), new Square(toSquare), 
                              movePiece, capturePiece, PieceType.None, flag));
        }

        private void AddPromotionMoves(int fromSquare, int toSquare, PieceType capturePiece = PieceType.None)
        {
            PieceType[] promotionPieces = { PieceType.Queen, PieceType.Rook, PieceType.Bishop, PieceType.Knight };
            foreach (var promotionPiece in promotionPieces)
            {
                moves.Add(new Move(new Square(fromSquare), new Square(toSquare), 
                                  PieceType.Pawn, capturePiece, promotionPiece));
            }
        }

        private Move[] FilterLegalMoves()
        {
            var legalMoves = new List<Move>();
            
            foreach (var move in moves)
            {
                if (IsLegalMove(move))
                {
                    legalMoves.Add(move);
                }
            }
            
            return legalMoves.ToArray();
        }

        /// <summary>
        /// Check if a move is legal (doesn't leave king in check)
        /// </summary>
        public bool IsLegalMove(BitboardPosition pos, Move move)
        {
            // Set position for this check
            position = pos;
            
            // Remember who is making the move (before switching turns)
            bool movingPlayerIsWhite = pos.IsWhiteToMove;
            
            // Make a copy of the position to test the move
            var testPosition = position;
            
            // Make the move
            MakeMove(ref testPosition, move);
            
            // Check if the king of the side that just moved is in check
            // After MakeMove, turns have been switched, so we check the king of the side that made the move
            bool isInCheck = testPosition.IsSquareAttacked(
                testPosition.GetKingSquare(movingPlayerIsWhite), 
                !movingPlayerIsWhite);
            
            return !isInCheck;
        }

        /// <summary>
        /// Check if a move is legal (doesn't leave king in check) - overload for backwards compatibility
        /// </summary>
        public bool IsLegalMove(Move move)
        {
            return IsLegalMove(position, move);
        }

        /// <summary>
        /// Apply a move to a position (for legal move checking)
        /// </summary>
        private void MakeMove(ref BitboardPosition pos, Move move)
        {
            int fromSquare = move.StartSquare.Index;
            int toSquare = move.TargetSquare.Index;
            
            // Handle special moves
            switch (move.Flag)
            {
                case MoveFlag.EnPassant:
                    // Remove the captured pawn
                    int capturedPawnSquare = pos.IsWhiteToMove ? toSquare - 8 : toSquare + 8;
                    pos.RemovePiece(capturedPawnSquare);
                    break;
                    
                case MoveFlag.Castling:
                    // Move the rook
                    if (toSquare == 6) // Kingside castling (white)
                    {
                        pos.MovePiece(7, 5); // h1 to f1
                    }
                    else if (toSquare == 2) // Queenside castling (white)
                    {
                        pos.MovePiece(0, 3); // a1 to d1
                    }
                    else if (toSquare == 62) // Kingside castling (black)
                    {
                        pos.MovePiece(63, 61); // h8 to f8
                    }
                    else if (toSquare == 58) // Queenside castling (black)
                    {
                        pos.MovePiece(56, 59); // a8 to d8
                    }
                    break;
            }
            
            // Move the piece
            pos.MovePiece(fromSquare, toSquare);
            
            // Handle promotion
            if (move.IsPromotion)
            {
                pos.RemovePiece(toSquare);
                pos.SetPiece(toSquare, move.PromotionPieceType, pos.IsWhiteToMove);
            }
            
            // Switch turns for check testing
            pos.IsWhiteToMove = !pos.IsWhiteToMove;
        }
    }
}
