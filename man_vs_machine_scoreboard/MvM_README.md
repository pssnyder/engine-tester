# Man vs Machine Scoreboard
This competitive scoreboard tracks the performance of the V7P3R human designed, analyzed, and developed chess engine vs the 100% Copilot managed chess engine. The goal is to evaluate the strengths and weaknesses of each approach in a controlled environment while gamifying the results and the project.

## Competitors

1. **V7P3R**: My human-designed, analyzed, and developed chess engine that incorporates advanced strategies and techniques based on my own play knowledge.
2. **SlowMate**: A chess engine that is fully managed and developed by Copilot, reviewing its own game results and suggesting and coding its own enhancements.

## Available Metrics

1. **Win Rate**: The percentage of games won by each engine.
2. **Decisive Win Rate**: The percentage of games won by each engine by checkmate.
3. **Missed Wins**: The % of times the engine had a forced mate or significant material advantage (>10) and still lost or drew a game.
4. **Average Move Time**: The average time taken by each engine to make a move.
5. **Search Depth**: The average depth of search (in plies) achieved by each engine.
6. **Puzzle Solving**: The ability of each engine to find the "best" move in a given position.
    a. **Opening Repertoire**: The variety and effectiveness of opening moves played by each engine.
    b. **Endgame Performance**: The ability of each engine to convert winning positions into victories in the endgame.
    c. **Tactical Ability**: The proficiency of each engine in finding and executing tactical combinations.

### Metrics Considerations and Implementation Notes
- Streamlit dashboard
- Total win rate can account for a win of any kind and should be weighted to consider total number of games played.
- Each engine version should be tracked separately, only using the most recent V7P3R version vs the most recent SlowMate version games for key metrics.
- Additional deep dive tabs can be provided for version specific metrics comparison between versions. Overall the default is most recent version.
- The engine-testers various tools, utilties, and analyzers can be used for key outputs and to compile data for these metrics.
- Similar to the analytics_and_dashboard file structure, all necessary data and visuals should be available in the man_vs_machine_scoreboard directory.

## Dashboard Structure

The Man vs Machine Scoreboard includes:

### 📁 Directory Structure
```
man_vs_machine_scoreboard/
├── MvM_README.md                    # This file
├── launch_mvm_dashboard.py          # Dashboard launcher
├── requirements.txt                 # Python dependencies
├── analyzers/
│   └── mvm_analyzer.py             # Man vs Machine data analyzer
└── dashboard/
    ├── mvm_dashboard.py            # Streamlit dashboard
    └── data/
        └── mvm_analysis.json       # Generated analysis data
```

### 🚀 Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r man_vs_machine_scoreboard/requirements.txt
   ```

2. **Launch Dashboard**:
   ```bash
   python man_vs_machine_scoreboard/launch_mvm_dashboard.py
   ```

   The launcher will automatically:
   - Check for existing analysis data
   - Run the analyzer if data is missing
   - Start the Streamlit dashboard on port 8502

### 📊 Dashboard Features

#### ⚔️ Main Scoreboard
- Head-to-head win/loss/draw statistics
- Visual pie charts and bar graphs
- Decisive win tracking (checkmates)
- Real-time score percentages

#### 📈 Overall Performance
- Complete performance statistics for both engines
- Win rates, score percentages, and game counts
- Comparative analysis beyond head-to-head

#### 🔄 Version Tracking
- Performance tracking by engine version
- Development progress visualization
- Latest version comparisons
- Historical performance trends

#### 🏟️ Tournament Breakdown
- Tournament-by-tournament analysis
- Detailed game listings
- Per-tournament head-to-head results
- Game termination analysis

#### 🎯 Advanced Metrics (Coming Soon)
- Opening repertoire analysis
- Endgame performance metrics
- Tactical ability assessment
- Missed opportunities tracking

### 🔧 Technical Implementation

#### Data Analysis (`mvm_analyzer.py`)
- Processes PGN files from the results directory
- Identifies V7P3R and SlowMate games using pattern matching
- Extracts version information from engine names
- Calculates comprehensive statistics and metrics
- Generates JSON output for dashboard consumption

#### Dashboard (`mvm_dashboard.py`)
- Streamlit-based web interface
- Interactive visualizations using Plotly
- Real-time data loading and caching
- Responsive design with multiple view tabs
- Clean, competitive scoreboard aesthetic

#### Engine Detection
The analyzer uses pattern matching to identify engines:
- **V7P3R patterns**: `V7P3R.*`, `v7p3r.*`, `V7P3R_.*`, etc.
- **SlowMate patterns**: `SlowMate.*`, `slowmate.*`, `SlowMate_.*`, etc.
- **Version extraction**: Supports patterns like `v1.0`, `_v2`, `-3.1`, etc.

### 📝 Usage Notes

- The dashboard runs on port 8502 (different from the main analytics dashboard on 8501)
- Analysis data is automatically cached for performance
- The analyzer processes all PGN files in the results directory
- Version tracking helps monitor development progress over time
- Head-to-head focus provides competitive insights beyond overall performance

### 🎯 Future Enhancements

- Advanced opening analysis integration
- Real-time evaluation graphs
- Tactical puzzle solving metrics
- Time management analysis
- Position-type performance breakdown
- Interactive game replay functionality