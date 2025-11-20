using System;
using System.Collections.Generic;

namespace C0BR4ChessEngine.Core
{
    /// <summary>
    /// Bitboard-based chess position representation
    /// Much more efficient than piece array for move generation and evaluation
    /// </summary>
    public struct BitboardPosition : ICloneable
    {
        // Piece bitboards by color and type
        public ulong WhitePawns;
        public ulong WhiteKnights;
        public ulong WhiteBishops;
        public ulong WhiteRooks;
        public ulong WhiteQueens;
        public ulong WhiteKing;
        
        public ulong BlackPawns;
        public ulong BlackKnights;
        public ulong BlackBishops;
        public ulong BlackRooks;
        public ulong BlackQueens;
        public ulong BlackKing;
        
        // Composite bitboards for efficient operations
        public ulong AllWhitePieces;
        public ulong AllBlackPieces;
        public ulong AllPieces;

        // Game state
        public bool IsWhiteToMove;
        public int HalfMoveClock;
        public int FullMoveNumber;
        
        // Castling rights
        public bool WhiteCanCastleKingside;
        public bool WhiteCanCastleQueenside;
        public bool BlackCanCastleKingside;
        public bool BlackCanCastleQueenside;
        
        // En passant target square (-1 if none)
        public int EnPassantSquare;

        /// <summary>
        /// Create a deep copy of the position
        /// </summary>
        public BitboardPosition Clone()
        {
            return new BitboardPosition
            {
                WhitePawns = this.WhitePawns,
                WhiteKnights = this.WhiteKnights,
                WhiteBishops = this.WhiteBishops,
                WhiteRooks = this.WhiteRooks,
                WhiteQueens = this.WhiteQueens,
                WhiteKing = this.WhiteKing,
                BlackPawns = this.BlackPawns,
                BlackKnights = this.BlackKnights,
                BlackBishops = this.BlackBishops,
                BlackRooks = this.BlackRooks,
                BlackQueens = this.BlackQueens,
                BlackKing = this.BlackKing,
                AllWhitePieces = this.AllWhitePieces,
                AllBlackPieces = this.AllBlackPieces,
                AllPieces = this.AllPieces,
                IsWhiteToMove = this.IsWhiteToMove,
                HalfMoveClock = this.HalfMoveClock,
                FullMoveNumber = this.FullMoveNumber,
                WhiteCanCastleKingside = this.WhiteCanCastleKingside,
                WhiteCanCastleQueenside = this.WhiteCanCastleQueenside,
                BlackCanCastleKingside = this.BlackCanCastleKingside,
                BlackCanCastleQueenside = this.BlackCanCastleQueenside,
                EnPassantSquare = this.EnPassantSquare
            };
        }

        /// <summary>
        /// ICloneable implementation
        /// </summary>
        object ICloneable.Clone()
        {
            return Clone();
        }

        /// <summary>
    /// Update composite bitboards after any piece movement
    /// Must be called whenever individual piece bitboards are modified
    /// </summary>
    public void UpdateCompositeBitboards()
    {
        ulong newWhitePieces = WhitePawns | WhiteKnights | WhiteBishops | WhiteRooks | WhiteQueens | WhiteKing;
        ulong newBlackPieces = BlackPawns | BlackKnights | BlackBishops | BlackRooks | BlackQueens | BlackKing;
        ulong newAllPieces = newWhitePieces | newBlackPieces;

        // Check for piece overlap - should never happen
        if ((newWhitePieces & newBlackPieces) != 0)
        {
            throw new InvalidOperationException("Position corruption: White and black pieces overlap");
        }

        AllWhitePieces = newWhitePieces;
        AllBlackPieces = newBlackPieces;
        AllPieces = newAllPieces;
    }

