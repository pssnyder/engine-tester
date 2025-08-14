# Engine Test Report

Total engines: 1

Critical PASS: 0/1

## Engine: Cece_v2.1.exe
Path: `engines\Cece_v2.1.exe`
Result: FAIL (critical tests)
Total Duration: 3.02s

| Stage | OK | Time (s) | Detail |
|-------|----|----------|--------|
| launch | ✅ | 0.50 |  |
| uci_handshake | ✅ | 2.24 | id name Cece
id author Pat Snyder
option name Debug type check default false
option name Hash type spin default 64 min 1 |
| isready | ✅ | 0.00 | readyok |
| newgame | ✅ | 0.00 | Initialized Cece v2.0;Author: Pat Snyder;Attribution: Built on python-chess by Niklas Fiekas;readyok |
| first_move_movetime | ❌ | 0.01 | ILLEGAL_MOVE:bestmove 0000 |
| first_move_timecontrol | ❌ | 0.00 | ILLEGAL_MOVE:bestmove 0000 |
| multi_sequence | ❌ | 0.01 | ILLEGAL_MOVE:Bad move line bestmove 0000 |
| graceful_quit | ✅ | 0.25 | Exit code 0 |
