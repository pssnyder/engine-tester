# Chess Engine Dashboard

A Streamlit-based dashboard for analyzing chess engine performance and UCI compliance.

## Files

### Core Dashboard
- `dashboard.py` - Main Streamlit application
- `requirements.txt` - Python dependencies

### Data Files
- `results/engine_test_report.json` - UCI compliance test results
- `results/tournament_analysis.json` - Tournament performance metrics
- `results/results_appendix.json` - Anomaly detection and insights

### Documentation
- `DASHBOARD_README.md` - Detailed dashboard usage guide

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the dashboard:
```bash
streamlit run dashboard.py
```

3. Open your browser to http://localhost:8501

## Features

- **Tournament Performance Analysis**: Win rates, points, decisive games
- **UCI Compliance Monitoring**: Engine protocol compliance testing
- **Performance Correlations**: Compare UCI compliance with tournament results
- **Interactive Visualizations**: Charts and metrics with Plotly

## Data Sources

The dashboard reads pre-generated analysis files from the `results/` directory. These contain:
- Engine test results from UCI protocol validation
- Tournament statistics from PGN file analysis
- Automated anomaly detection results

## Production Deployment

This branch contains only the essential files needed to run the dashboard in production environments.
