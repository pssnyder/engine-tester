using System;
using System.Collections.Generic;

namespace C0BR4ChessEngine.Core.V28
{
    /// <summary>
    /// Clean, simple move generator for C0BR4 v2.8
    /// Uses simple ray-based attack generation - prioritizes correctness over speed
    /// Built from scratch to eliminate all legacy magic bitboard issues
    /// </summary>
    public static class CleanMoveGenerator
    {
        /// <summary>
        /// Generate all legal moves for the current position
        /// </summary>
        public static List<CleanMove> GenerateLegalMoves(CleanBoardState boardState)
        {
            var pseudoLegalMoves = GeneratePseudoLegalMoves(boardState);
            var legalMoves = new List<CleanMove>();
            
            foreach (var move in pseudoLegalMoves)
            {
                if (IsLegalMove(move, boardState))
                {
                    legalMoves.Add(move);
                }
            }
            
            return legalMoves;
        }
        
        /// <summary>
        /// Generate all pseudo-legal moves (may leave king in check)
        /// </summary>
        public static List<CleanMove> GeneratePseudoLegalMoves(CleanBoardState boardState)
        {
            var moves = new List<CleanMove>();
            
            bool isWhite = boardState.WhiteToMove;
            ulong friendlyPieces = isWhite ? boardState.WhitePieces : boardState.BlackPieces;
            ulong enemyPieces = isWhite ? boardState.BlackPieces : boardState.WhitePieces;
            
            // Generate moves for each piece type
            if (isWhite)
            {
                GeneratePawnMoves(moves, boardState.WhitePawns, true, boardState);
                GenerateRookMoves(moves, boardState.WhiteRooks, true, boardState);
                GenerateKnightMoves(moves, boardState.WhiteKnights, true, boardState);
                GenerateBishopMoves(moves, boardState.WhiteBishops, true, boardState);
                GenerateQueenMoves(moves, boardState.WhiteQueens, true, boardState);
                GenerateKingMoves(moves, boardState.WhiteKing, true, boardState);
            }
            else
            {
                GeneratePawnMoves(moves, boardState.BlackPawns, false, boardState);
                GenerateRookMoves(moves, boardState.BlackRooks, false, boardState);
                GenerateKnightMoves(moves, boardState.BlackKnights, false, boardState);
                GenerateBishopMoves(moves, boardState.BlackBishops, false, boardState);
                GenerateQueenMoves(moves, boardState.BlackQueens, false, boardState);
                GenerateKingMoves(moves, boardState.BlackKing, false, boardState);
            }
            
            return moves;
        }
        
        /// <summary>
        /// Check if a move is legal (doesn't leave own king in check)
        /// </summary>
        public static bool IsLegalMove(CleanMove move, CleanBoardState boardState)
        {
            // Make the move on a copy of the board
            var testBoard = boardState;
            MakeMove(ref testBoard, move);
            
            // Check if our king is in check after the move
            bool isWhite = move.IsWhite;
            int kingSquare = GetKingSquare(testBoard, isWhite);
            
            if (kingSquare == -1)
                return false; // No king found - invalid position
                
            return !IsSquareAttacked(testBoard, kingSquare, !isWhite);
        }
        
