# Engine Test Report

Total engines: 35

Critical PASS: 22/35

## Engine: Cece_v1.0.exe
Path: `Functioning_Engines_20250807\Cece_v1.0.exe`
Result: PASS (critical tests)
Total Duration: 5.24s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 1.89 | id name Cece
id author Pat Snyder
option name Debug type check default false
option name Hash type spin default 64 min 1 |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | Initialized Cece v1.0;Author: Pat Snyder;Attribution: Built on python-chess by Niklas Fiekas;readyok |
| first_move_movetime | ✅ | 1.00 | bestmove h2h4 |
| first_move_timecontrol | ✅ | 0.07 | bestmove g1h3 |
| multi_sequence | ✅ | 1.52 | Moves=e2e4,e7e5,g1f3,c2c3,f1a6,d8f6 |
| graceful_quit | ✅ | 0.25 | Exit code 0 |

## Engine: Cece_v1.1.exe
Path: `Functioning_Engines_20250807\Cece_v1.1.exe`
Result: PASS (critical tests)
Total Duration: 3.21s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 0.06 | id name Cece
id author Pat Snyder
option name Debug type check default false
option name Hash type spin default 64 min 1 |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | Initialized Cece v1.1;Author: Pat Snyder;Attribution: Built on python-chess by Niklas Fiekas;readyok |
| first_move_movetime | ✅ | 1.00 | bestmove h2h4 |
| first_move_timecontrol | ✅ | 0.07 | bestmove g1h3 |
| multi_sequence | ✅ | 1.52 | Moves=e2e4,e7e5,g1f3,h2h3,g1h3,d8f6 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: Cece_v1.2.exe
Path: `Functioning_Engines_20250807\Cece_v1.2.exe`
Result: PASS (critical tests)
Total Duration: 3.49s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 0.06 | id name Cece
id author Pat Snyder
option name Debug type check default false
option name Hash type spin default 64 min 1 |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | Initialized Cece v1.1;Author: Pat Snyder;Attribution: Built on python-chess by Niklas Fiekas;readyok |
| first_move_movetime | ✅ | 1.00 | bestmove g1h3 |
| first_move_timecontrol | ✅ | 0.06 | bestmove g1f3 |
| multi_sequence | ✅ | 1.51 | Moves=e2e4,e7e5,g1f3,g2g4,g1f3,g8h6 |
| graceful_quit | ✅ | 0.36 | Exit code 0 |

## Engine: Cece_v1.3.exe
Path: `Functioning_Engines_20250807\Cece_v1.3.exe`
Result: PASS (critical tests)
Total Duration: 5.29s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 1.92 | id name Cece
id author Pat Snyder
option name Debug type check default false
option name Hash type spin default 64 min 1 |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | Initialized Cece v1.3;Author: Pat Snyder;Attribution: Built on python-chess by Niklas Fiekas;readyok |
| first_move_movetime | ✅ | 1.01 | bestmove g1h3 |
| first_move_timecontrol | ✅ | 0.07 | bestmove g1f3 |
| multi_sequence | ✅ | 1.53 | Moves=e2e4,e7e5,g1f3,g1f3,g1f3,g8h6 |
| graceful_quit | ✅ | 0.25 | Exit code 0 |

## Engine: Cecilia_v0.1.0_Basic.exe
Path: `Functioning_Engines_20250807\Cecilia_v0.1.0_Basic.exe`
Result: PASS (critical tests)
Total Duration: 0.93s

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
| graceful_quit | ✅ | 0.30 | Exit code 0 |

## Engine: Cecilia_v0.2.0_Enhanced.exe
Path: `Functioning_Engines_20250807\Cecilia_v0.2.0_Enhanced.exe`
Result: FAIL (critical tests)
Total Duration: 2.58s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 0.07 | id name Cecilia Enhanced v0.2.0
id author GitHub Copilot
option name Hash type spin default 64 min 1 max 2048
option nam |
| isready | ❌ | 2.01 | TIMEOUT:[1056] Failed to execute script 'uci_interface' due to unhandled exception!;Error loading config: expected '<document st |

## Engine: Cecilia_v0.3.0_Advanced.exe
Path: `Functioning_Engines_20250807\Cecilia_v0.3.0_Advanced.exe`
Result: FAIL (critical tests)
Total Duration: 7.70s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 0.07 | id name Cecilia Advanced v0.3.0
id author GitHub Copilot
option name Hash type spin default 64 min 1 max 2048
option nam |
| isready | ✅ | 0.02 | readyok |
| newgame | ✅ | 0.02 | readyok |
| first_move_movetime | ❌ | 2.02 | NO_BESTMOVE: |
| first_move_timecontrol | ❌ | 3.00 | NO_BESTMOVE: |
| multi_sequence | ❌ | 2.01 | NO_BESTMOVE:Missing move 1 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: Interactive_400_ELO.exe
Path: `Functioning_Engines_20250807\Interactive_400_ELO.exe`
Result: FAIL (critical tests)
Total Duration: 3.52s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ❌ | 3.01 | TRACEBACK:Traceback (most recent call last):
  File "elo_400_opponent.py", line 11, in <module>