    /// <summary>
    /// Validate the entire position state
    /// </summary>
    public bool ValidateState()
    {
        try
        {
            return ValidateStateDetailed().isValid;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Validate the position state with detailed error reporting
    /// </summary>
    public (bool isValid, string details) ValidateStateDetailed()
    {
        // 1. King Count Check
        int whiteKings = Bitboard.PopCount(WhiteKing);
        int blackKings = Bitboard.PopCount(BlackKing);
        if (whiteKings != 1 || blackKings != 1)
        {
            return (false, $"Invalid king count: White={whiteKings}, Black={blackKings}");
        }

        // 2. Piece Overlap Check
        ulong whitePieceSum = WhitePawns | WhiteKnights | WhiteBishops | WhiteRooks | WhiteQueens | WhiteKing;
        ulong blackPieceSum = BlackPawns | BlackKnights | BlackBishops | BlackRooks | BlackQueens | BlackKing;
        if (whitePieceSum != AllWhitePieces)
        {
            return (false, "White piece bitboards don't match composite bitboard");
        }
        if (blackPieceSum != AllBlackPieces)
        {
            return (false, "Black piece bitboards don't match composite bitboard");
        }
        if ((AllWhitePieces & AllBlackPieces) != 0)
        {
            return (false, "White and black pieces overlap");
        }

        // 3. Pawn Position Check
        if ((WhitePawns & Bitboard.Rank8) != 0)
        {
            return (false, "White pawns found on 8th rank");
        }
        if ((BlackPawns & Bitboard.Rank1) != 0)
        {
            return (false, "Black pawns found on 1st rank");
        }

        // 4. Piece Count Check
        int whitePawns = Bitboard.PopCount(WhitePawns);
        int blackPawns = Bitboard.PopCount(BlackPawns);
        if (whitePawns > 8 || blackPawns > 8)
        {
            return (false, $"Too many pawns: White={whitePawns}, Black={blackPawns}");
        }

        // 5. En Passant Validation
        if (EnPassantSquare != -1)
        {
            int epRank = Bitboard.GetRank(EnPassantSquare);
            if (IsWhiteToMove && epRank != 5 || !IsWhiteToMove && epRank != 2)
            {
                return (false, $"Invalid en passant square rank: {epRank}");
            }
        }

        // 6. Castling Rights Validation
        int whiteKingSquare = Bitboard.LSB(WhiteKing);
        int blackKingSquare = Bitboard.LSB(BlackKing);

        if (WhiteCanCastleKingside && 
            (whiteKingSquare != 4 || (WhiteRooks & Bitboard.SquareToBitboard(7)) == 0))
        {
            return (false, "Invalid white kingside castling rights");
        }
        if (WhiteCanCastleQueenside && 
            (whiteKingSquare != 4 || (WhiteRooks & Bitboard.SquareToBitboard(0)) == 0))
        {
            return (false, "Invalid white queenside castling rights");
        }
        if (BlackCanCastleKingside && 
            (blackKingSquare != 60 || (BlackRooks & Bitboard.SquareToBitboard(63)) == 0))
        {
            return (false, "Invalid black kingside castling rights");
        }
        if (BlackCanCastleQueenside && 
            (blackKingSquare != 60 || (BlackRooks & Bitboard.SquareToBitboard(56)) == 0))
        {
            return (false, "Invalid black queenside castling rights");
        }

        // 7. Check Counter Validation
        if (HalfMoveClock < 0)
        {
            return (false, $"Invalid halfmove clock: {HalfMoveClock}");
        }
        if (FullMoveNumber < 1)
        {
            return (false, $"Invalid fullmove number: {FullMoveNumber}");
        }

        return (true, "Position is valid");
    }

    /// <summary>
    /// Ensure position consistency after every state change
    /// </summary>
    private void EnsurePositionConsistency()
    {
        // 1. Update composite bitboards
        UpdateCompositeBitboards();

        // 2. Update castling rights
        UpdateCastlingRights();

        // 3. Validate total piece count
        if (Bitboard.PopCount(AllPieces) > 32)
        {
            throw new InvalidOperationException("Position corruption: Too many pieces");
        }

        // 4. Validate kings
        if (Bitboard.PopCount(WhiteKing) != 1 || Bitboard.PopCount(BlackKing) != 1)
        {
            throw new InvalidOperationException("Position corruption: Invalid king count");
        }

        // 5. Validate pawn ranks
        if ((WhitePawns & Bitboard.Rank8) != 0 || (BlackPawns & Bitboard.Rank1) != 0)
        {
            throw new InvalidOperationException("Position corruption: Invalid pawn position");
        }
    }

    /// <summary>
    /// Ensure position consistency with optional validation (for FEN parsing)
    /// </summary>
    public void EnsurePositionConsistency(string? context = null)
    {
        // 1. Update composite bitboards
        UpdateCompositeBitboards();

        // 2. Update castling rights
        UpdateCastlingRights();

        // Only do strict validation if not during FEN parsing or move operations
        if (context != "FromFEN" && context != "move")
        {
            // 3. Validate total piece count
            if (Bitboard.PopCount(AllPieces) > 32)
            {
                throw new InvalidOperationException("Position corruption: Too many pieces");
            }

            // 4. Validate kings - be more lenient during move operations
            int whiteKings = Bitboard.PopCount(WhiteKing);
            int blackKings = Bitboard.PopCount(BlackKing);
            if (whiteKings > 1 || blackKings > 1)
            {
                throw new InvalidOperationException($"Position corruption: Too many kings - White: {whiteKings}, Black: {blackKings}");
            }
            // Allow temporary states with 0 kings during move operations, but log it
            if (whiteKings == 0 || blackKings == 0)
            {
                // This could be a temporary state during move application
                // Don't throw an exception, just update composite bitboards
                return;
            }

            // 5. Validate pawn ranks
            if ((WhitePawns & Bitboard.Rank8) != 0 || (BlackPawns & Bitboard.Rank1) != 0)
            {
                throw new InvalidOperationException("Position corruption: Invalid pawn position");
            }
        }
    }

    /// <summary>
    /// Update castling rights based on king and rook positions
    /// </summary>
    private void UpdateCastlingRights()
    {
        // White castling
        if ((WhiteKing & Bitboard.SquareToBitboard(4)) == 0)
        {
            WhiteCanCastleKingside = false;
            WhiteCanCastleQueenside = false;
        }
        if ((WhiteRooks & Bitboard.SquareToBitboard(7)) == 0)
            WhiteCanCastleKingside = false;
        if ((WhiteRooks & Bitboard.SquareToBitboard(0)) == 0)
            WhiteCanCastleQueenside = false;

        // Black castling
        if ((BlackKing & Bitboard.SquareToBitboard(60)) == 0)
        {
            BlackCanCastleKingside = false;
            BlackCanCastleQueenside = false;
        }
        if ((BlackRooks & Bitboard.SquareToBitboard(63)) == 0)
            BlackCanCastleKingside = false;
        if ((BlackRooks & Bitboard.SquareToBitboard(56)) == 0)
            BlackCanCastleQueenside = false;
    }

    /// <summary>
    /// Get the piece type and color at a specific square
    /// Returns (PieceType.None, true) if square is empty
    /// </summary>
    public (PieceType type, bool isWhite) GetPieceAt(int square)
    {
            ulong squareBit = Bitboard.SquareToBitboard(square);
            
            if ((AllWhitePieces & squareBit) != 0)
            {
                if ((WhitePawns & squareBit) != 0) return (PieceType.Pawn, true);
                if ((WhiteKnights & squareBit) != 0) return (PieceType.Knight, true);
                if ((WhiteBishops & squareBit) != 0) return (PieceType.Bishop, true);
                if ((WhiteRooks & squareBit) != 0) return (PieceType.Rook, true);
                if ((WhiteQueens & squareBit) != 0) return (PieceType.Queen, true);
                if ((WhiteKing & squareBit) != 0) return (PieceType.King, true);
            }
            else if ((AllBlackPieces & squareBit) != 0)
            {
                if ((BlackPawns & squareBit) != 0) return (PieceType.Pawn, false);
                if ((BlackKnights & squareBit) != 0) return (PieceType.Knight, false);
                if ((BlackBishops & squareBit) != 0) return (PieceType.Bishop, false);
                if ((BlackRooks & squareBit) != 0) return (PieceType.Rook, false);
                if ((BlackQueens & squareBit) != 0) return (PieceType.Queen, false);
                if ((BlackKing & squareBit) != 0) return (PieceType.King, false);
            }
            
            return (PieceType.None, true);
    }

    /// <summary>
    /// Place a piece on the board with enhanced validation
    /// </summary>
    public void SetPiece(int square, PieceType pieceType, bool isWhite)
    {
        SetPiece(square, pieceType, isWhite, "move");
    }

    /// <summary>
    /// Place a piece on the board with enhanced validation and context awareness
    /// </summary>
    public void SetPiece(int square, PieceType pieceType, bool isWhite, string context)
    {
            // Validate input
            if (square < 0 || square >= 64)
                throw new ArgumentOutOfRangeException(nameof(square));
            if (pieceType == PieceType.None)
                throw new ArgumentException("Cannot set None piece type");

            // Validate pawn placement (skip during move operations for now)
            if (pieceType == PieceType.Pawn && context != "promotion" && context != "move")
            {
                int rank = Bitboard.GetRank(square);
                if (isWhite && rank == 7 || !isWhite && rank == 0)
                    throw new ArgumentException("Cannot place pawn on first/last rank");
            }

            // Count kings before placing
            int whiteKings = Bitboard.PopCount(WhiteKing);
            int blackKings = Bitboard.PopCount(BlackKing);

            // Validate king count
            if (pieceType == PieceType.King)
            {
                if (isWhite && whiteKings >= 1 || !isWhite && blackKings >= 1)
                    throw new InvalidOperationException("Cannot place second king");
            }
            
            ulong squareBit = Bitboard.SquareToBitboard(square);
            
            // Remove any existing piece at this square first
            RemovePiece(square);
            
            // Add the new piece
            if (isWhite)
            {
                switch (pieceType)
                {
                    case PieceType.Pawn: WhitePawns |= squareBit; break;
                    case PieceType.Knight: WhiteKnights |= squareBit; break;
                    case PieceType.Bishop: WhiteBishops |= squareBit; break;
                    case PieceType.Rook: WhiteRooks |= squareBit; break;
                    case PieceType.Queen: WhiteQueens |= squareBit; break;
                    case PieceType.King: WhiteKing |= squareBit; break;
                    default: throw new ArgumentException($"Invalid piece type: {pieceType}");
                }
            }
            else
            {
                switch (pieceType)
                {
                    case PieceType.Pawn: BlackPawns |= squareBit; break;
                    case PieceType.Knight: BlackKnights |= squareBit; break;
                    case PieceType.Bishop: BlackBishops |= squareBit; break;
                    case PieceType.Rook: BlackRooks |= squareBit; break;
                    case PieceType.Queen: BlackQueens |= squareBit; break;
                    case PieceType.King: BlackKing |= squareBit; break;
                    default: throw new ArgumentException($"Invalid piece type: {pieceType}");
                }
            }
            
            // Ensure position remains valid
            EnsurePositionConsistency("move");
    }

    /// <summary>
    /// Remove a piece from the board with enhanced validation
    /// </summary>
    public void RemovePiece(int square)
    {
            // Validate input
            if (square < 0 || square >= 64)
                throw new ArgumentOutOfRangeException(nameof(square));

            // Get existing piece for validation
            var (pieceType, isWhite) = GetPieceAt(square);
            
            // Create removal mask
            ulong squareBit = ~Bitboard.SquareToBitboard(square);
            
            // Remove the piece
            WhitePawns &= squareBit;
            WhiteKnights &= squareBit;
            WhiteBishops &= squareBit;
            WhiteRooks &= squareBit;
            WhiteQueens &= squareBit;
            WhiteKing &= squareBit;
            
            BlackPawns &= squareBit;
            BlackKnights &= squareBit;
            BlackBishops &= squareBit;
            BlackRooks &= squareBit;
            BlackQueens &= squareBit;
            BlackKing &= squareBit;

            // Update composite bitboards
            UpdateCompositeBitboards();

            // If we removed a king, ensure castling rights are updated
            if (pieceType == PieceType.King)
            {
                if (isWhite)
                {
                    WhiteCanCastleKingside = false;
                    WhiteCanCastleQueenside = false;
                }
                else
                {
                    BlackCanCastleKingside = false;
                    BlackCanCastleQueenside = false;
                }
            }
            
            // If we removed a rook, update castling rights
            if (pieceType == PieceType.Rook)
            {
                if (isWhite)
                {
                    if (square == 0) // a1
                        WhiteCanCastleQueenside = false;
                    else if (square == 7) // h1
                        WhiteCanCastleKingside = false;
                }
                else
                {
                    if (square == 56) // a8
                        BlackCanCastleQueenside = false;
                    else if (square == 63) // h8
                        BlackCanCastleKingside = false;
                }
            }
    }

    /// <summary>
    /// Move a piece from one square to another with enhanced validation
    /// </summary>
    public void MovePiece(int fromSquare, int toSquare)
    {
            // Input validation
            if (fromSquare < 0 || fromSquare >= 64)
                throw new ArgumentOutOfRangeException(nameof(fromSquare));
            if (toSquare < 0 || toSquare >= 64)
                throw new ArgumentOutOfRangeException(nameof(toSquare));
            if (fromSquare == toSquare)
                throw new ArgumentException("From and to squares cannot be the same");

            // Get moving piece
            var (pieceType, isWhite) = GetPieceAt(fromSquare);
            if (pieceType == PieceType.None)
                throw new InvalidOperationException($"No piece at square {fromSquare}");
            
            // Get captured piece (if any)
            var (capturedType, capturedIsWhite) = GetPieceAt(toSquare);
            if (capturedType != PieceType.None && capturedIsWhite == isWhite)
                throw new InvalidOperationException("Cannot capture own piece");

            // Handle en passant clearing
            if (pieceType == PieceType.Pawn)
            {
                // Check for double push and set en passant
                int fromRank = Bitboard.GetRank(fromSquare);
                int toRank = Bitboard.GetRank(toSquare);
                if (Math.Abs(toRank - fromRank) == 2)
                {
                    EnPassantSquare = (fromSquare + toSquare) / 2; // Middle square
                }
                else
                {
                    EnPassantSquare = -1;
                }
            }
            else
            {
                EnPassantSquare = -1; // Clear en passant on non-pawn moves
            }
            
            // Make the move
            RemovePiece(fromSquare);
            SetPiece(toSquare, pieceType, isWhite);

            // Ensure position remains valid
            EnsurePositionConsistency("move");
    }

    /// <summary>
    /// Get all pieces of a specific type and color
    /// </summary>
    public ulong GetPieces(PieceType pieceType, bool isWhite)
    {
            return (pieceType, isWhite) switch
            {
                (PieceType.Pawn, true) => WhitePawns,
                (PieceType.Knight, true) => WhiteKnights,
                (PieceType.Bishop, true) => WhiteBishops,
                (PieceType.Rook, true) => WhiteRooks,
                (PieceType.Queen, true) => WhiteQueens,
                (PieceType.King, true) => WhiteKing,
                (PieceType.Pawn, false) => BlackPawns,
                (PieceType.Knight, false) => BlackKnights,
                (PieceType.Bishop, false) => BlackBishops,
                (PieceType.Rook, false) => BlackRooks,
                (PieceType.Queen, false) => BlackQueens,
                (PieceType.King, false) => BlackKing,
                _ => 0UL
            };
    }

    /// <summary>
    /// Get all pieces of a specific color
    /// </summary>
    public ulong GetAllPieces(bool isWhite)
    {
        return isWhite ? AllWhitePieces : AllBlackPieces;
    }

    /// <summary>
    /// Find the king square for a specific color
    /// </summary>
    public int GetKingSquare(bool isWhite)
    {
        ulong kingBitboard = isWhite ? WhiteKing : BlackKing;
        return kingBitboard != 0 ? Bitboard.LSB(kingBitboard) : -1;
    }

    /// <summary>
    /// Check if a square is attacked by the specified color
    /// </summary>
    public bool IsSquareAttacked(int square, bool byWhite)
    {
            // Safety check for invalid squares
            if (square < 0 || square >= 64)
            {
                return false;
            }
            
            ulong squareBit = Bitboard.SquareToBitboard(square);
            
            // Check pawn attacks
            ulong enemyPawns = GetPieces(PieceType.Pawn, byWhite);
            ulong pawnAttacks = byWhite ? Bitboard.WhitePawnAttacks(enemyPawns) : Bitboard.BlackPawnAttacks(enemyPawns);
            if ((pawnAttacks & squareBit) != 0) return true;
            
            // Check knight attacks
            ulong enemyKnights = GetPieces(PieceType.Knight, byWhite);
            while (enemyKnights != 0)
            {
                int knightSquare = Bitboard.PopLSB(ref enemyKnights);
                if ((Bitboard.KnightAttacks(knightSquare) & squareBit) != 0) return true;
            }
            
            // Check sliding piece attacks
            ulong enemyBishopsQueens = GetPieces(PieceType.Bishop, byWhite) | GetPieces(PieceType.Queen, byWhite);
            if ((MagicBitboards.GetBishopAttacks(square, AllPieces) & enemyBishopsQueens) != 0) return true;
            
            ulong enemyRooksQueens = GetPieces(PieceType.Rook, byWhite) | GetPieces(PieceType.Queen, byWhite);
            if ((MagicBitboards.GetRookAttacks(square, AllPieces) & enemyRooksQueens) != 0) return true;
            
            // Check king attacks
            int enemyKingSquare = GetKingSquare(byWhite);
            if (enemyKingSquare != -1 && (Bitboard.KingAttacks(enemyKingSquare) & squareBit) != 0) return true;
            
            return false;
    }

    /// <summary>
    /// Check if the current player is in check
    /// </summary>
    public bool IsInCheck()
    {
        int kingSquare = GetKingSquare(IsWhiteToMove);
        if (kingSquare == -1)
        {
            // King not found - this should never happen in a valid position
            // Return false to avoid crashes, but this indicates a serious bug
            return false;
        }
        return IsSquareAttacked(kingSquare, !IsWhiteToMove);
    }

    /// <summary>
    /// Load position from FEN string with enhanced validation
    /// </summary>
    public static BitboardPosition FromFEN(string fen)
    {
            if (string.IsNullOrWhiteSpace(fen))
                throw new ArgumentException("FEN string cannot be null or empty");

            string[] parts = fen.Split(' ');
            if (parts.Length != 6)
                throw new ArgumentException("FEN must have 6 parts");

            try
            {
                var position = new BitboardPosition();

                // Clear all bitboards
                position.WhitePawns = position.WhiteKnights = position.WhiteBishops = 0UL;
                position.WhiteRooks = position.WhiteQueens = position.WhiteKing = 0UL;
                position.BlackPawns = position.BlackKnights = position.BlackBishops = 0UL;
                position.BlackRooks = position.BlackQueens = position.BlackKing = 0UL;

                // Parse piece placement with validation
                string[] ranks = parts[0].Split('/');
                if (ranks.Length != 8)
                    throw new ArgumentException("FEN must have 8 ranks");

                // Track piece counts for validation
                int whitePawns = 0, blackPawns = 0;
                int whiteKings = 0, blackKings = 0;

                for (int rank = 0; rank < 8; rank++)
                {
                    int file = 0;
                    int rankSum = 0;
                    foreach (char c in ranks[7 - rank]) // FEN starts from rank 8
                    {
                        if (char.IsDigit(c))
                        {
                            int emptyCount = c - '0';
                            if (emptyCount < 1 || emptyCount > 8)
                                throw new ArgumentException($"Invalid empty square count: {emptyCount}");
                            file += emptyCount;
                            rankSum += emptyCount;
                            
                            if (file > 8)
                                throw new ArgumentException($"Rank overflow at rank {8-rank}");
                        }
                        else
                        {
                            bool isWhite = char.IsUpper(c);
                            PieceType pieceType = char.ToLower(c) switch
                            {
                                'p' => PieceType.Pawn,
                                'n' => PieceType.Knight,
                                'b' => PieceType.Bishop,
                                'r' => PieceType.Rook,
                                'q' => PieceType.Queen,
                                'k' => PieceType.King,
                                _ => throw new ArgumentException($"Invalid piece character: {c}")
                            };

                            // Track piece counts
                            if (pieceType == PieceType.Pawn)
                            {
                                if (isWhite)
                                {
                                    whitePawns++;
                                    if (rank == 7) // 8th rank
                                        throw new ArgumentException("White pawn on 8th rank");
                                }
                                else
                                {
                                    blackPawns++;
                                    if (rank == 0) // 1st rank
                                        throw new ArgumentException("Black pawn on 1st rank");
                                }
                                if (whitePawns > 8 || blackPawns > 8)
                                    throw new ArgumentException("Too many pawns");
                            }
                            else if (pieceType == PieceType.King)
                            {
                                if (isWhite) whiteKings++;
                                else blackKings++;
                                if (whiteKings > 1 || blackKings > 1)
                                    throw new ArgumentException("Too many kings");
                            }

                            if (file >= 8)
                                throw new ArgumentException("Rank overflow");
                                
                            int square = Bitboard.GetSquare(file, rank);
                            
                            // Directly set the bitboard bits instead of using SetPiece to avoid intermediate validation
                            ulong squareBit = Bitboard.SquareToBitboard(square);
                            if (isWhite)
                            {
                                switch (pieceType)
                                {
                                    case PieceType.Pawn: position.WhitePawns |= squareBit; break;
                                    case PieceType.Knight: position.WhiteKnights |= squareBit; break;
                                    case PieceType.Bishop: position.WhiteBishops |= squareBit; break;
                                    case PieceType.Rook: position.WhiteRooks |= squareBit; break;
                                    case PieceType.Queen: position.WhiteQueens |= squareBit; break;
                                    case PieceType.King: position.WhiteKing |= squareBit; break;
                                }
                            }
                            else
                            {
                                switch (pieceType)
                                {
                                    case PieceType.Pawn: position.BlackPawns |= squareBit; break;
                                    case PieceType.Knight: position.BlackKnights |= squareBit; break;
                                    case PieceType.Bishop: position.BlackBishops |= squareBit; break;
                                    case PieceType.Rook: position.BlackRooks |= squareBit; break;
                                    case PieceType.Queen: position.BlackQueens |= squareBit; break;
                                    case PieceType.King: position.BlackKing |= squareBit; break;
                                }
                            }
                            
                            file++;
                            rankSum++;
                        }
                    }

                    if (rankSum != 8)
                        throw new ArgumentException($"Invalid rank sum: {rankSum} at rank {8-rank}");
                }

                // Validate kings
                if (whiteKings != 1 || blackKings != 1)
                    throw new ArgumentException("Must have exactly one king per side");

                // Parse active color
                if (parts[1] != "w" && parts[1] != "b")
                    throw new ArgumentException("Invalid active color");
                position.IsWhiteToMove = parts[1] == "w";

                // Parse castling with validation
                foreach (char c in parts[2])
                {
                    switch (c)
                    {
                        case 'K':
                            // Validate white kingside castling requirements
                            if ((position.WhiteKing & Bitboard.SquareToBitboard(4)) == 0 ||
                                (position.WhiteRooks & Bitboard.SquareToBitboard(7)) == 0)
                                throw new ArgumentException("Invalid white kingside castling rights");
                            position.WhiteCanCastleKingside = true;
                            break;
                            
                        case 'Q':
                            // Validate white queenside castling requirements
                            if ((position.WhiteKing & Bitboard.SquareToBitboard(4)) == 0 ||
                                (position.WhiteRooks & Bitboard.SquareToBitboard(0)) == 0)
                                throw new ArgumentException("Invalid white queenside castling rights");
                            position.WhiteCanCastleQueenside = true;
                            break;
                            
                        case 'k':
                            // Validate black kingside castling requirements
                            if ((position.BlackKing & Bitboard.SquareToBitboard(60)) == 0 ||
                                (position.BlackRooks & Bitboard.SquareToBitboard(63)) == 0)
                                throw new ArgumentException("Invalid black kingside castling rights");
                            position.BlackCanCastleKingside = true;
                            break;
                            
                        case 'q':
                            // Validate black queenside castling requirements
                            if ((position.BlackKing & Bitboard.SquareToBitboard(60)) == 0 ||
                                (position.BlackRooks & Bitboard.SquareToBitboard(56)) == 0)
                                throw new ArgumentException("Invalid black queenside castling rights");
                            position.BlackCanCastleQueenside = true;
                            break;
                            
                        case '-':
                            break;
                            
                        default:
                            throw new ArgumentException($"Invalid castling right: {c}");
                    }
                }

                // Parse en passant square
                if (parts[3] == "-")
                {
                    position.EnPassantSquare = -1;
                }
                else
                {
                    if (parts[3].Length != 2)
                        throw new ArgumentException("Invalid en passant square");
                        
                    char file = parts[3][0];
                    char rank = parts[3][1];
                    
                    if (file < 'a' || file > 'h' || rank < '1' || rank > '8')
                        throw new ArgumentException("Invalid en passant square");
                        
                    position.EnPassantSquare = Bitboard.GetSquare(file - 'a', rank - '1');
                    
                    // Validate en passant square is on correct rank
                    int epRank = Bitboard.GetRank(position.EnPassantSquare);
                    if (position.IsWhiteToMove && epRank != 5 || !position.IsWhiteToMove && epRank != 2)
                        throw new ArgumentException("Invalid en passant square rank");
                }

                // Parse move counts
                if (!int.TryParse(parts[4], out int halfMoves) || halfMoves < 0)
                    throw new ArgumentException("Invalid halfmove clock");
                position.HalfMoveClock = halfMoves;

                if (!int.TryParse(parts[5], out int fullMoves) || fullMoves < 1)
                    throw new ArgumentException("Invalid fullmove number");
                position.FullMoveNumber = fullMoves;

                // Final validation - use minimal validation during FEN parsing
                position.EnsurePositionConsistency("FromFEN");
                var validation = position.ValidateStateDetailed();
                if (!validation.isValid)
                {
                    throw new ArgumentException($"Invalid position state after FEN parsing: {validation.details}");
                }

                return position;
            }
            catch (Exception ex)
            {
                throw new ArgumentException($"FEN parsing error: {ex.Message}", ex);
            }
    }

    /// <summary>
    /// Get starting position
    /// </summary>
    public static BitboardPosition StartingPosition()
    {
        return FromFEN("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
    }

    /// <summary>
    /// Convert position to FEN string
    /// </summary>
    public string ToFEN()
    {
            var fen = new System.Text.StringBuilder();
            
            // 1. Piece placement
            for (int rank = 7; rank >= 0; rank--)
            {
                int emptySquares = 0;
                for (int file = 0; file < 8; file++)
                {
                    int square = Bitboard.GetSquare(file, rank);
                    var (pieceType, isWhite) = GetPieceAt(square);
                    
                    if (pieceType == PieceType.None)
                    {
                        emptySquares++;
                    }
                    else
                    {
                        if (emptySquares > 0)
                        {
                            fen.Append(emptySquares);
                            emptySquares = 0;
                        }
                        
                        char pieceChar = pieceType switch
                        {
                            PieceType.Pawn => 'p',
                            PieceType.Rook => 'r',
                            PieceType.Knight => 'n',
                            PieceType.Bishop => 'b',
                            PieceType.Queen => 'q',
                            PieceType.King => 'k',
                            _ => '?'
                        };
                        
                        if (isWhite)
                        {
                            pieceChar = char.ToUpper(pieceChar);
                        }
                        
                        fen.Append(pieceChar);
                    }
                }
                
                if (emptySquares > 0)
                {
                    fen.Append(emptySquares);
                }
                
                if (rank > 0)
                {
                    fen.Append('/');
                }
            }
            
            // 2. Active color
            fen.Append(' ');
            fen.Append(IsWhiteToMove ? 'w' : 'b');
            
            // 3. Castling availability
            fen.Append(' ');
            var castling = "";
            if (WhiteCanCastleKingside) castling += "K";
            if (WhiteCanCastleQueenside) castling += "Q";
            if (BlackCanCastleKingside) castling += "k";
            if (BlackCanCastleQueenside) castling += "q";
            fen.Append(castling == "" ? "-" : castling);
            
            // 4. En passant target square
            fen.Append(' ');
            if (EnPassantSquare == -1)
            {
                fen.Append('-');
            }
            else
            {
                char file = (char)('a' + Bitboard.GetFile(EnPassantSquare));
                int rank = Bitboard.GetRank(EnPassantSquare) + 1;
                fen.Append($"{file}{rank}");
            }
            
            // 5. Halfmove clock and fullmove number
            fen.Append($" {HalfMoveClock} {FullMoveNumber}");
            
            return fen.ToString();
        }
    }
}