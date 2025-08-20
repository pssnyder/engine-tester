# Simplified Chess Engine Analysis Dashboard

A streamlined system for analyzing chess engine tournament performance with consistent metrics and clean visualizations.

## Quick Start

### 1. Run Analytics
```bash
cd analytics_and_dashboard/analyzers
python run_analytics.py
```

### 2. Launch Dashboard
```bash
cd analytics_and_dashboard
python launch_dashboard.py
```

## What's Included

### Core Analyzers
- **`unified_tournament_analyzer.py`** - Main ELO rankings and performance analysis
- **`enhanced_tournament_analyzer.py`** - Supplementary behavioral analysis
- **`name_mapper.py`** - Engine name consolidation system

### Dashboard Features
- **Engine Rankings** - ELO-based rankings with key metrics
- **Family Progress** - Development tracking by engine family (SlowMate, Cece, etc.)
- **Tournament Performance** - Breakdown by individual tournaments
- **Head-to-Head** - Compare engines directly
- **Stockfish Achievers** - Engines that have scored against Stockfish

### Key Improvements
- ✅ **Consistent naming** - All views use the same consolidated engine names
- ✅ **Clean metrics** - Focus on essential performance indicators
- ✅ **Simplified UI** - Minimalistic design, easy navigation
- ✅ **Fast processing** - Streamlined analyzers with error handling
- ✅ **Reliable data** - Proper encoding handling for all PGN files

## File Structure

```
analytics_and_dashboard/
├── analyzers/
│   ├── unified_tournament_analyzer.py    # Main rankings analyzer
│   ├── enhanced_tournament_analyzer.py   # Behavioral analysis
│   ├── name_mapper.py                   # Name consolidation
│   └── run_analytics.py                 # Analytics pipeline
├── dashboard/
│   ├── dashboard.py                     # Simplified dashboard
│   └── data/                           # Analysis results
│       ├── name_consolidation.json     # Engine name mappings
│       └── *.json                      # Analysis outputs
└── launch_dashboard.py                 # Dashboard launcher
```

## Engine Name Consolidation

The system uses a centralized mapping file (`dashboard/data/name_consolidation.json`) that:
- Maps engine variants to canonical names (e.g., `ChessAI_v1.0` → `C0BR4 1.0`)
- Provides rating overrides for reference engines (Stockfish, Random)
- Ensures consistent naming across all analysis views

## Legacy Files

Complex/experimental analyzers and dashboards have been moved to `development/legacy_analyzers/` to keep the main workflow clean and focused.

## Requirements

- Python 3.8+
- Required packages: `streamlit`, `pandas`, `plotly`, `chess`
- Install with: `pip install streamlit pandas plotly python-chess`

## Data Flow

1. **Tournament Results** (`results/`) → 
2. **Analyzers** process PGN files with name consolidation → 
3. **Dashboard Data** (`dashboard/data/`) → 
4. **Web Dashboard** displays clean metrics

The system ensures that engine names are consistently consolidated at every step, eliminating the confusion between family names (SlowMate) and specific versions (SlowMate 1.0).
