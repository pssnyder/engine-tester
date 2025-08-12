# Engine Test Report

Total engines: 22

Critical PASS: 16/22

## Engine: Cece_v1.0.exe
Path: `engines\Cece_v1.0.exe`
Result: FAIL (critical tests)
Total Duration: 5.71s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 1.07 |  |
| uci_handshake | ❌ | 1.54 | TIMEOUT: |
| isready | ❌ | 1.00 | TIMEOUT: |
| newgame | ✅ | 0.32 | option name PositionalWeight type spin default 30 min 0 max 100;option name TacticalWeight type spin default 20 min 0 ma |
| first_move_movetime | ❌ | 1.00 | NO_BESTMOVE:Initialized Cece v1.0;Author: Pat Snyder;Attribution: Built on python-chess by Niklas Fiekas;readyok;Position set: rnbqk |
| first_move_timecontrol | ✅ | 0.00 | bestmove h2h4 |
| multi_sequence | ❌ | 0.02 | ILLEGAL_MOVE:Bad move line bestmove 0000 |
| graceful_quit | ✅ | 0.76 | Exit code 0 |

## Engine: Cece_v1.1.exe
Path: `engines\Cece_v1.1.exe`
Result: FAIL (critical tests)
Total Duration: 2.54s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.89 |  |
| uci_handshake | ✅ | 0.05 | id name Cece
id author Pat Snyder
option name Debug type check default false
option name Hash type spin default 64 min 1 |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | Initialized Cece v1.1;Author: Pat Snyder;Attribution: Built on python-chess by Niklas Fiekas;readyok |
| first_move_movetime | ❌ | 1.00 | NO_BESTMOVE:Position set: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1;\nSearching position (depth: 10, time: 1.0s)...;S |
| first_move_timecontrol | ✅ | 0.00 | bestmove f2f4 |
| multi_sequence | ❌ | 0.04 | ILLEGAL_MOVE:Bad move line bestmove 0000 |
| graceful_quit | ✅ | 0.56 | Exit code 0 |

## Engine: Cece_v1.2.exe
Path: `engines\Cece_v1.2.exe`
Result: FAIL (critical tests)
Total Duration: 2.57s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.62 |  |
| uci_handshake | ✅ | 0.06 | id name Cece
id author Pat Snyder
option name Debug type check default false
option name Hash type spin default 64 min 1 |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | Initialized Cece v1.1;Author: Pat Snyder;Attribution: Built on python-chess by Niklas Fiekas;readyok |
| first_move_movetime | ❌ | 1.00 | NO_BESTMOVE:Position set: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1;\nSearching position (depth: 10, time: 1.0s)...;S |
| first_move_timecontrol | ✅ | 0.00 | bestmove g1h3 |
| multi_sequence | ❌ | 0.03 | ILLEGAL_MOVE:Bad move line bestmove 0000 |
| graceful_quit | ✅ | 0.86 | Exit code 0 |

## Engine: Cece_v1.3.exe
Path: `engines\Cece_v1.3.exe`
Result: FAIL (critical tests)
Total Duration: 5.54s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 1.64 |  |
| uci_handshake | ❌ | 1.54 | TIMEOUT: |
| isready | ✅ | 0.56 | option name PositionalWeight type spin default 30 min 0 max 100;option name TacticalWeight type spin default 20 min 0 ma |
| newgame | ✅ | 0.00 | Initialized Cece v1.3;Author: Pat Snyder;Attribution: Built on python-chess by Niklas Fiekas;readyok |
| first_move_movetime | ❌ | 1.00 | NO_BESTMOVE:Position set: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1;\nSearching position (depth: 6, time: 1.0s)...;Se |
| first_move_timecontrol | ✅ | 0.00 | bestmove g1h3 |
| multi_sequence | ❌ | 0.04 | ILLEGAL_MOVE:Bad move line bestmove 0000 |
| graceful_quit | ✅ | 0.76 | Exit code 0 |

## Engine: Cece_v2.0.exe
Path: `engines\Cece_v2.0.exe`
Result: FAIL (critical tests)
Total Duration: 2.33s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.68 |  |
| uci_handshake | ✅ | 0.06 | id name Cece
id author Pat Snyder
option name Debug type check default false
option name Hash type spin default 64 min 1 |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | Initialized Cece v2.0;Author: Pat Snyder;Attribution: Built on python-chess by Niklas Fiekas;readyok |
| first_move_movetime | ❌ | 1.00 | NO_BESTMOVE:Position set: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1;\nSearching position (depth: 6, time: 1.0s)...;Se |
| first_move_timecontrol | ✅ | 0.00 | bestmove g1f3 |
| multi_sequence | ❌ | 0.03 | ILLEGAL_MOVE:Bad move line bestmove 0000 |
| graceful_quit | ✅ | 0.56 | Exit code 0 |

