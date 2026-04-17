@echo off
REM V18.4 Puzzle Analysis Test
REM Tests v18.4 against tactical puzzles to validate improvements

echo ============================================================
echo V7P3R v18.4 Tactical Puzzle Validation
echo ============================================================
echo.

cd /d "%~dp0"

REM Test configuration
set ENGINE_PATH=e:\Programming Stuff\Chess Engines\V7P3R Chess Engine\v7p3r-chess-engine\development\V7P3R_v18.4_20260415\V7P3R_v18.4.bat
set NUM_PUZZLES=50
set TIME_PER_PUZZLE=10
set MIN_RATING=1200
set MAX_RATING=1800
set THEMES=mate mateIn1 mateIn2 pin fork skewer discoveredAttack

echo Engine: %ENGINE_PATH%
echo Puzzles: %NUM_PUZZLES%
echo Time per position: %TIME_PER_PUZZLE%s
echo Rating range: %MIN_RATING%-%MAX_RATING%
echo Themes: %THEMES%
echo.
echo Starting analysis...
echo.

py -3 engine_utilities/universal_puzzle_analyzer.py ^
    --engine "%ENGINE_PATH%" ^
    --puzzles %NUM_PUZZLES% ^
    --time %TIME_PER_PUZZLE% ^
    --min-rating %MIN_RATING% ^
    --max-rating %MAX_RATING% ^
    --themes %THEMES%

echo.
echo ============================================================
echo Test complete! Check results in current directory.
echo ============================================================
pause
