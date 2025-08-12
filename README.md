# Chess Engine Tester & Tournament Analyzer

A comprehensive system for testing chess engines and analyzing tournament performance with advanced rating calculations, name consolidation, and visual analytics.

## 🎯 Goals

1. **Engine Testing**: Quickly find broken builds (hang on start, never move, wrong protocol, crash, illegal move, timeout).
2. **Tournament Analysis**: Comprehensive cross-tournament performance analysis with opponent-strength-adjusted ratings.
3. **Rating System**: Advanced ELO calculation with manual rating overrides for accurate baselines.
4. **Name Consolidation**: Intelligent engine name normalization to properly group engine variants.
5. **Visual Dashboard**: Interactive Streamlit dashboard for exploring engine performance and rankings.

## 🚀 Features

### Engine Testing (Original Functionality)
- UCI protocol compliance testing
- Basic functionality verification
- Timeout and crash detection
- Detailed failure categorization

### Tournament Analysis System ⭐ NEW
- **Cross-tournament aggregate statistics**
- **Opponent-strength-adjusted scoring**
- **Unified ranking system across all engines**
- **Head-to-head performance matrices**
- **Statistical significance weighting**
- **Manual rating override system**

### Name Consolidation & Rating System ⭐ NEW
- **Intelligent engine name normalization**
- **Manual consolidation mapping**
- **Rating override system for accurate baselines**
- **Stockfish strength-based rating anchoring**

### Interactive Dashboard ⭐ NEW
- **Real-time tournament analytics**
- **Engine performance visualization**
- **Rating distribution charts**
- **Consolidation status tracking**
- **Filter and search capabilities**

## 📁 Project Structure

```
engine-tester/
├── engine_tester.py              # Original engine testing tool
├── tournament_analyzer.py        # Individual tournament analysis
├── unified_tournament_analyzer.py # Cross-tournament unified analysis ⭐
├── dashboard.py                   # Interactive Streamlit dashboard ⭐
├── name_mapper.py                # Engine name normalization system ⭐
├── results/
│   ├── name_consolidation.json   # Manual name mapping & rating overrides ⭐
│   ├── unified_tournament_analysis.json  # Comprehensive analysis results ⭐
│   └── [tournament folders]/
└── engines/                      # Engine executables
```

## 🏃 Quick Start

### 1. Basic Engine Testing
Test engine executables for UCI compliance:

```bash
python engine_tester.py --dir ../engines --parallel 1
```

### 2. Tournament Analysis ⭐
Analyze all tournaments and generate unified rankings:

```bash
python unified_tournament_analyzer.py
```

### 3. Interactive Dashboard ⭐
Launch the visual analytics dashboard:

```bash
streamlit run dashboard.py
```

## 📊 Tournament Analysis System

### Core Features

**Unified Analysis**: Processes all PGN files across tournament directories to create comprehensive engine performance metrics.

**Smart Name Consolidation**: Automatically groups engine variants (e.g., `SlowMate_v1.0`, `SlowMate v1.0`, `SlowMate_v1.0_RELEASE`) under canonical names.

**Advanced Rating System**: 
- Iterative ELO-like calculation considering opponent strength
- Manual rating overrides for known engine strengths
- Stockfish anchoring with proper strength-based ratings

### Usage

```bash
# Run comprehensive analysis
python unified_tournament_analyzer.py

# Output: results/unified_tournament_analysis.json
```

### Sample Output
```
🏆 TOP ENGINE RANKINGS (Estimated Rating):
============================================================
 1. Stockfish 3645                 3645 ELO ( 30 games, 100.0% wins)
 2. Stockfish 2650                 2650 ELO (170 games,  97.6% wins)
 3. SlowMate 1.0                   1251 ELO (296 games,  76.7% wins)
 4. SlowMate 0.0                   1230 ELO (819 games,  55.1% wins)
```

## 🎛️ Rating Override System ⭐

### Manual Rating Control
Set exact ELO ratings for engines where you know their approximate strength via the `results/name_consolidation.json` file.

### Configuration Format
```json
{
  "name_consolidation": {
    "consolidations": {
      "Stockfish 3645": {
        "variants": ["Stockfish"],
        "rating_override": 3645
      },
      "Stockfish 2650": {
        "variants": ["Stockfish_1%", "Stockfish 1%"],
        "rating_override": 2650
      },
      "SlowMate 1.0": {
        "variants": ["SlowMate_v1.0", "SlowMate v1.0"],
        "rating_override": 1300
      }
    }
  }
}
```