## Engine: Cecilia_v0.1.0_Basic.exe
Path: `engines\Cecilia_v0.1.0_Basic.exe`
Result: PASS (critical tests)
Total Duration: 1.67s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.62 |  |
| uci_handshake | ✅ | 0.64 | id name Viper Basic v0.1.0
id author GitHub Copilot
option name Hash type spin default 64 min 1 max 2048
option name Thr |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.01 | bestmove g1h3 |
| first_move_timecontrol | ✅ | 0.01 | bestmove g1h3 |
| multi_sequence | ✅ | 0.03 | Moves=e2e4,e7e5,g1f3,g1h3,g1h3,g8e7 |
| graceful_quit | ✅ | 0.35 | Exit code 0 |

## Engine: Cecilia_v0.2.0_Enhanced_Fixed.exe
Path: `engines\Cecilia_v0.2.0_Enhanced_Fixed.exe`
Result: PASS (critical tests)
Total Duration: 1.11s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.64 |  |
| uci_handshake | ✅ | 0.06 | id name Cecilia Enhanced v0.2.0
id author GitHub Copilot
option name Hash type spin default 64 min 1 max 2048
option nam |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.01 | bestmove g1h3 |
| first_move_timecontrol | ✅ | 0.01 | bestmove g1h3 |
| multi_sequence | ✅ | 0.03 | Moves=e2e4,e7e5,g1f3,g1h3,g1h3,g8e7 |
| graceful_quit | ✅ | 0.35 | Exit code 0 |

## Engine: Cecilia_v0.3.0_Advanced_Fixed.exe
Path: `engines\Cecilia_v0.3.0_Advanced_Fixed.exe`
Result: PASS (critical tests)
Total Duration: 1.46s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.99 |  |
| uci_handshake | ✅ | 0.06 | id name Cecilia Advanced v0.3.0
id author GitHub Copilot
option name Hash type spin default 64 min 1 max 2048
option nam |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.01 | bestmove g1h3 |
| first_move_timecontrol | ✅ | 0.01 | bestmove g1h3 |
| multi_sequence | ✅ | 0.03 | Moves=e2e4,e7e5,g1f3,g1h3,g1h3,g8e7 |
| graceful_quit | ✅ | 0.35 | Exit code 0 |

## Engine: Random_Opponent.exe
Path: `engines\Random_Opponent.exe`
Result: PASS (critical tests)
Total Duration: 1.02s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.61 |  |
| uci_handshake | ✅ | 0.06 | id name Random Opponent
id author OpponentEngine
uciok |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.00 | bestmove b2b4 |
| first_move_timecontrol | ✅ | 0.00 | bestmove e2e4 |
| multi_sequence | ✅ | 0.00 | Moves=e2e4,e7e5,g1f3,c2c4,f1a6,f1e2 |
| graceful_quit | ✅ | 0.35 | Exit code 0 |

## Engine: SlowMate_v0.0.0.exe
Path: `engines\SlowMate_v0.0.0.exe`
Result: PASS (critical tests)
Total Duration: 2.07s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.61 |  |
| uci_handshake | ✅ | 0.06 | SlowMate v0.0.1 - Pure Random Engine
Educational baseline with no strategic knowledge
Perfect for measuring incremental  |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.17 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.17 | bestmove b1c3 |
| multi_sequence | ✅ | 0.70 | Moves=e2e4,e7e5,g1f3,g1f3,d1h5,g8f6 |
| graceful_quit | ✅ | 0.35 | Exit code 0 |

## Engine: SlowMate_v0.0.1.exe
Path: `engines\SlowMate_v0.0.1.exe`
Result: PASS (critical tests)
Total Duration: 1.20s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.61 |  |
| uci_handshake | ✅ | 0.06 | SlowMate v0.0.2 - Enhanced Intelligence Engine
Features: Tactical awareness + Move intelligence
Notable improvement over |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.03 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.03 | bestmove g1f3 |
| multi_sequence | ✅ | 0.12 | Moves=e2e4,e7e5,g1f3,b1c3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.35 | Exit code 0 |

## Engine: SlowMate_v0.1.0.exe
Path: `engines\SlowMate_v0.1.0.exe`
Result: PASS (critical tests)
Total Duration: 1.98s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.68 |  |
| uci_handshake | ✅ | 0.06 | id name SlowMate 0.1.0
id author Pat Snyder
option name Intelligence type check default true
uciok |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.20 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.21 | bestmove g1f3 |
| multi_sequence | ✅ | 0.77 | Moves=e2e4,e7e5,g1f3,b1c3,d1h5,g8f6 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: SlowMate_v0.1.1.exe
Path: `engines\SlowMate_v0.1.1.exe`
Result: PASS (critical tests)
Total Duration: 1.21s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.62 |  |
| uci_handshake | ✅ | 0.07 | id name SlowMate 0.1.01
id author Pat Snyder
option name Intelligence type check default true
uciok |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.03 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.03 | bestmove g1f3 |
| multi_sequence | ✅ | 0.11 | Moves=e2e4,e7e5,g1f3,g1f3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.35 | Exit code 0 |

