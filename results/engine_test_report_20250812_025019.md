# Engine Test Report

Total engines: 22

Critical PASS: 22/22

## Engine: Cece_v1.0.exe
Path: `engines\Cece_v1.0.exe`
Result: PASS (critical tests)
Total Duration: 5.30s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 1.97 | id name Cece
id author Pat Snyder
option name Debug type check default false
option name Hash type spin default 64 min 1 |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | Initialized Cece v1.0;Author: Pat Snyder;Attribution: Built on python-chess by Niklas Fiekas;readyok |
| first_move_movetime | ✅ | 1.00 | bestmove c2c4 |
| first_move_timecontrol | ✅ | 0.07 | bestmove g1h3 |
| multi_sequence | ✅ | 1.50 | Moves=e2e4,e7e5,g1f3,b2b3,g1h3,d8f6 |
| graceful_quit | ✅ | 0.25 | Exit code 0 |

## Engine: Cece_v1.1.exe
Path: `engines\Cece_v1.1.exe`
Result: PASS (critical tests)
Total Duration: 3.18s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.05 | id name Cece
id author Pat Snyder
option name Debug type check default false
option name Hash type spin default 64 min 1 |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | Initialized Cece v1.1;Author: Pat Snyder;Attribution: Built on python-chess by Niklas Fiekas;readyok |
| first_move_movetime | ✅ | 1.00 | bestmove f2f4 |
| first_move_timecontrol | ✅ | 0.07 | bestmove g1h3 |
| multi_sequence | ✅ | 1.50 | Moves=e2e4,e7e5,g1f3,e2e3,g1h3,d8f6 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: Cece_v1.2.exe
Path: `engines\Cece_v1.2.exe`
Result: PASS (critical tests)
Total Duration: 3.48s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.05 | id name Cece
id author Pat Snyder
option name Debug type check default false
option name Hash type spin default 64 min 1 |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | Initialized Cece v1.1;Author: Pat Snyder;Attribution: Built on python-chess by Niklas Fiekas;readyok |
| first_move_movetime | ✅ | 1.00 | bestmove g1h3 |
| first_move_timecontrol | ✅ | 0.07 | bestmove g1f3 |
| multi_sequence | ✅ | 1.50 | Moves=e2e4,e7e5,g1f3,g1f3,g1h3,g8h6 |
| graceful_quit | ✅ | 0.35 | Exit code 0 |

## Engine: Cece_v1.3.exe
Path: `engines\Cece_v1.3.exe`
Result: PASS (critical tests)
Total Duration: 5.21s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 1.88 | id name Cece
id author Pat Snyder
option name Debug type check default false
option name Hash type spin default 64 min 1 |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | Initialized Cece v1.3;Author: Pat Snyder;Attribution: Built on python-chess by Niklas Fiekas;readyok |
| first_move_movetime | ✅ | 1.00 | bestmove g1h3 |
| first_move_timecontrol | ✅ | 0.07 | bestmove f2f3 |
| multi_sequence | ✅ | 1.50 | Moves=e2e4,e7e5,g1f3,g1f3,g1f3,g8h6 |
| graceful_quit | ✅ | 0.25 | Exit code 0 |

## Engine: Cece_v2.0.exe
Path: `engines\Cece_v2.0.exe`
Result: PASS (critical tests)
Total Duration: 3.18s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.05 | id name Cece
id author Pat Snyder
option name Debug type check default false
option name Hash type spin default 64 min 1 |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | Initialized Cece v2.0;Author: Pat Snyder;Attribution: Built on python-chess by Niklas Fiekas;readyok |
| first_move_movetime | ✅ | 1.00 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.07 | bestmove g1f3 |
| multi_sequence | ✅ | 1.50 | Moves=e2e4,e7e5,g1f3,g1f3,d2d4,d7d5 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: Cecilia_v0.1.0_Basic.exe
Path: `engines\Cecilia_v0.1.0_Basic.exe`
Result: PASS (critical tests)
Total Duration: 0.97s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.06 | id name Viper Basic v0.1.0
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
Total Duration: 0.97s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
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
Total Duration: 0.96s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.05 | id name Cecilia Advanced v0.3.0
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
Total Duration: 0.92s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.06 | id name Random Opponent
id author OpponentEngine
uciok |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.00 | bestmove g2g3 |
| first_move_timecontrol | ✅ | 0.00 | bestmove e2e4 |
| multi_sequence | ✅ | 0.00 | Moves=e2e4,e7e5,g1f3,e2e3,a2a4,c7c5 |
| graceful_quit | ✅ | 0.35 | Exit code 0 |

## Engine: SlowMate_v0.0.0.exe
Path: `engines\SlowMate_v0.0.0.exe`
Result: PASS (critical tests)
Total Duration: 1.89s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.06 | SlowMate v0.0.1 - Pure Random Engine
Educational baseline with no strategic knowledge
Perfect for measuring incremental  |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.16 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.17 | bestmove b1c3 |
| multi_sequence | ✅ | 0.64 | Moves=e2e4,e7e5,g1f3,g1f3,d1h5,g8f6 |
| graceful_quit | ✅ | 0.35 | Exit code 0 |

