# Material Opponent Chess Engine

A UCI-compatible chess engine focused on material balance evaluation with modern search techniques.

## Features

### Evaluation
- **Pure Material Evaluation**: Primary heuristic based on piece values
- **Dynamic Bishop Evaluation**: Bishops worth 3.25 each when paired, 2.75 when alone
- **Piece Count Bonus**: Small bonus for piece diversity over pure pawn count

### Search
- **Minimax with Alpha-Beta Pruning**: Classic negamax search
- **Iterative Deepening**: Progressively deeper searches with time management
- **Quiescence Search**: Captures-only search to avoid horizon effects
- **Null Move Pruning**: Skip a turn to achieve beta cutoffs faster
- **Principal Variation Search**: Enhanced alpha-beta with null window searches

### Move Ordering
1. Transposition table move
2. Checkmate threats
3. Checks
4. Captures (MVV-LVA ordering)
5. Killer moves (2 per ply)
6. Pawn advances toward promotion
7. History heuristic
8. Other moves

### Optimizations
- **Zobrist Transposition Table**: Configurable size (default 128MB)
- **Killer Move Tables**: Best non-capture moves that caused cutoffs
- **History Heuristic**: Move success tracking for ordering
- **Time Management**: Adaptive time allocation for various time controls

## Usage

### UCI Interface
```bash
python material_opponent.py
```

### Direct API
```python
from material_opponent import MaterialOpponent
import chess

engine = MaterialOpponent(max_depth=6, tt_size_mb=128)
engine.board = chess.Board()
best_move = engine.get_best_move(time_left=300.0, increment=3.0)
```

### Configuration Options
- `MaxDepth`: Maximum search depth (default: 6, range: 1-20)
- `TTSize`: Transposition table size in MB (default: 128, range: 16-1024)

## Performance Characteristics

- **Target Depth**: Designed to consistently reach 10+ ply
- **Speed Focus**: Lightweight evaluation for maximum search depth
- **Time Controls**: Optimized for 30min, 10min, and 1min games
- **Node Rate**: Typically 25,000-50,000 nodes per second

## Design Philosophy

This engine serves as a stage 2 baseline opponent, emphasizing:
1. **Minimal Evaluation**: Pure material focus to test search effectiveness
2. **Maximum Depth**: Prioritizing search depth over evaluation complexity  
3. **Extensibility**: Clean foundation for future engine development
4. **Performance**: Python engine depth capability exploration

## Piece Values

- Pawn: 100 centipawns
- Knight: 300 centipawns  
- Bishop: 325 centipawns (paired) / 275 centipawns (alone)
- Rook: 500 centipawns
- Queen: 900 centipawns
- King: 0 centipawns

The dynamic bishop evaluation creates strategic depth where knight trades become favorable when opponents lose the bishop pair.

## Example Output

```
info depth 6 score cp 105 nodes 17333 nps 26634 time 650 pv f3e5
info string Search completed in 1.030s, 17333 nodes
bestmove f3e5
```

This engine demonstrates that with minimal evaluation overhead, Python chess engines can achieve impressive search depths through efficient algorithms and pruning techniques.