## Engine: SlowMate_v0.1.2.exe
Path: `engines\SlowMate_v0.1.2.exe`
Result: PASS (critical tests)
Total Duration: 1.31s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.71 |  |
| uci_handshake | ✅ | 0.05 | ------------------------------------------------------------
SlowMate engine initialized with knowledge base (data: C:\U |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.03 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.03 | bestmove b1c3 |
| multi_sequence | ✅ | 0.12 | Moves=e2e4,e7e5,g1f3,b1c3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.35 | Exit code 0 |

## Engine: SlowMate_v0.1.3.exe
Path: `engines\SlowMate_v0.1.3.exe`
Result: PASS (critical tests)
Total Duration: 1.16s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.62 |  |
| uci_handshake | ✅ | 0.06 | SlowMate engine initialized with knowledge base (data: C:\Users\patss\AppData\Local\Temp\_MEI188002\data)
Opening book:  |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.03 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.03 | bestmove b1c3 |
| multi_sequence | ✅ | 0.12 | Moves=e2e4,e7e5,g1f3,b1c3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.30 | Exit code 0 |

## Engine: SlowMate_v0.2.0.exe
Path: `engines\SlowMate_v0.2.0.exe`
Result: PASS (critical tests)
Total Duration: 1.59s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 1.00 |  |
| uci_handshake | ✅ | 0.06 | SlowMate engine initialized with knowledge base (data: C:\Users\patss\AppData\Local\Temp\_MEI239002\data)
Opening book:  |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.03 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.03 | bestmove b1c3 |
| multi_sequence | ✅ | 0.12 | Moves=e2e4,e7e5,g1f3,g1f3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.35 | Exit code 0 |

## Engine: SlowMate_v0.2.1.exe
Path: `engines\SlowMate_v0.2.1.exe`
Result: PASS (critical tests)
Total Duration: 1.18s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.88 |  |
| uci_handshake | ✅ | 0.06 | SlowMate engine initialized with knowledge base (data: C:\Users\patss\AppData\Local\Temp\_MEI58922\data)
Opening book: T |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.03 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.03 | bestmove g1f3 |
| multi_sequence | ✅ | 0.12 | Moves=e2e4,e7e5,g1f3,b1c3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: SlowMate_v0.2.2.exe
Path: `engines\SlowMate_v0.2.2.exe`
Result: PASS (critical tests)
Total Duration: 1.00s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.70 |  |
| uci_handshake | ✅ | 0.05 | SlowMate engine initialized with knowledge base (data: C:\Users\patss\AppData\Local\Temp\_MEI167362\data)
Opening book:  |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.03 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.03 | bestmove b1c3 |
| multi_sequence | ✅ | 0.13 | Moves=e2e4,e7e5,g1f3,g1f3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: SlowMate_v0.3.0.exe
Path: `engines\SlowMate_v0.3.0.exe`
Result: PASS (critical tests)
Total Duration: 1.67s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.68 |  |
| uci_handshake | ✅ | 0.05 | Endgame tactics: True
Knowledge base ready
SlowMate Chess Engine v0.2.01 by Pat Snyder
id name SlowMate
id author Pat Sn |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.34 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.11 | bestmove g1f3 |
| multi_sequence | ✅ | 0.44 | Moves=e2e4,e7e5,g1f3,b1c3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: SlowMate_v0.3.3.exe
Path: `engines\SlowMate_v0.3.3.exe`
Result: PASS (critical tests)
Total Duration: 1.91s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.91 |  |
| uci_handshake | ✅ | 0.07 | option name RookCoordination type check default true
option name BatteryAttacks type check default true
option name Knig |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.33 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.12 | bestmove g1f3 |
| multi_sequence | ✅ | 0.43 | Moves=e2e4,e7e5,g1f3,b1c3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: SlowMate_v1.0.exe
Path: `engines\SlowMate_v1.0.exe`
Result: PASS (critical tests)
Total Duration: 2.58s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.75 |  |
| uci_handshake | ✅ | 0.06 | info string init complete
SlowMate UCI ready. Type 'uci' to begin.
id name SlowMate
id author Pat Snyder
option name Has |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.26 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.00 | bestmove g1f3 |
| multi_sequence | ❌ | 1.51 | NO_BESTMOVE:Missing move 3 |

## Engine: V7P3RAI_v1.0.exe
Path: `engines\V7P3RAI_v1.0.exe`
Result: FAIL (critical tests)
Total Duration: 3.71s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 1.05 |  |
| uci_handshake | ❌ | 1.54 | TIMEOUT: |
| isready | ✅ | 0.77 | No model found at models/v7p3r_model.pkl, using static evaluation;id name V7P3R Chess AI;id author pssnyder;uciok;readyo |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.01 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.01 | bestmove g1f3 |
| multi_sequence | ✅ | 0.07 | Moves=e2e4,e7e5,g1f3,g1f3,d1h5,e8e7 |
| graceful_quit | ✅ | 0.25 | Exit code 0 |