        /// <summary>
        /// Make a move on the board (modifies the board state)
        /// </summary>
        public static void MakeMove(ref CleanBoardState boardState, CleanMove move)
        {
            // Remove piece from source square
            boardState.RemovePiece(move.FromSquare);
            
            // Handle captures
            if (move.CapturedPieceType > 0 && !move.IsEnPassant)
            {
                boardState.RemovePiece(move.ToSquare);
            }
            
            // Handle en passant capture
            if (move.IsEnPassant)
            {
                int capturedPawnSquare = move.IsWhite ? move.ToSquare - 8 : move.ToSquare + 8;
                boardState.RemovePiece(capturedPawnSquare);
            }
            
            // Handle promotion
            int finalPieceType = move.PromotionPieceType > 0 ? move.PromotionPieceType : move.PieceType;
            
            // Add piece to destination square
            boardState.AddPiece(move.ToSquare, finalPieceType, move.IsWhite);
            
            // Handle castling - move the rook
            if (move.IsCastling)
            {
                int kingFile = CleanBitboard.GetFile(move.ToSquare);
                int rank = move.IsWhite ? 0 : 7;
                
                if (kingFile == 6) // Kingside
                {
                    int rookFrom = CleanBitboard.GetSquare(7, rank);
                    int rookTo = CleanBitboard.GetSquare(5, rank);
                    boardState.RemovePiece(rookFrom);
                    boardState.AddPiece(rookTo, 2, move.IsWhite); // Rook
                }
                else if (kingFile == 2) // Queenside
                {
                    int rookFrom = CleanBitboard.GetSquare(0, rank);
                    int rookTo = CleanBitboard.GetSquare(3, rank);
                    boardState.RemovePiece(rookFrom);
                    boardState.AddPiece(rookTo, 2, move.IsWhite); // Rook
                }
            }
            
            // Update castling rights
            UpdateCastlingRights(ref boardState, move);
            
            // Update en passant square
            UpdateEnPassantSquare(ref boardState, move);
            
            // Update move counters
            if (move.CapturedPieceType > 0 || move.PieceType == 1) // Capture or pawn move
            {
                boardState.HalfmoveClock = 0;
            }
            else
            {
                boardState.HalfmoveClock++;
            }
            
            if (!move.IsWhite) // After black's move
            {
                boardState.FullmoveNumber++;
            }
            
            // Switch turn
            boardState.WhiteToMove = !boardState.WhiteToMove;
            
            // Update occupancy bitboards
            boardState.UpdateOccupancyBitboards();
        }
        
        /// <summary>
        /// Check if a square is attacked by the specified color
        /// </summary>
        public static bool IsSquareAttacked(CleanBoardState boardState, int square, bool byWhite)
        {
            // Check pawn attacks
            ulong pawnAttacks = CleanBitboard.GetPawnAttacks(square, !byWhite);
            ulong attackingPawns = byWhite ? boardState.WhitePawns : boardState.BlackPawns;
            if ((pawnAttacks & attackingPawns) != 0)
                return true;
            
            // Check knight attacks
            ulong knightAttacks = CleanBitboard.GetKnightAttacks(square);
            ulong attackingKnights = byWhite ? boardState.WhiteKnights : boardState.BlackKnights;
            if ((knightAttacks & attackingKnights) != 0)
                return true;
            
            // Check bishop/queen diagonal attacks
            ulong bishopAttacks = CleanBitboard.GetBishopAttacks(square, boardState.AllPieces);
            ulong attackingBishops = byWhite ? (boardState.WhiteBishops | boardState.WhiteQueens) : 
                                              (boardState.BlackBishops | boardState.BlackQueens);
            if ((bishopAttacks & attackingBishops) != 0)
                return true;
            
            // Check rook/queen horizontal/vertical attacks
            ulong rookAttacks = CleanBitboard.GetRookAttacks(square, boardState.AllPieces);
            ulong attackingRooks = byWhite ? (boardState.WhiteRooks | boardState.WhiteQueens) : 
                                            (boardState.BlackRooks | boardState.BlackQueens);
            if ((rookAttacks & attackingRooks) != 0)
                return true;
            
            // Check king attacks
            ulong kingAttacks = CleanBitboard.GetKingAttacks(square);
            ulong attackingKing = byWhite ? boardState.WhiteKing : boardState.BlackKing;
            if ((kingAttacks & attackingKing) != 0)
                return true;
            
            return false;
        }
        
        /// <summary>
        /// Get the square of the specified king
        /// </summary>
        private static int GetKingSquare(CleanBoardState boardState, bool isWhite)
        {
            ulong kingBitboard = isWhite ? boardState.WhiteKing : boardState.BlackKing;
            
            if (kingBitboard == 0)
                return -1;
                
            return System.Numerics.BitOperations.TrailingZeroCount(kingBitboard);
        }
        