ModuleNotFoundError: No module nam |

## Engine: Interactive_Opening_1200_ELO.exe
Path: `Functioning_Engines_20250807\Interactive_Opening_1200_ELO.exe`
Result: FAIL (critical tests)
Total Duration: 3.56s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ❌ | 3.06 | TRACEBACK:Traceback (most recent call last):
  File "opening_elo_1200_opponent.py", line 11, in <module>
ModuleNotFoundError: No m |

## Engine: Interactive_Opening_800_ELO.exe
Path: `Functioning_Engines_20250807\Interactive_Opening_800_ELO.exe`
Result: FAIL (critical tests)
Total Duration: 3.55s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ❌ | 3.04 | TRACEBACK:Traceback (most recent call last):
  File "opening_elo_800_opponent.py", line 11, in <module>
ModuleNotFoundError: No mo |

## Engine: Interactive_Opening_Random.exe
Path: `Functioning_Engines_20250807\Interactive_Opening_Random.exe`
Result: FAIL (critical tests)
Total Duration: 3.52s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ❌ | 3.02 | TRACEBACK:Traceback (most recent call last):
  File "opening_random_opponent.py", line 11, in <module>
ModuleNotFoundError: No mod |

## Engine: Interactive_Random_Only.exe
Path: `Functioning_Engines_20250807\Interactive_Random_Only.exe`
Result: FAIL (critical tests)
Total Duration: 3.51s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ❌ | 3.00 | TRACEBACK:Traceback (most recent call last):
  File "random_only_opponent.py", line 11, in <module>
ModuleNotFoundError: No module |

## Engine: OpponentEngine_400_ELO.exe
Path: `Functioning_Engines_20250807\OpponentEngine_400_ELO.exe`
Result: FAIL (critical tests)
Total Duration: 0.51s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ❌ | 0.51 | CRASH:Process not alive |

## Engine: OpponentEngine_Opening_1200_ELO.exe
Path: `Functioning_Engines_20250807\OpponentEngine_Opening_1200_ELO.exe`
Result: FAIL (critical tests)
Total Duration: 0.51s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ❌ | 0.51 | CRASH:Process not alive |

## Engine: OpponentEngine_Opening_800_ELO.exe
Path: `Functioning_Engines_20250807\OpponentEngine_Opening_800_ELO.exe`
Result: FAIL (critical tests)
Total Duration: 0.51s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ❌ | 0.51 | CRASH:Process not alive |

## Engine: OpponentEngine_Opening_Random.exe
Path: `Functioning_Engines_20250807\OpponentEngine_Opening_Random.exe`
Result: FAIL (critical tests)
Total Duration: 0.51s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ❌ | 0.51 | CRASH:Process not alive |

## Engine: OpponentEngine_Random_Only.exe
Path: `Functioning_Engines_20250807\OpponentEngine_Random_Only.exe`
Result: FAIL (critical tests)
Total Duration: 0.51s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ❌ | 0.51 | CRASH:Process not alive |

## Engine: SlowMate_v0.0.0_DELTA.exe
Path: `Functioning_Engines_20250807\SlowMate_v0.0.0_DELTA.exe`
Result: PASS (critical tests)
Total Duration: 1.83s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 0.07 | SlowMate v0.0.1 - Pure Random Engine
Educational baseline with no strategic knowledge
Perfect for measuring incremental  |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.16 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.15 | bestmove g1f3 |
| multi_sequence | ✅ | 0.64 | Moves=e2e4,e7e5,g1f3,g1f3,d1h5,g8f6 |
| graceful_quit | ✅ | 0.32 | Exit code 0 |

## Engine: SlowMate_v0.0.10_Tactical_Intelligence.exe
Path: `Functioning_Engines_20250807\SlowMate_v0.0.10_Tactical_Intelligence.exe`
Result: PASS (critical tests)
Total Duration: 1.05s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 0.06 | SlowMate v0.0.2 - Enhanced Intelligence Engine
Features: Tactical awareness + Move intelligence
Notable improvement over |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.03 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.03 | bestmove g1f3 |
| multi_sequence | ✅ | 0.11 | Moves=e2e4,e7e5,g1f3,b1c3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.31 | Exit code 0 |

