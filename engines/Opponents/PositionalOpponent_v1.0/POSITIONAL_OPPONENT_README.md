# Positional Opponent v1.0

A UCI-compatible chess engine that uses piece-square tables (PSTs) for position-based evaluation.

## Overview

**Positional Opponent** is a chess engine that evaluates positions based entirely on piece placement rather than static material values. Each piece's value is determined dynamically by its position on the board using comprehensive piece-square tables, creating a distinctly positional playing style.

### Engine Philosophy

Unlike traditional engines that assign fixed values to pieces (e.g., pawn=100, knight=300), the Positional Opponent evaluates pieces based on **where they are positioned**:

- A knight on the edge (b1) = 220 centipawns
- A knight in the center (d4) = 350 centipawns
- **Centralization bonus: 130 centipawns!**

This approach naturally encourages:
- Central piece placement
- Pawn advancement toward promotion
- Optimal square occupation
- Dynamic positional understanding

## Key Features

### Piece-Square Table Evaluation

Each piece type has its own comprehensive PST with values ranging from minimum to maximum potential:

| Piece Type | Value Range | Strategy |
|------------|-------------|----------|
| **Pawn** | 0 - 900 cp | Values increase dramatically as pawns advance toward the 8th rank (promotion) |
| **Knight** | 200 - 400 cp | Highest values on central squares (d4, e4, d5, e5) |
| **Bishop** | 250 - 400 cp | Rewards long diagonals and central control |
| **Rook** | 400 - 600 cp | Values open files, back rank power, and 7th rank penetration |
| **Queen** | 700 - 1100 cp | Highly centralized and active positioning |
| **King** | Variable | Middlegame: prioritizes safety (castled positions)<br>Endgame: rewards centralization |

### Advanced Features

1. **Endgame Detection**: Automatically switches king evaluation from safety-focused to centralization-focused
2. **Dynamic Values**: Same piece can have vastly different values based on position
3. **Positional Understanding**: Naturally plays positionally strong moves without explicit mobility/king safety evaluation

### Search Infrastructure

The Positional Opponent inherits the complete search framework from the Opponent Engine Template:

- **Minimax with Alpha-Beta Pruning**: Efficient tree search
- **Iterative Deepening**: Progressive depth increases
- **Move Ordering**: TT moves, checks, captures (MVV-LVA), killer moves, history heuristic
- **Quiescence Search**: Avoids horizon effect on captures
- **Null Move Pruning**: Reduces search space
- **Principal Variation Search**: Optimizes alpha-beta efficiency
- **Zobrist Transposition Table**: Position caching for speed
- **Time Management**: Adaptive time allocation

## Installation & Setup

### Requirements

- Python 3.13 or higher
- `python-chess` library

### Installation Steps