        /// <summary>
        /// Generate pawn moves
        /// </summary>
        private static void GeneratePawnMoves(List<CleanMove> moves, ulong pawns, bool isWhite, CleanBoardState boardState)
        {
            int direction = isWhite ? 8 : -8;
            int startRank = isWhite ? 1 : 6;
            int promotionRank = isWhite ? 7 : 0;
            
            ulong pawnsCopy = pawns;
            while (pawnsCopy != 0)
            {
                int fromSquare = CleanBitboard.PopLSB(ref pawnsCopy);
                int fromRank = CleanBitboard.GetRank(fromSquare);
                int fromFile = CleanBitboard.GetFile(fromSquare);
                
                // Forward moves
                int oneSquareForward = fromSquare + direction;
                if (oneSquareForward >= 0 && oneSquareForward <= 63 && boardState.IsEmpty(oneSquareForward))
                {
                    if (CleanBitboard.GetRank(oneSquareForward) == promotionRank)
                    {
                        // Promotion
                        moves.Add(CleanMove.CreatePromotion(fromSquare, oneSquareForward, isWhite, 5)); // Queen
                        moves.Add(CleanMove.CreatePromotion(fromSquare, oneSquareForward, isWhite, 2)); // Rook
                        moves.Add(CleanMove.CreatePromotion(fromSquare, oneSquareForward, isWhite, 4)); // Bishop
                        moves.Add(CleanMove.CreatePromotion(fromSquare, oneSquareForward, isWhite, 3)); // Knight
                    }
                    else
                    {
                        moves.Add(CleanMove.Create(fromSquare, oneSquareForward, 1, isWhite));
                        
                        // Two squares forward from starting position
                        if (fromRank == startRank)
                        {
                            int twoSquaresForward = fromSquare + 2 * direction;
                            if (twoSquaresForward >= 0 && twoSquaresForward <= 63 && boardState.IsEmpty(twoSquaresForward))
                            {
                                moves.Add(CleanMove.Create(fromSquare, twoSquaresForward, 1, isWhite));
                            }
                        }
                    }
                }
                
                // Captures
                int[] captureOffsets = isWhite ? new[] { 7, 9 } : new[] { -9, -7 };
                foreach (int offset in captureOffsets)
                {
                    int toSquare = fromSquare + offset;
                    if (toSquare >= 0 && toSquare <= 63)
                    {
                        int toFile = CleanBitboard.GetFile(toSquare);
                        
                        // Check file wrapping
                        if (Math.Abs(fromFile - toFile) == 1)
                        {
                            // Regular capture
                            if (!boardState.IsEmpty(toSquare) && 
                                ((isWhite && boardState.IsBlackPiece(toSquare)) || 
                                 (!isWhite && boardState.IsWhitePiece(toSquare))))
                            {
                                int capturedPieceType = boardState.GetPieceTypeAt(toSquare);
                                
                                if (CleanBitboard.GetRank(toSquare) == promotionRank)
                                {
                                    // Capture with promotion
                                    moves.Add(CleanMove.CreatePromotion(fromSquare, toSquare, isWhite, 5, capturedPieceType));
                                    moves.Add(CleanMove.CreatePromotion(fromSquare, toSquare, isWhite, 2, capturedPieceType));
                                    moves.Add(CleanMove.CreatePromotion(fromSquare, toSquare, isWhite, 4, capturedPieceType));
                                    moves.Add(CleanMove.CreatePromotion(fromSquare, toSquare, isWhite, 3, capturedPieceType));
                                }
                                else
                                {
                                    moves.Add(CleanMove.CreateCapture(fromSquare, toSquare, 1, isWhite, capturedPieceType));
                                }
                            }
                            // En passant capture
                            else if (toSquare == boardState.EnPassantSquare)
                            {
                                moves.Add(CleanMove.CreateEnPassant(fromSquare, toSquare, isWhite));
                            }
                        }
                    }
                }
            }
        }
        
