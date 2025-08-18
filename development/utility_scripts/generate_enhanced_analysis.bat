@echo off
echo Generating Enhanced Chess Analytics and Behavioral Analysis...
cd /d "%~dp0"

echo Step 1: Running Unified Tournament Analysis...
python unified_tournament_analyzer.py
echo.

echo Step 2: Running Enhanced Behavioral Pattern Analysis...
python "analysis\behavioral_analyzer.py"
echo.

echo Step 3: Creating Decision Flow Diagram...
python "analysis\generate_decision_diagram.py"
echo.

echo Step 4: Generating Landscape Visualizations...
python "analysis\landscape_visualizer.py"
echo.

echo Step 5: Creating Comprehensive Analysis Report...
python "analysis\comprehensive_reporter.py"
echo.

echo Step 6: Generating Updated Dashboard...
python "analysis\generate_dashboard_final.py"
echo.

echo Enhanced analysis complete! Results saved to the results directory.
echo Opening decision flow diagram...
start "" "results\engine_decision_flow.png"

echo.
echo Press any key to open the enhanced dashboard in your browser...
pause > nul
start "" "http://localhost:8504"