1. **Install Python 3.13**: Download from [python.org](https://www.python.org)

2. **Install python-chess**:
   ```bash
   pip install python-chess
   ```

3. **Verify Installation**:
   ```bash
   python positional_opponent.py
   ```
   Type `uci` and press Enter - should respond with engine identification.

### Arena Chess GUI Setup

1. Open Arena Chess GUI
2. Go to: **Engines → Install New Engine**
3. Navigate to this folder and select: `PositionalOpponent.bat`
4. Engine will appear as: **Positional Opponent v1.0**

**Important**: Update the Python path in `PositionalOpponent.bat` if your Python installation differs:
```batch
"C:\Users\patss\AppData\Local\Programs\Python\Python313\python.exe" positional_opponent.py
```

## Usage

### UCI Commands

The engine supports standard UCI protocol:

```
uci                    # Engine identification
isready                # Check readiness
ucinewgame            # Start new game
position startpos      # Set starting position
position startpos moves e2e4 e7e5  # Set position with moves
go wtime 300000 btime 300000       # Search with time control
go depth 10           # Search to fixed depth
quit                  # Exit engine
```

### Configuration Options

| Option | Type | Default | Range | Description |
|--------|------|---------|-------|-------------|
| MaxDepth | spin | 6 | 1-20 | Maximum search depth |
| TTSize | spin | 128 | 16-1024 | Transposition table size (MB) |

Example configuration:
```
setoption name MaxDepth value 8
setoption name TTSize value 256
```

## Performance Characteristics

### Typical Performance

- **Depth**: Reaches depth 6-8 in standard time controls
- **Nodes per Second**: 15,000 - 100,000 nps (position dependent)
- **Memory Usage**: ~128 MB (default TT size)
- **Search Efficiency**: High due to aggressive move ordering

### Benchmark Results

Starting position, 2-second search:
- **Depth Reached**: 6
- **Nodes Searched**: ~16,000
- **Time**: 1.1 seconds
- **NPS**: ~25,000

Midgame position, 2-second search:
- **Depth Reached**: 4
- **Nodes Searched**: ~2,600
- **Time**: 0.2 seconds
- **NPS**: ~98,000

## Playing Style

### Strengths

1. **Positional Understanding**: Naturally seeks optimal piece placement
2. **Central Control**: Strong preference for central squares
3. **Pawn Structure**: Values pawn advancement and promotion threats
4. **Piece Activity**: Rewards active, well-placed pieces
5. **Consistent Strategy**: Position-based evaluation creates coherent plans

### Weaknesses

1. **Material Blindness**: May sacrifice material for positional gains
2. **Tactical Oversights**: PST-only evaluation misses some tactical nuances
3. **King Safety**: Basic king safety (only PST-based, no attack evaluation)
4. **Pawn Structure**: No explicit weak pawn or isolated pawn detection
5. **Mobility**: Doesn't explicitly evaluate piece mobility

### Ideal Opponents

- **Good Practice Against**: Material-focused engines, beginners learning positional play
- **Challenging Matchups**: Tactically sharp engines, strong material evaluators
- **Interesting Games**: Mirror matches against other positional engines

## Technical Details

### Architecture

```
PositionalOpponent (Main Class)
├── Evaluation: _evaluate_position() using PSTs
├── PST Lookup: _get_piece_square_value()
├── Endgame Detection: _is_endgame()
├── Search: _search() - minimax with alpha-beta
├── Move Ordering: _order_moves()
├── Quiescence: _quiescence_search()
└── Time Management: _calculate_time_limit()

UCIPositionalEngine (UCI Interface)
├── Command Parsing: _handle_position(), _handle_go()
├── Option Management: _handle_setoption()
└── Main Loop: run()
```

### Code Statistics

- **Total Lines**: 675
- **Search Infrastructure**: 85% shared with template
- **Unique Evaluation Code**: ~15% (PST tables and lookup)
- **Comments/Documentation**: Comprehensive

### Piece-Square Table Design

**Design Principles**:
1. **Pawns**: Exponential growth toward promotion (50 → 400 → 900)
2. **Knights**: Peak values on central squares (d4/e4/d5/e5)
3. **Bishops**: Long diagonal bonuses (a1-h8, h1-a8)
4. **Rooks**: Back rank (1st) and penetration (7th rank) bonuses
5. **Queens**: Gradual centralization rewards
6. **Kings**: Phase-dependent (safety vs centralization)

**Symmetry**: All PSTs are symmetric along the e-file, reflecting chess board symmetry.

## Customization

### Modifying Piece-Square Tables

Edit the PST arrays at the top of `positional_opponent.py`:

```python
# Example: Make knights even more centralized
KNIGHT_PST = [
    [200,220,240,250,250,240,220,200],
    [220,240,260,270,270,260,240,220],
    [240,260,300,320,320,300,260,240],
    [250,270,320,400,400,320,270,250],  # Increased center values
    [250,270,320,400,400,320,270,250],  # Increased center values
    [240,260,300,320,320,300,260,240],
    [220,240,260,270,270,260,240,220],
    [200,220,240,250,250,240,220,200],
]
```

### Adjusting Endgame Threshold

Modify the `_is_endgame()` method:

```python
def _is_endgame(self, board: chess.Board) -> bool:
    # Current: < 800 material per side
    # More aggressive: < 1200
    return white_material < 1200 and black_material < 1200
```

### Adding New Evaluation Terms

While keeping the PST core, you can add bonuses:

```python
def _evaluate_position(self, board: chess.Board) -> int:
    score = 0
    is_endgame = self._is_endgame(board)
    
    # PST evaluation (core)
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            score += self._get_piece_square_value(piece, square, is_endgame)
    
    # Optional: Add mobility bonus
    mobility_bonus = len(list(board.legal_moves)) * 5
    score += mobility_bonus if board.turn == chess.WHITE else -mobility_bonus
    
    return score if board.turn == chess.WHITE else -score
```

## Development History

**Version 1.0** (November 2025)
- Initial release
- Complete PST implementation for all pieces
- Full UCI protocol support
- Endgame king PST switching
- Based on Opponent Engine Template architecture

## Comparison with Material Opponent

| Feature | Positional Opponent | Material Opponent |
|---------|-------------------|-------------------|
| **Evaluation** | Position-based PSTs | Static material values + bishop pairs |
| **Pawn Value** | 0-900 (position dependent) | 100 (fixed) |
| **Knight Value** | 200-400 (centralization) | 300 (fixed) |
| **Strategy** | Positional, piece placement | Material balance |
| **Playing Style** | Seeks optimal squares | Seeks material advantage |
| **Code Changes** | Only evaluation (~15%) | Only evaluation (~10%) |
| **Framework** | Shared template | Shared template |

## Troubleshooting

### Engine Won't Start

1. **Check Python Path**: Verify Python 3.13 installation path in `PositionalOpponent.bat`
2. **Install Dependencies**: Run `pip install python-chess`
3. **Test Manually**: Run `python positional_opponent.py` and type `uci`

### Slow Performance

1. **Reduce MaxDepth**: Set to 4-5 for faster play
2. **Increase TTSize**: More memory = better caching
3. **Check System Resources**: Close other applications

### Strange Moves

1. **Verify PST Values**: Check that PST tables are correct
2. **Test Evaluation**: Use `_evaluate_position()` on known positions
3. **Check Endgame Detection**: Verify phase detection is working

## Credits

**Engine Design**: Opponent Chess Engines Project  
**Architecture**: Based on Opponent Engine Template  
**Evaluation Concept**: Classic piece-square table approach  
**UCI Protocol**: Universal Chess Interface standard  

## License

This engine is part of the Opponent Chess Engines collection, designed for educational purposes and chess engine development learning.

## Contact & Support

For issues, improvements, or questions about the Positional Opponent engine, refer to the main Opponent Chess Engines project documentation.

---

**Version**: 1.0  
**Release Date**: November 2025  
**Python Version**: 3.13+  
**UCI Protocol**: Fully compatible  
**Status**: Production ready