        /// <summary>
        /// Generate rook moves
        /// </summary>
        private static void GenerateRookMoves(List<CleanMove> moves, ulong rooks, bool isWhite, CleanBoardState boardState)
        {
            ulong rooksCopy = rooks;
            while (rooksCopy != 0)
            {
                int fromSquare = CleanBitboard.PopLSB(ref rooksCopy);
                ulong attacks = CleanBitboard.GetRookAttacks(fromSquare, boardState.AllPieces);
                
                GenerateMovesFromAttacks(moves, fromSquare, 2, isWhite, attacks, boardState);
            }
        }
        
        /// <summary>
        /// Generate knight moves
        /// </summary>
        private static void GenerateKnightMoves(List<CleanMove> moves, ulong knights, bool isWhite, CleanBoardState boardState)
        {
            ulong knightsCopy = knights;
            while (knightsCopy != 0)
            {
                int fromSquare = CleanBitboard.PopLSB(ref knightsCopy);
                ulong attacks = CleanBitboard.GetKnightAttacks(fromSquare);
                
                GenerateMovesFromAttacks(moves, fromSquare, 3, isWhite, attacks, boardState);
            }
        }
        
        /// <summary>
        /// Generate bishop moves
        /// </summary>
        private static void GenerateBishopMoves(List<CleanMove> moves, ulong bishops, bool isWhite, CleanBoardState boardState)
        {
            ulong bishopsCopy = bishops;
            while (bishopsCopy != 0)
            {
                int fromSquare = CleanBitboard.PopLSB(ref bishopsCopy);
                ulong attacks = CleanBitboard.GetBishopAttacks(fromSquare, boardState.AllPieces);
                
                GenerateMovesFromAttacks(moves, fromSquare, 4, isWhite, attacks, boardState);
            }
        }
        
        /// <summary>
        /// Generate queen moves
        /// </summary>
        private static void GenerateQueenMoves(List<CleanMove> moves, ulong queens, bool isWhite, CleanBoardState boardState)
        {
            ulong queensCopy = queens;
            while (queensCopy != 0)
            {
                int fromSquare = CleanBitboard.PopLSB(ref queensCopy);
                ulong attacks = CleanBitboard.GetQueenAttacks(fromSquare, boardState.AllPieces);
                
                GenerateMovesFromAttacks(moves, fromSquare, 5, isWhite, attacks, boardState);
            }
        }
        
        /// <summary>
        /// Generate king moves (including castling)
        /// </summary>
        private static void GenerateKingMoves(List<CleanMove> moves, ulong kings, bool isWhite, CleanBoardState boardState)
        {
            if (kings == 0)
                return;
                
            int fromSquare = System.Numerics.BitOperations.TrailingZeroCount(kings);
            ulong attacks = CleanBitboard.GetKingAttacks(fromSquare);
            
            GenerateMovesFromAttacks(moves, fromSquare, 6, isWhite, attacks, boardState);
            
            // Generate castling moves
            GenerateCastlingMoves(moves, fromSquare, isWhite, boardState);
        }
        
        /// <summary>
        /// Generate moves from attack bitboard
        /// </summary>
        private static void GenerateMovesFromAttacks(List<CleanMove> moves, int fromSquare, int pieceType, bool isWhite, ulong attacks, CleanBoardState boardState)
        {
            // Remove friendly pieces from attacks
            ulong friendlyPieces = isWhite ? boardState.WhitePieces : boardState.BlackPieces;
            attacks &= ~friendlyPieces;
            
            while (attacks != 0)
            {
                int toSquare = CleanBitboard.PopLSB(ref attacks);
                
                if (boardState.IsEmpty(toSquare))
                {
                    moves.Add(CleanMove.Create(fromSquare, toSquare, pieceType, isWhite));
                }
                else
                {
                    int capturedPieceType = boardState.GetPieceTypeAt(toSquare);
                    moves.Add(CleanMove.CreateCapture(fromSquare, toSquare, pieceType, isWhite, capturedPieceType));
                }
            }
        }
        
