# Chess Engine Tester & Tournament Analyzer

Test (batch) verify Windows chess engine `.exe` builds for basic UCI and Arena GUI compatibility **before** installing them.

## Goals

1. Quickly find broken builds (hang on start, never move, wrong protocol, crash, illegal move, timeout).
2. Produce a concise report ranking readiness & listing concrete failures.
3. Be engine‑agnostic (any UCI engine .exe in the target folder).

## Current Test Battery (v0.1)

Each engine is executed in a fresh process and the following staged tests run with timeouts:

| Stage | Name | Purpose | Pass Criteria | Default Timeout |
|-------|------|---------|---------------|-----------------|
| 1 | launch | Process spawn & pipe open | Process alive after 0.5s | 2s |
| 2 | uci_handshake | Basic UCI identity/options | Receive `uciok` after `uci` | 3s |
| 3 | isready | Engine responds ready | Receive `readyok` | 2s |
| 4 | newgame | Accepts `ucinewgame` then `isready` | `readyok` | 2s |
| 5 | first_move_movetime | Produces a move quickly | Line `bestmove <move>` (legal format) after `go movetime 1000` | 2s (1s search + slack) |
| 6 | first_move_timecontrol | Handles wtime/btime | `bestmove` within allotted soft timeout | 3s |
| 7 | multi_sequence | Responds to a short forced line (e2e4 e7e5 g1f3) alternating searches | All 3 bestmoves produced | 6s total |
| 8 | graceful_quit | Accepts `quit` | Process exits within timeout | 2s |

Failures are categorized: `TIMEOUT`, `NO_BESTMOVE`, `CRASH`, `PROTOCOL`, `ILLEGAL_MOVE`, `OTHER`.

## Output Report

Generates `engine_test_report_<timestamp>.md` + JSON summary `engine_test_report_<timestamp>.json` in the results directory.

Per engine you get:

```
### Engine: SlowMate_v0.4.03_Stable_Baseline.exe
Result: PASS (7/7 critical tests)
Launch: OK (0.12s)
UCI Handshake: OK (id name SlowMate ...)
...
Issues: (none)
```

Critical tests (handshake, readiness, ability to make at least one move) determine PASS/FAIL. Non‑critical (multi sequence, graceful quit) flagged but do not alone mark a build irredeemable.

## Directory Scanned

Default: `Functioning_Engines_20250807/` (sibling directory to this README). All `*.exe` files included. You can exclude patterns (see CLI options).

## Usage

1. Ensure Python 3.9+ is installed (Windows).
2. Place this folder next to the engine executables directory as shown.
3. Run the tester:

```bash
python engine_tester.py --dir ../Functioning_Engines_20250807 --parallel 1 --timeout-scale 1.0
```

### CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--dir DIR` | `../Functioning_Engines_20250807` | Directory containing engine exes |
| `--include PATTERN` | `*.exe` | Glob for engines (repeatable) |
| `--exclude PATTERN` | (none) | Exclusion glob (repeatable) |
| `--parallel N` | 1 | How many engines to test in parallel (set >1 cautiously) |
| `--timeout-scale F` | 1.0 | Multiply all timeouts (e.g. slow debug builds) |
| `--json PATH` | auto | Override JSON report path |
| `--md PATH` | auto | Override Markdown report path |
| `--max-move-ms` | 1500 | Hard cap (ms) to wait for a single move (post search command) |

## Interpreting Failures

- `TIMEOUT uci_handshake`: Engine stuck before producing `uciok`. Verify it prints lines to stdout (not only stderr) & flushes.
- `NO_BESTMOVE`: Engine never printed `bestmove` line; ensure it handles the `go` parameters used.
- `ILLEGAL_MOVE`: Returned move fails basic SAN/UCI regex or not legal in position (simple legality validator may be added later). For now only regex is checked.
- `CRASH`: Process exited early (non-zero code) during test.

## Roadmap / Next Steps

- [ ] PGN scripted mini matches between engines for deeper stability check.
- [ ] Option discovery & per-option probing (e.g., set hash size, threads, custom engine params) + rollback detection.
- [ ] Enhanced legality validation via lightweight move generator (avoid integrating full chess engine library unless needed).
- [ ] Logging raw protocol transcript per engine to `logs/<engine>.log`.
- [ ] Arena specific quirk tests (ponder, analyze mode, draw offers, `setoption` endurance).
- [ ] Crash dump capture & retry logic.

## Contributing / Extending

Add new stages by editing `TEST_STAGES` in `engine_tester.py`. Each stage is a callable receiving the `UCIEngine` wrapper and returning a `StageResult`.

## Safety Note

The tester executes arbitrary `.exe` files you place in the directory. Only run it on binaries you trust.

## License

Personal project; adapt freely for your own engines.

---

Run the script now to generate your first readiness report.

Happy testing!
