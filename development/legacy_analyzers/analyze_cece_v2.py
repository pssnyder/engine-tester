import os, sys, collections
import chess.pgn, json

TARGET = {"Cece v2.0", "Cece v2.2"}
PGN_EXTS = {".pgn", ".txt"}

def iter_pgn_files(root):
    for dirpath, _, files in os.walk(root):
        for f in files:
            if os.path.splitext(f)[1].lower() in PGN_EXTS:
                yield os.path.join(dirpath, f)

def piece_letter(piece):
    if piece is None:
        return "?"
    return piece.symbol().upper()

def analyze_game(game, target):
    board = game.board()
    stats = {
        "moves": [],
        "piece_moves": collections.Counter(),
        "san": collections.Counter(),
        "missed_captures": 0,
        "pieces_captured_after_move": 0,
        "rook_moves_while_castling_rights": 0,
        "king_moved_before_castle": 0,
        "castle_occurred": False,
        "rook_shuffle": 0,
        "knight_first_dev": 0,
    }

    node = game
    ply = 0
    knight_moved = False
    bishop_or_pawn_moved = False
    rook_moves = []  # list of (from,to,ply)

    while node.variations:
        move = node.variations[0].move
        san = node.board().san(move)
        mover_color = node.board().turn
        mover_name = game.headers.get("White") if mover_color == chess.WHITE else game.headers.get("Black")
        is_target = mover_name == target

        legal_moves = list(node.board().legal_moves)
        capture_available = any(node.board().is_capture(m) for m in legal_moves)

        from_sq = move.from_square
        to_sq = move.to_square
        moved_piece = node.board().piece_at(from_sq)
        node = node.variations[0]
        board_after = node.board()
        ply += 1

        if is_target:
            stats["moves"].append((ply, san, moved_piece.piece_type if moved_piece else None, from_sq, to_sq))
            stats["san"][san] += 1
            stats["piece_moves"][piece_letter(moved_piece)] += 1

            if capture_available and not board_after.is_capture(move):
                # player made a non-capture when a capture existed
                stats["missed_captures"] += 1

            # immediate capture: opponent captures this destination on next ply
            if node.variations:
                next_move = node.variations[0].move
                if node.board().is_capture(next_move) and next_move.to_square == to_sq:
                    stats["pieces_captured_after_move"] += 1

            # castling detection (simple SAN check)
            if san in ("O-O", "O-O-O"):
                stats["castle_occurred"] = True

            # rook logging
            if moved_piece and moved_piece.piece_type == chess.ROOK:
                rook_moves.append((from_sq, to_sq, ply))
                # if castling rights still exist for this color before move, count
                if board_after.has_castling_rights(mover_color):
                    stats["rook_moves_while_castling_rights"] += 1

            if moved_piece and moved_piece.piece_type == chess.KING:
                if board_after.has_castling_rights(mover_color):
                    stats["king_moved_before_castle"] += 1

            # dev ordering
            if moved_piece:
                if moved_piece.piece_type == chess.KNIGHT:
                    knight_moved = True
                if moved_piece.piece_type in (chess.BISHOP, chess.PAWN):
                    bishop_or_pawn_moved = True

    # rook shuffle metric (back-and-forth)
    shuffle = 0
    for i in range(2, len(rook_moves)):
        if rook_moves[i][0] == rook_moves[i-2][1]:
            shuffle += 1
    stats["rook_shuffle"] = shuffle
    stats["knight_first_dev"] = int(knight_moved and not bishop_or_pawn_moved)
    return stats

def main(root):
    agg = {t: {"games":0, "san":collections.Counter(), "piece_moves":collections.Counter(),
               "missed_captures":0, "pieces_captured_after":0,
               "rook_moves_while_castling_rights":0, "king_moved_before_castle":0,
               "castle_games":0, "rook_shuffle":0, "knight_first_dev":0}
           for t in TARGET}

    for pgn in iter_pgn_files(root):
        with open(pgn, 'r', encoding='utf-8', errors='ignore') as f:
            while True:
                game = chess.pgn.read_game(f)
                if game is None:
                    break
                white = game.headers.get("White","")
                black = game.headers.get("Black","")
                for t in TARGET:
                    if t in (white, black):
                        stats = analyze_game(game, t)
                        agg[t]["games"] += 1
                        agg[t]["san"].update(stats["san"])
                        agg[t]["piece_moves"].update(stats["piece_moves"])
                        agg[t]["missed_captures"] += stats["missed_captures"]
                        agg[t]["pieces_captured_after"] += stats["pieces_captured_after_move"]
                        agg[t]["rook_moves_while_castling_rights"] += stats["rook_moves_while_castling_rights"]
                        agg[t]["king_moved_before_castle"] += stats["king_moved_before_castle"]
                        agg[t]["castle_games"] += 1 if stats["castle_occurred"] else 0
                        agg[t]["rook_shuffle"] += stats["rook_shuffle"]
                        agg[t]["knight_first_dev"] += stats["knight_first_dev"]

    for t,v in agg.items():
        print(f"\n--- {t} ({v['games']} games) ---")
        print("Top SAN moves:")
        for m,c in v["san"].most_common(15):
            print(f"  {m}: {c}")
        print("Piece move totals (K,Q,R,B,N,P):")
        order = ["K","Q","R","B","N","P"]
        print("  " + ", ".join(f"{o}:{v['piece_moves'].get(o,0)}" for o in order))
        print(f"Missed captures: {v['missed_captures']}")
        print(f"Pieces captured immediately after moving: {v['pieces_captured_after']}")
        print(f"Rook moves while still having castling rights: {v['rook_moves_while_castling_rights']}")
        print(f"King moved while castling rights still present: {v['king_moved_before_castle']}")
        print(f"Rook shuffle metric: {v['rook_shuffle']}")
        print(f"Knight-first-development games: {v['knight_first_dev']}")
        print(f"Castled games: {v['castle_games']}")

if __name__ == '__main__':
    root = os.path.abspath(os.path.dirname(__file__))
    if len(sys.argv) > 1:
        root = sys.argv[1]
    main(root)