### Benefits
- **Accurate Baselines**: Known engine strengths anchor the rating system
- **Easy Tuning**: Just edit the JSON file and re-run the analyzer  
- **Progressive Refinement**: Add overrides as you gather more data
- **Stability**: Manual overrides prevent rating drift in iterative calculations

### Protected Ratings
Engines with manual rating overrides are protected from adjustment during iterative rating calculations, ensuring consistent baselines.

## 📈 Interactive Dashboard

### Launch Dashboard
```bash
streamlit run dashboard.py
```

### Features
- **Engine Rankings**: Sortable tables with ELO ratings, games played, win rates
- **Performance Charts**: Scatter plots, bar charts, rating distributions
- **Filter Options**: 
  - Top 20 Engines
  - All Non-SlowMate Engines  
  - SlowMate Only
  - Custom name filtering
- **Consolidation Tracking**: Visual indicators for consolidated engines
- **Stockfish Achievements**: Special tracking for engines with notable Stockfish results

### Dashboard Sections
1. **📊 Engine Rankings**: Comprehensive performance tables
2. **📈 Performance Analysis**: Visual charts and trends
3. **⚔️ Stockfish Analysis**: Dedicated section for Stockfish performance tracking
4. **🔗 Consolidation Summary**: Name mapping and grouping statistics

## 🛠️ Engine Name Consolidation

### Automatic Normalization
The system automatically handles common engine name variations:
- Version format differences (`v1.0` vs `1.0`)
- Underscore vs space variants (`SlowMate_v1.0` vs `SlowMate v1.0`)
- Common suffixes (`_RELEASE`, `_BETA`, `_ENHANCED`, etc.)

### Manual Mapping
For complex cases, use the manual mapping system in `results/name_consolidation.json`:

```json
"SlowMate 0.1": [
  "SlowMate_v0.1.0",
  "SlowMate_v0.1.01", 
  "SlowMate_v0.1.02",
  "SlowMate_v0.1.0_BETA",
  "Slowmate_v0.1.01_beta"
]
```

### Test Name Mapping
```bash
python name_mapper.py
```

## 🧪 Original Engine Testing

### Test Battery
Each engine is executed in a fresh process with the following staged tests:

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

### Failure Categories
- `TIMEOUT`: Engine didn't respond within time limit
- `NO_BESTMOVE`: Engine never produced a move
- `CRASH`: Process exited unexpectedly  
- `PROTOCOL`: UCI protocol violation
- `ILLEGAL_MOVE`: Move format issues
- `OTHER`: Unclassified failures

### CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--dir DIR` | `../engines` | Directory containing engine exes |
| `--include PATTERN` | `*.exe` | Glob for engines (repeatable) |
| `--exclude PATTERN` | (none) | Exclusion glob (repeatable) |
| `--parallel N` | 1 | How many engines to test in parallel |
| `--timeout-scale F` | 1.0 | Multiply all timeouts |
| `--json PATH` | auto | Override JSON report path |
| `--md PATH` | auto | Override Markdown report path |
| `--max-move-ms` | 1500 | Hard cap (ms) to wait for a single move |

### Sample Output
```
### Engine: SlowMate_v0.4.03_Stable_Baseline.exe
Result: PASS (7/7 critical tests)
Launch: OK (0.12s)
UCI Handshake: OK (id name SlowMate ...)
...
Issues: (none)
```

## 🔧 Advanced Configuration

### Rating Override Examples

Add these to your `results/name_consolidation.json`:

```json
{
  "name_consolidation": {
    "consolidations": {
      "Stockfish 3645": {
        "variants": ["Stockfish"],
        "rating_override": 3645
      },
      "Stockfish 2650": {
        "variants": ["Stockfish_1%", "Stockfish 1%"],
        "rating_override": 2650
      },
      "SlowMate 1.0": {
        "variants": ["SlowMate_v1.0", "SlowMate v1.0", "SlowMate_v1.0_RELEASE"],
        "rating_override": 1300
      },
      "Random Playing Opponent": {
        "variants": ["Random_Opponent", "Random Playing Opponent"],
        "rating_override": 600
      }
    }
  }
}
```