## Engine: SlowMate_v0.0.1.exe
Path: `engines\SlowMate_v0.0.1.exe`
Result: PASS (critical tests)
Total Duration: 1.09s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.07 | SlowMate v0.0.2 - Enhanced Intelligence Engine
Features: Tactical awareness + Move intelligence
Notable improvement over |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.03 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.03 | bestmove g1f3 |
| multi_sequence | ✅ | 0.11 | Moves=e2e4,e7e5,g1f3,g1f3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.35 | Exit code 0 |

## Engine: SlowMate_v0.1.0.exe
Path: `engines\SlowMate_v0.1.0.exe`
Result: PASS (critical tests)
Total Duration: 1.69s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.05 | id name SlowMate 0.1.0
id author Pat Snyder
option name Intelligence type check default true
uciok |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.18 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.18 | bestmove g1f3 |
| multi_sequence | ✅ | 0.72 | Moves=e2e4,e7e5,g1f3,g1f3,d1h5,g8f6 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: SlowMate_v0.1.1.exe
Path: `engines\SlowMate_v0.1.1.exe`
Result: PASS (critical tests)
Total Duration: 1.08s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.06 | id name SlowMate 0.1.01
id author Pat Snyder
option name Intelligence type check default true
uciok |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.03 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.03 | bestmove b1c3 |
| multi_sequence | ✅ | 0.11 | Moves=e2e4,e7e5,g1f3,g1f3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.35 | Exit code 0 |

## Engine: SlowMate_v0.1.2.exe
Path: `engines\SlowMate_v0.1.2.exe`
Result: PASS (critical tests)
Total Duration: 1.08s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.05 | ------------------------------------------------------------
SlowMate engine initialized with knowledge base (data: C:\U |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.03 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.03 | bestmove b1c3 |
| multi_sequence | ✅ | 0.11 | Moves=e2e4,e7e5,g1f3,g1f3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.35 | Exit code 0 |

## Engine: SlowMate_v0.1.3.exe
Path: `engines\SlowMate_v0.1.3.exe`
Result: PASS (critical tests)
Total Duration: 1.09s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.06 | SlowMate engine initialized with knowledge base (data: C:\Users\patss\AppData\Local\Temp\_MEI211762\data)
Opening book:  |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.03 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.03 | bestmove g1f3 |
| multi_sequence | ✅ | 0.12 | Moves=e2e4,e7e5,g1f3,g1f3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.35 | Exit code 0 |

## Engine: SlowMate_v0.2.0.exe
Path: `engines\SlowMate_v0.2.0.exe`
Result: PASS (critical tests)
Total Duration: 1.08s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.05 | SlowMate engine initialized with knowledge base (data: C:\Users\patss\AppData\Local\Temp\_MEI50882\data)
Opening book: T |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.03 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.03 | bestmove b1c3 |
| multi_sequence | ✅ | 0.12 | Moves=e2e4,e7e5,g1f3,g1f3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.35 | Exit code 0 |

## Engine: SlowMate_v0.2.1.exe
Path: `engines\SlowMate_v0.2.1.exe`
Result: PASS (critical tests)
Total Duration: 0.80s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.06 | SlowMate engine initialized with knowledge base (data: C:\Users\patss\AppData\Local\Temp\_MEI208042\data)
Opening book:  |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.03 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.03 | bestmove g1f3 |
| multi_sequence | ✅ | 0.12 | Moves=e2e4,e7e5,g1f3,b1c3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: SlowMate_v0.2.2.exe
Path: `engines\SlowMate_v0.2.2.exe`
Result: PASS (critical tests)
Total Duration: 0.80s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.05 | SlowMate engine initialized with knowledge base (data: C:\Users\patss\AppData\Local\Temp\_MEI167202\data)
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
Total Duration: 1.47s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.06 | Endgame tactics: True
Knowledge base ready
SlowMate Chess Engine v0.2.01 by Pat Snyder
id name SlowMate
id author Pat Sn |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.32 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.13 | bestmove b1c3 |
| multi_sequence | ✅ | 0.42 | Moves=e2e4,e7e5,g1f3,g1f3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: SlowMate_v0.3.3.exe
Path: `engines\SlowMate_v0.3.3.exe`
Result: PASS (critical tests)
Total Duration: 1.49s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.06 | option name RookCoordination type check default true
option name BatteryAttacks type check default true
option name Knig |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.32 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.12 | bestmove g1f3 |
| multi_sequence | ✅ | 0.45 | Moves=e2e4,e7e5,g1f3,b1c3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: SlowMate_v1.0.exe
Path: `engines\SlowMate_v1.0.exe`
Result: PASS (critical tests)
Total Duration: 5.35s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.06 | info string init complete
SlowMate UCI ready. Type 'uci' to begin.
id name SlowMate
id author Pat Snyder
option name Has |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.27 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.00 | bestmove g1f3 |
| multi_sequence | ❌ | 4.52 | NO_BESTMOVE:Missing move 3 |

## Engine: V7P3RAI_v1.0.exe
Path: `engines\V7P3RAI_v1.0.exe`
Result: PASS (critical tests)
Total Duration: 2.99s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 2.15 | Error loading config: [Errno 2] No such file or directory: 'config.json'
No model found at models/v7p3r_model.pkl, using |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.01 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.01 | bestmove g1f3 |
| multi_sequence | ✅ | 0.07 | Moves=e2e4,e7e5,g1f3,g1f3,d1h5,e8e7 |
| graceful_quit | ✅ | 0.25 | Exit code 0 |