## Engine: SlowMate_v0.1.01_Tactics.exe
Path: `Functioning_Engines_20250807\SlowMate_v0.1.01_Tactics.exe`
Result: PASS (critical tests)
Total Duration: 1.03s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 0.06 | id name SlowMate 0.1.01
id author Pat Snyder
option name Intelligence type check default true
uciok |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.02 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.03 | bestmove g1f3 |
| multi_sequence | ✅ | 0.11 | Moves=e2e4,e7e5,g1f3,b1c3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.31 | Exit code 0 |

## Engine: SlowMate_v0.1.02_Opening_Endgame.exe
Path: `Functioning_Engines_20250807\SlowMate_v0.1.02_Opening_Endgame.exe`
Result: PASS (critical tests)
Total Duration: 1.03s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 0.06 | ------------------------------------------------------------
SlowMate engine initialized with knowledge base (data: C:\U |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.03 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.03 | bestmove b1c3 |
| multi_sequence | ✅ | 0.10 | Moves=e2e4,e7e5,g1f3,b1c3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.32 | Exit code 0 |

## Engine: SlowMate_v0.1.03_Middlegame.exe
Path: `Functioning_Engines_20250807\SlowMate_v0.1.03_Middlegame.exe`
Result: PASS (critical tests)
Total Duration: 1.04s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 0.06 | SlowMate engine initialized with knowledge base (data: C:\Users\patss\AppData\Local\Temp\_MEI183442\data)
Opening book:  |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.02 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.03 | bestmove g1f3 |
| multi_sequence | ✅ | 0.11 | Moves=e2e4,e7e5,g1f3,g1f3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.31 | Exit code 0 |

## Engine: SlowMate_v0.1.0_BETA.exe
Path: `Functioning_Engines_20250807\SlowMate_v0.1.0_BETA.exe`
Result: PASS (critical tests)
Total Duration: 1.68s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.06 | id name SlowMate 0.1.0
id author Pat Snyder
option name Intelligence type check default true
uciok |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.17 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.17 | bestmove g1f3 |
| multi_sequence | ✅ | 0.72 | Moves=e2e4,e7e5,g1f3,g1f3,d1h5,g8f6 |
| graceful_quit | ✅ | 0.06 | Exit code 0 |

## Engine: SlowMate_v0.2.01_Enhanced_Search.exe
Path: `Functioning_Engines_20250807\SlowMate_v0.2.01_Enhanced_Search.exe`
Result: PASS (critical tests)
Total Duration: 0.79s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.05 | SlowMate engine initialized with knowledge base (data: C:\Users\patss\AppData\Local\Temp\_MEI64162\data)
Opening book: T |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.02 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.04 | bestmove b1c3 |
| multi_sequence | ✅ | 0.12 | Moves=e2e4,e7e5,g1f3,g1f3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: SlowMate_v0.2.02_Time_Management.exe
Path: `Functioning_Engines_20250807\SlowMate_v0.2.02_Time_Management.exe`
Result: PASS (critical tests)
Total Duration: 0.81s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.07 | SlowMate engine initialized with knowledge base (data: C:\Users\patss\AppData\Local\Temp\_MEI169522\data)
Opening book:  |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.03 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.02 | bestmove g1f3 |
| multi_sequence | ✅ | 0.12 | Moves=e2e4,e7e5,g1f3,b1c3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.06 | Exit code 0 |

## Engine: SlowMate_v0.2.0_BETA.exe
Path: `Functioning_Engines_20250807\SlowMate_v0.2.0_BETA.exe`
Result: PASS (critical tests)
Total Duration: 1.11s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 0.07 | SlowMate engine initialized with knowledge base (data: C:\Users\patss\AppData\Local\Temp\_MEI99402\data)
Opening book: T |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.03 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.02 | bestmove b1c3 |
| multi_sequence | ✅ | 0.12 | Moves=e2e4,e7e5,g1f3,b1c3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.36 | Exit code 0 |

## Engine: SlowMate_v0.3.01_Opening_Enhancements.exe
Path: `Functioning_Engines_20250807\SlowMate_v0.3.01_Opening_Enhancements.exe`
Result: PASS (critical tests)
Total Duration: 1.51s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 0.07 | Endgame tactics: True
Knowledge base ready
SlowMate Chess Engine v0.2.01 by Pat Snyder
id name SlowMate
id author Pat Sn |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.33 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.14 | bestmove b1c3 |
| multi_sequence | ✅ | 0.41 | Moves=e2e4,e7e5,g1f3,g1f3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: SlowMate_v0.3.02_Enhanced_Endgame.exe
Path: `Functioning_Engines_20250807\SlowMate_v0.3.02_Enhanced_Endgame.exe`
Result: PASS (critical tests)
Total Duration: 1.50s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 0.06 | Endgame tactics: True
Knowledge base ready
SlowMate Chess Engine v0.2.01 by Pat Snyder
id name SlowMate
id author Pat Sn |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.31 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.13 | bestmove b1c3 |
| multi_sequence | ✅ | 0.42 | Moves=e2e4,e7e5,g1f3,g1f3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.06 | Exit code 0 |

## Engine: SlowMate_v0.3.03_Version_vs_Version_Nuclear_Fix.exe
Path: `Functioning_Engines_20250807\SlowMate_v0.3.03_Version_vs_Version_Nuclear_Fix.exe`
Result: PASS (critical tests)
Total Duration: 1.50s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.05 | option name RookCoordination type check default true
option name BatteryAttacks type check default true
option name Knig |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.33 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.15 | bestmove b1c3 |
| multi_sequence | ✅ | 0.40 | Moves=e2e4,e7e5,g1f3,b1c3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.06 | Exit code 0 |

## Engine: SlowMate_v0.3.0_BETA.exe
Path: `Functioning_Engines_20250807\SlowMate_v0.3.0_BETA.exe`
Result: PASS (critical tests)
Total Duration: 1.50s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 0.06 | Endgame tactics: True
Knowledge base ready
SlowMate Chess Engine v0.2.01 by Pat Snyder
id name SlowMate
id author Pat Sn |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.31 | bestmove g1f3 |
| first_move_timecontrol | ✅ | 0.13 | bestmove g1f3 |
| multi_sequence | ✅ | 0.42 | Moves=e2e4,e7e5,g1f3,g1f3,f1c4,f8a3 |
| graceful_quit | ✅ | 0.06 | Exit code 0 |

## Engine: SlowMate_v0.4.01_uci_standardization.exe
Path: `Functioning_Engines_20250807\SlowMate_v0.4.01_uci_standardization.exe`
Result: FAIL (critical tests)
Total Duration: 4.64s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.06 | option name Debug Log File type string default 
option name UCI_AnalyseMode type check default false
option name UCI_Lim |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ❌ | 2.01 | NO_BESTMOVE:info depth 1 seldepth 1 multipv 1 score cp 0 nodes 20 nps 20000 time 0 pv b1a3;info string Material evaluation: 0.00;inf |
| first_move_timecontrol | ✅ | 0.00 | bestmove b1a3 |
| multi_sequence | ❌ | 2.01 | NO_BESTMOVE:Missing move 1 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: SlowMate_v0.4.02_Time_Revision.exe
Path: `Functioning_Engines_20250807\SlowMate_v0.4.02_Time_Revision.exe`
Result: PASS (critical tests)
Total Duration: 1.82s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 0.05 | option name Show Evaluation Details type check default true
option name Show Material Count type check default true
opti |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.26 | bestmove b1c3 |
| first_move_timecontrol | ✅ | 0.16 | bestmove a2a3 |
| multi_sequence | ✅ | 0.79 | Moves=e2e4,e7e5,g1f3,e2e4,f2f3,c7c5 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: SlowMate_v0.4.03_Stable_Baseline.exe
Path: `Functioning_Engines_20250807\SlowMate_v0.4.03_Stable_Baseline.exe`
Result: PASS (critical tests)
Total Duration: 2.68s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 0.07 | option name Show Evaluation Details type check default true
option name Show Material Count type check default true
opti |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.41 | bestmove h2h3 |
| first_move_timecontrol | ✅ | 0.41 | bestmove g1h3 |
| multi_sequence | ✅ | 1.23 | Moves=e2e4,e7e5,g1f3,c2c4,c2c3,b8a6 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: SlowMate_v0.4.0_BETA.exe
Path: `Functioning_Engines_20250807\SlowMate_v0.4.0_BETA.exe`
Result: PASS (critical tests)
Total Duration: 0.64s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 0.08 | id name SlowMate 0.1.0
id author SlowMate Development Team
uciok |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.00 | bestmove h2h4 |
| first_move_timecontrol | ✅ | 0.00 | bestmove b1a3 |
| multi_sequence | ✅ | 0.00 | Moves=e2e4,e7e5,g1f3,e2e4,d1e2,b8c6 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |

## Engine: SlowMate_v0.5.0_BETA.exe
Path: `Functioning_Engines_20250807\SlowMate_v0.5.0_BETA.exe`
Result: PASS (critical tests)
Total Duration: 1.03s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.51 |  |
| uci_handshake | ✅ | 0.06 | option name Show Evaluation Details type check default true
option name Show Material Count type check default true
opti |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | readyok |
| first_move_movetime | ✅ | 0.08 | bestmove g1h3 |
| first_move_timecontrol | ✅ | 0.08 | bestmove g1h3 |
| multi_sequence | ✅ | 0.25 | Moves=e2e4,e7e5,g1f3,g1h3,g1h3,g8e7 |
| graceful_quit | ✅ | 0.05 | Exit code 0 |
