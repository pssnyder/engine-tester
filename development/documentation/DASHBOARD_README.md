# Chess Engine Analysis Dashboard

A comprehensive Streamlit-based web interface for analyzing chess engine performance, UCI compliance, and tournament results.

## Features

### 🏆 Tournament Overview
- Total games and engines statistics
- Tournament points rankings with interactive charts
- Top performer identification
- Performance metrics by engine family

### 📊 Performance Analysis  
- Win rate vs decisive win rate correlation analysis
- Interactive scatter plots with engine details
- Performance comparison by engine family
- Games played volume analysis

### 📈 Version Progression
- SlowMate version performance trends over time
- Automated regression detection between versions
- Performance cliff identification
- Version-by-version comparison

### 🔧 UCI Compliance Analysis
- Engine test results vs tournament performance correlation
- UCI compliance status overview
- Test duration analysis
- Compliance failure impact on tournament performance

### 🔍 Data Insights & Anomalies
- Manual engine behavior insights and context
- Automated anomaly detection results
- Version regression alerts
- Feature implementation effectiveness analysis
- Data quality issue identification

## Quick Start

1. **Install Dependencies:**
   ```bash
   pip install streamlit plotly pandas
   ```

2. **Launch Dashboard:**
   ```bash
   streamlit run dashboard.py
   ```

3. **Access Interface:**
   Open http://localhost:8501 in your browser

## Data Sources

The dashboard integrates three main data sources:

- **`results/tournament_analysis.json`** - Tournament performance metrics
- **`results/engine_test_report.json`** - UCI compliance test results  
- **`results/results_appendix.json`** - Manual insights and automated anomaly detection

## Navigation

Use the sidebar to:
- Switch between analysis views
- Filter by engine families (SlowMate, Cece, Cecilia)
- Set minimum games threshold for statistical relevance
- View data source information

## Key Insights Surfaced

- **Performance Peaks:** SlowMate v0.2.0_BETA identified as optimal version
- **Breaking Points:** v0.4.x series shows critical regression
- **Feature Mismatches:** Engines named for specific features not excelling in those areas
- **Data Quality Issues:** Random-move engines achieving unrealistic win rates due to broken opponents

## Filters and Interactivity

- **Engine Family Filtering:** Focus analysis on specific engine lines
- **Minimum Games Filter:** Exclude engines with insufficient data
- **Interactive Charts:** Click, hover, and zoom for detailed exploration
- **Cross-Referenced Data:** UCI compliance correlated with tournament performance

## Anomaly Detection

The dashboard highlights:
- Version regressions where newer versions underperform
- Feature implementation failures
- Data inflation from broken opponent engines
- UCI compliance vs performance mismatches

## Future Enhancements

- Head-to-head matchup analysis
- Opening book effectiveness correlation
- Time control performance breakdown
- Opponent-strength-adjusted rankings
- Export functionality for filtered data