        /// <summary>
        /// Generate castling moves
        /// </summary>
        private static void GenerateCastlingMoves(List<CleanMove> moves, int kingSquare, bool isWhite, CleanBoardState boardState)
        {
            if (IsSquareAttacked(boardState, kingSquare, !isWhite))
                return; // Can't castle when in check
            
            int rank = isWhite ? 0 : 7;
            
            // Kingside castling
            if ((isWhite && boardState.WhiteCanCastleKingside) || (!isWhite && boardState.BlackCanCastleKingside))
            {
                int f1 = CleanBitboard.GetSquare(5, rank);
                int g1 = CleanBitboard.GetSquare(6, rank);
                int h1 = CleanBitboard.GetSquare(7, rank);
                
                if (boardState.IsEmpty(f1) && boardState.IsEmpty(g1) &&
                    !IsSquareAttacked(boardState, f1, !isWhite) &&
                    !IsSquareAttacked(boardState, g1, !isWhite))
                {
                    moves.Add(CleanMove.CreateCastling(kingSquare, g1, isWhite));
                }
            }
            
            // Queenside castling
            if ((isWhite && boardState.WhiteCanCastleQueenside) || (!isWhite && boardState.BlackCanCastleQueenside))
            {
                int d1 = CleanBitboard.GetSquare(3, rank);
                int c1 = CleanBitboard.GetSquare(2, rank);
                int b1 = CleanBitboard.GetSquare(1, rank);
                
                if (boardState.IsEmpty(d1) && boardState.IsEmpty(c1) && boardState.IsEmpty(b1) &&
                    !IsSquareAttacked(boardState, d1, !isWhite) &&
                    !IsSquareAttacked(boardState, c1, !isWhite))
                {
                    moves.Add(CleanMove.CreateCastling(kingSquare, c1, isWhite));
                }
            }
        }
        
        /// <summary>
        /// Update castling rights after a move
        /// </summary>
        private static void UpdateCastlingRights(ref CleanBoardState boardState, CleanMove move)
        {
            // King moves remove all castling rights
            if (move.PieceType == 6)
            {
                if (move.IsWhite)
                {
                    boardState.WhiteCanCastleKingside = false;
                    boardState.WhiteCanCastleQueenside = false;
                }
                else
                {
                    boardState.BlackCanCastleKingside = false;
                    boardState.BlackCanCastleQueenside = false;
                }
            }
            
            // Rook moves or captures remove specific castling rights
            CheckRookCastlingRights(ref boardState, move.FromSquare);
            CheckRookCastlingRights(ref boardState, move.ToSquare);
        }
        
        /// <summary>
        /// Check if a rook move or capture affects castling rights
        /// </summary>
        private static void CheckRookCastlingRights(ref CleanBoardState boardState, int square)
        {
            switch (square)
            {
                case 0: // a1
                    boardState.WhiteCanCastleQueenside = false;
                    break;
                case 7: // h1
                    boardState.WhiteCanCastleKingside = false;
                    break;
                case 56: // a8
                    boardState.BlackCanCastleQueenside = false;
                    break;
                case 63: // h8
                    boardState.BlackCanCastleKingside = false;
                    break;
            }
        }
        
        /// <summary>
        /// Update en passant square after a move
        /// </summary>
        private static void UpdateEnPassantSquare(ref CleanBoardState boardState, CleanMove move)
        {
            boardState.EnPassantSquare = -1;
            
            // Two-square pawn move sets en passant square
            if (move.PieceType == 1 && Math.Abs(move.ToSquare - move.FromSquare) == 16)
            {
                boardState.EnPassantSquare = (move.FromSquare + move.ToSquare) / 2;
            }
        }
    }
}
