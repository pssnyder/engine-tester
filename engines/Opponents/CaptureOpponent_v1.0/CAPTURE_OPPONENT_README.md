# Capture Opponent v1.0 - The Strategic Simplifier

## Overview

**Capture Opponent** is a chess engine with one obsessive goal: remove as much material from the board as possible. This engine will trade pieces aggressively, accepting up to -1 material disadvantage to force simplifications. It creates a unique challenge for opponents by exploiting any hanging pieces or tactical tension immediately.

**Philosophy**: "If it can be taken, it WILL be taken"

---

## Core Strategy

### Custom Piece Valuations
The Capture Opponent uses non-standard piece values designed to create interesting trade dynamics:

- **Pawn**: 2 points
- **Knight**: 4 points  
- **Bishop**: 3 points
- **Rook**: 5 points
- **Queen**: 8 points
- **King**: 0 points (no trade value)

These values make the engine willing to make trades that traditional engines might avoid, such as trading a knight for two pawns (4 for 4 = acceptable).

### Trade Acceptance Criteria

The engine uses **Static Exchange Evaluation (SEE)** to calculate multi-move capture sequences and will accept trades that meet these criteria:

✅ **Will Make These Trades:**
- Queen for queen (0 material - perfect!)
- Knight for 2 pawns (4 for 4 - acceptable)
- Rook for knight + pawn (5 for 6 - we gain material!)
- Any trade losing ≤ 1 material point

❌ **Will Avoid These Trades:**
- Queen for 2 pawns (-4 material - too uneven)
- Rook for pawn (-3 material - too much)
- Any trade losing > 1 material point

---

## Technical Features

### Static Exchange Evaluation (SEE)
The engine implements full SEE calculations to accurately evaluate complex capture sequences:
- Simulates all recaptures on a square
- Uses minimax to determine the final material balance
- Only used for sequences with 2+ potential recaptures
- Ensures trades don't exceed the -1 material threshold

### Evaluation Function

The Capture Opponent evaluates positions using these factors (in priority order):

1. **Checkmate Detection** (highest priority)
   - Always recognizes and plays mate-in-N
   - Will take checkmate over any simplification

2. **Total Material on Board** (primary goal)
   - Lower total material = better evaluation
   - Rewards material removal regardless of who's ahead
   - +50cp bonus per material point removed from starting position

3. **Material Balance** (secondary goal)
   - Accepts being down by 1 material point
   - Penalizes deficits > 1 point to avoid unwinnable positions
   - +10cp per point of material advantage within acceptable range

4. **Capture Opportunities** (tertiary goal)
   - +100cp bonus per "good capture" available
   - Encourages positions with forcing continuations

### Move Ordering

Heavily biased toward captures:
1. Checkmate moves (10,000,000 priority)
2. Transposition table move (9,000,000)
3. Good captures passing SEE test (5,000,000+)
4. All other captures (3,000,000+)
5. Killer moves (100,000)
6. Other moves (history heuristic)

---

## Engine Specifications

### Search Characteristics
- **Algorithm**: Minimax with alpha-beta pruning
- **Default Max Depth**: 8 (deeper than standard due to simplified positions)
- **Iterative Deepening**: Yes
- **Quiescence Search**: Yes (captures only)
- **Null Move Pruning**: Yes (R=3)
- **Principal Variation Search**: Yes
- **Transposition Table**: 256 MB (configurable)

### Performance
- **Typical Search Depth**: 5-7 plies in middlegame positions
- **Nodes per Second**: 4,000-8,000 nps (varies by position complexity)
- **Time Management**: Adaptive based on remaining time
- **UCI Protocol**: Fully compliant

---

## Behavioral Characteristics

### What This Engine Does Well
✅ Punishes hanging pieces mercilessly  
✅ Forces concrete calculations from opponents  
✅ Creates simplified positions rapidly  
✅ Exploits tactical oversights  
✅ Reaches deeper search depths in simplified positions  
✅ Finds checkmates when available  

### What This Engine Does Poorly
❌ Positional understanding (none)  
❌ Pawn structure evaluation (none)  
❌ King safety considerations (minimal)  
❌ Endgame technique (only checkmate awareness)  
❌ Long-term planning (only immediate trades)  
❌ Opening theory (none)  

### Expected Outcomes
- **Draws by insufficient material**: Considered a success!
- **Tactical shootouts**: Thrives in sharp positions
- **Quiet positions**: Will create forcing complications
- **Endgames**: May draw or lose theoretically won positions

---

## Usage

### Command Line
```bash
python capture_opponent.py
```
Or use the batch file:
```bash
CaptureOpponent.bat
```

