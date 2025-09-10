# V7P3R v11 Analysis Utilities

This directory contains powerful analysis tools to support V7P3R v11 development by establishing baselines and extracting strategic patterns from historical games.

## 🔧 Tools Overview

### 1. Historical Game Analyzer (`historical_game_analyzer.py`)
Analyzes V7P3R's historical games against Stockfish to identify successful positions and moves for the nudge system.

**Purpose**: Learn from past games to create a database of favorable positions and preferred moves.

**Process**:
1. Parse PGN files containing V7P3R games
2. For each V7P3R move, analyze with Stockfish  
3. Identify moves that are in Stockfish's top 3 and show positive eval improvement
4. Build database of successful positions and moves
5. Generate nudge system data for V7P3R v11

### 2. Engine Performance Analyzer (`engine_performance_analyzer.py`)
Performs comprehensive performance testing on historical V7P3R engine versions to establish baselines.

**Purpose**: Establish performance baselines for v11 development measurement.

**Tests Include**:
- Perft testing for move generation speed
- Search performance on standard positions
- Tactical puzzle solving accuracy
- Time management evaluation
- UCI compliance and stability

### 3. Analysis Runner (`run_v11_analysis.py`)
Convenient script to run both analyzers with sensible defaults for the V7P3R development environment.

## 🚀 Quick Start

### Run Both Analyses (Recommended)
```bash
cd src/v7p3r_utilities
python run_v11_analysis.py --mode both
```

### Run Individual Analyses
```bash
# Historical game analysis only
python run_v11_analysis.py --mode historical

# Performance analysis only  
python run_v11_analysis.py --mode performance
```

## 📋 Prerequisites

### Required Software
- **Python 3.8+** with chess library (`pip install python-chess`)
- **Stockfish** executable (for historical analysis)
- **V7P3R engines** in executable format

### Default Paths (automatically detected)
- **PGN Files**: `engine-metrics/game_records/` 
- **Stockfish**: `engine-tester/downloaded_engines/stockfish/stockfish.exe`
- **V7P3R Engines**: `engine-tester/engines/V7P3R/`

## 📊 Output Files

### Historical Game Analysis
- `v7p3r_position_database_YYYYMMDD_HHMMSS.json` - Complete position analysis database
- `v7p3r_nudge_entries_YYYYMMDD_HHMMSS.json` - Nudge system data for v11
- `v7p3r_analysis_summary_YYYYMMDD_HHMMSS.json` - Summary statistics and top entries

### Engine Performance Analysis  
- `v7p3r_performance_analysis_YYYYMMDD_HHMMSS.json` - Complete performance data
- `v7p3r_performance_comparison_YYYYMMDD_HHMMSS.md` - Markdown comparison report
- `v7p3r_baseline_metrics_YYYYMMDD_HHMMSS.json` - Baseline metrics for v11 tracking

## ⚙️ Configuration Options

### Historical Analysis Parameters
```bash
python run_v11_analysis.py \
  --mode historical \
  --depth 15 \                      # Stockfish analysis depth
  --min-eval-improvement 0.1 \      # Minimum eval improvement (pawns)
  --max-rank 3 \                    # Max Stockfish rank for good moves  
  --min-frequency 2                 # Min frequency for nudge entries
```

### Performance Analysis Parameters
```bash
python run_v11_analysis.py \
  --mode performance \
  --timeout 30                      # Test timeout in seconds
```

## 📈 Using Results for V7P3R v11

### Historical Analysis Results
The nudge system data can be directly integrated into V7P3R v11:

```python
# Example: Loading nudge entries for Phase 2 implementation
import json

with open('v7p3r_nudge_entries_20250907_143022.json', 'r') as f:
    nudge_data = json.load(f)

# Each entry contains:
# - position_fen: FEN of the position
# - position_hash: Unique position identifier  
# - preferred_move: Best move for this position
# - confidence_score: How confident we are (higher = better)
# - frequency: How often this pattern occurred
# - avg_eval_improvement: Average evaluation improvement
```

### Performance Baseline Results
Use baseline metrics to track v11 improvements:

```python
# Example: Tracking improvement against baseline
with open('v7p3r_baseline_metrics_20250907_143022.json', 'r') as f:
    baseline = json.load(f)

current_performance = test_current_engine()
improvement = {
    'overall_score': current_performance['score'] - baseline['performance_targets']['overall_score'],
    'tactical_accuracy': current_performance['tactical'] - baseline['performance_targets']['tactical_accuracy'],
    'search_depth': current_performance['depth'] - baseline['search_metrics']['avg_depth']
}
```

## 🎯 V7P3R v11 Integration Points

### Phase 1: Core Performance & Search Optimization
- **Baseline Metrics**: Use performance analysis results to set improvement targets
- **Perft Benchmarks**: Track move generation speed improvements
- **Search Depth Goals**: Current baseline vs 10+ ply target

### Phase 2: Positional Awareness & Strategic Nudging  
- **Nudge Database**: Direct integration of historical analysis results
- **Position Matching**: Use position hashes for instant move recognition
- **Confidence Scoring**: Prioritize high-confidence nudge entries

### Phase 3: Evaluation Enhancement
- **Pattern Recognition**: Historical patterns inform defensive analysis
- **Success Metrics**: Track improvement in tactical accuracy

### Phase 4: Endgame & Polish
- **Endgame Patterns**: Extract endgame-specific nudge entries
- **Draw Prevention**: Analyze historical draw patterns to avoid

## 🔍 Example Analysis Workflow

```bash
# 1. Run complete analysis
python run_v11_analysis.py --mode both --output-dir v11_baseline

# 2. Review results
ls v11_baseline/
# v7p3r_performance_comparison_20250907_143022.md
# v7p3r_nudge_entries_20250907_143022.json  
# v7p3r_baseline_metrics_20250907_143022.json

# 3. Extract key metrics for v11 planning
python -c "
import json
with open('v11_baseline/v7p3r_baseline_metrics_20250907_143022.json') as f:
    data = json.load(f)
print('Current Performance Targets:')
print(f'Overall Score: {data[\"performance_targets\"][\"overall_score\"]:.1f}/100')
print(f'Tactical Accuracy: {data[\"performance_targets\"][\"tactical_accuracy\"]:.1f}%')
print(f'Target Search Depth: {data[\"improvement_goals\"][\"target_search_depth\"]} plies')
"

# 4. Begin Phase 1 implementation with baseline established
```

## 🏆 Success Metrics

After running the analysis, you'll have:

✅ **Complete performance baseline** for all V7P3R versions  
✅ **Strategic position database** from successful historical games  
✅ **Nudge system data** ready for Phase 2 integration  
✅ **Improvement targets** for v11 development phases  
✅ **Measurement framework** to track v11 enhancements  

## 🛠️ Troubleshooting

### Common Issues

**Stockfish not found**:
```bash
python run_v11_analysis.py --stockfish-path "path/to/stockfish.exe"
```

**PGN files not found**:
```bash  
python run_v11_analysis.py --pgn-dir "path/to/pgn/directory"
```

**Engine timeout issues**:
```bash
python run_v11_analysis.py --timeout 60  # Increase timeout
```

**Permission errors**:
- Ensure executables have proper permissions
- Run from appropriate directory with write access

### Validation

Test the tools on a small dataset first:
```bash
# Create test directory with 1-2 PGN files
mkdir test_analysis
python run_v11_analysis.py --pgn-dir test_pgns --output-dir test_analysis
```

---

**Ready to establish your V7P3R v11 development baseline!** 🚀