### Workflow Integration

**Typical Development Workflow:**
1. **Test New Engine**: `python engine_tester.py --dir engines --include "MyEngine_v*.exe"`
2. **Run Tournaments**: Use Arena GUI or cutechess-cli to generate PGN files
3. **Analyze Performance**: `python unified_tournament_analyzer.py` 
4. **Review Results**: `streamlit run dashboard.py`
5. **Tune Ratings**: Add rating overrides to `name_consolidation.json` as needed
6. **Iterate**: Repeat analysis with updated baselines

## 📋 Output Files

### Generated Reports
- `results/engine_test_report_<timestamp>.md` - Engine testing report
- `results/engine_test_report_<timestamp>.json` - Testing data  
- `results/unified_tournament_analysis.json` - Comprehensive tournament analysis ⭐
- `results/name_consolidation.json` - Manual name mapping configuration ⭐

### Tournament Data Structure
```json
{
  "analysis_date": "2025-08-11T23:25:17.493301",
  "consolidation_summary": {
    "consolidated_engines": 21,
    "total_raw_names": 96,
    "consolidated_groups": {...}
  },
  "unified_rankings": [
    {
      "rank": 1,
      "name": "Stockfish 3645", 
      "estimated_rating": 3645.0,
      "games": 30,
      "win_rate": 100.0,
      "tournaments": 8,
      "reliability_score": 1.0
    }
  ],
  "stockfish_achievers": [...],
  "engine_details": {...}
}
```

## 🚨 Troubleshooting

### Common Issues

**Rating Calculation Problems**
- ✅ **Fixed**: Stockfish ratings now use manual overrides (3645/2650 ELO)
- ✅ **Fixed**: Engine variants properly consolidated under canonical names
- **Solution**: Use rating overrides in `name_consolidation.json` for known engine strengths

**Engine Name Consolidation**
- **Issue**: Multiple variants of same engine showing separately
- **Solution**: Add entries to `name_consolidation.json` or check name_mapper.py output

**Dashboard Display Issues**  
- **Issue**: Ratings showing as 1.0 or incorrect values
- **Solution**: Regenerate analysis with `python unified_tournament_analyzer.py`

**Missing Tournament Data**
- **Issue**: PGN files not being processed
- **Solution**: Ensure PGN files are in `results/[Tournament Name]/` subdirectories

### Interpreting Failures

**Engine Testing Failures:**
- `TIMEOUT uci_handshake`: Engine stuck before producing `uciok`
- `NO_BESTMOVE`: Engine never printed `bestmove` line  
- `ILLEGAL_MOVE`: Move format issues
- `CRASH`: Process exited unexpectedly

## 🗺️ Roadmap

### Completed ✅
- ✅ Cross-tournament unified analysis
- ✅ Manual rating override system  
- ✅ Engine name consolidation
- ✅ Interactive Streamlit dashboard
- ✅ Opponent-strength-adjusted ratings

### Next Steps 🚧
- [ ] Enhanced legality validation via lightweight move generator
- [ ] Option discovery & per-option probing
- [ ] Logging raw protocol transcript per engine
- [ ] Arena specific quirk tests (ponder, analyze mode)
- [ ] Crash dump capture & retry logic
- [ ] Opening book performance analysis
- [ ] Time control adaptation analysis
- [ ] Multi-threaded tournament processing

## 🔒 Safety Note

The tester executes arbitrary `.exe` files you place in the directory. Only run it on binaries you trust.

## 🤝 Contributing

Add new analysis features by:
1. **Engine Testing**: Edit `TEST_STAGES` in `engine_tester.py`
2. **Tournament Analysis**: Extend `unified_tournament_analyzer.py`
3. **Dashboard**: Add visualizations in `dashboard.py`
4. **Name Mapping**: Improve normalization logic in `name_mapper.py`

## 📄 License

Personal project; adapt freely for your own engines.

---

## 🎮 Happy Testing!

**Quick Commands:**
```bash
# Test engines
python engine_tester.py --dir engines

# Analyze tournaments  
python unified_tournament_analyzer.py

# Launch dashboard
streamlit run dashboard.py
```

**Results at a glance:**
- Engine testing reports in `results/`
- Tournament analysis in `results/unified_tournament_analysis.json` 
- Interactive dashboard at `http://localhost:8501`