### UCI Options
- `MaxDepth`: Search depth limit (1-20, default: 8)
- `TTSize`: Transposition table size in MB (16-1024, default: 256)

### Example UCI Session
```
uci
isready
position startpos moves e2e4 e7e5 g1f3 b8c6
go depth 5
```

---

## Testing Results

### Typical Behavior Examples

**Position with hanging pawn:**
```
rnbqkb1r/pppp1ppp/5n2/4p3/3P4/5N2/PPP1PPPP/RNBQKB1R w KQkq
Best move: f3e5 (knight takes pawn)
Evaluation: +330cp at depth 5
```

**Queen trade opportunity:**
```
rnb1kbnr/pppp1ppp/8/4p3/3Pq3/5N2/PPP1QPPP/RNB1KB1R w KQkq
Best move: e2e4 (queen takes queen)
Evaluation: +605cp at depth 5
```

**Bad queen trade avoided:**
```
rnbqkbnr/pppp1ppp/8/8/3Pp3/8/PPP2PPP/RNBQKBNR w KQkq
Best move: d1g4 (developing move, not Qxe4)
Correctly avoids losing queen for pawn
```

---

## Design Philosophy

### Why This Engine Exists

The Capture Opponent serves multiple purposes in engine testing:

1. **Defensive Testing**: Forces other engines to defend accurately
2. **Tactical Awareness**: Punishes engines that don't calculate forcing sequences
3. **Material Management**: Tests if engines can maintain material advantages
4. **Simplification Skills**: Challenges engines in simplified positions
5. **Experimental Design**: Explores non-traditional evaluation functions

### Unique Characteristics

Unlike traditional engines that balance material, position, and tactics, the Capture Opponent has a singular obsession. This creates fascinating game dynamics:

- **No Positional Considerations**: Pure tactical calculation
- **Accepts Disadvantages**: Willing to be slightly behind materially
- **Forces Concrete Play**: Opponents can't rely on positional advantages
- **Rapid Simplification**: Games quickly enter unusual territory

---

## Technical Implementation

### Architecture
- **Single-file implementation**: ~1,140 lines of Python
- **Standalone**: No external dependencies beyond `python-chess`
- **Embedded template**: All base engine code included
- **Type-safe**: Full type annotations with assertions

### Key Methods
- `_static_exchange_evaluation()`: Full SEE implementation
- `_is_good_trade()`: Trade acceptance logic
- `_evaluate_position()`: Custom evaluation function
- `_order_moves()`: Capture-biased move ordering
- `_calculate_total_material()`: Board material counting

---

## Version History

### v1.0 (November 2025)
- Initial release
- Custom piece values (P=2, N=4, B=3, R=5, Q=8)
- Static Exchange Evaluation implementation
- Trade acceptance threshold: -1 material
- Default depth: 8
- Transposition table: 256 MB

---

## Known Limitations

1. **Computational Intensity**: SEE calculations in evaluation can be expensive
2. **No Endgame Tables**: Relies only on search for endgame play
3. **Draw-heavy**: May reach insufficient material draws frequently
4. **Position Blindness**: Cannot evaluate pawn structures or weak squares
5. **Time Management**: May search too deep in complex positions

---

## Future Development Ideas

Potential enhancements for future versions:
- Adjust MAX_TRADE_LOSS threshold dynamically based on position
- Add minimal king safety to avoid instant tactical losses
- Implement basic pawn endgame knowledge
- Optimize SEE calculations (currently called during evaluation)
- Add tablebase support for 3-6 piece endgames
- Create "EndgameOpponent" variant with superior endgame technique

---

## Recommended Opponents

### Good Matchups
- **Material Opponent**: Similar evaluation, tests who trades better
- **Positional Opponent**: Tests positional vs tactical play
- **Coverage Opponent**: Both favor dynamic positions
- **Random Opponent**: Chaotic games with unpredictable tactics

### Challenging Matchups
- **Stockfish/Strong Engines**: Will exploit positional weaknesses
- **Endgame Specialists**: Better technique in simplified positions
- **Defensive Engines**: May successfully defend and convert small advantages

---

## Credits

**Author**: OpponentEngine Project  
**Engine Type**: UCI-compatible Python chess engine  
**Purpose**: Testing and experimental opponent  
**License**: Part of the Opponent Chess Engines collection

---

## Quick Reference

**Goal**: Remove all material from the board  
**Strategy**: Accept trades losing ≤ 1 material point  
**Strength**: Tactical calculation and forcing play  
**Weakness**: Positional understanding and endgame technique  
**Best Use**: Testing tactical awareness and defensive skills

**Remember**: This engine will trade everything it can. Defend carefully or it will simplify you into a draw!
