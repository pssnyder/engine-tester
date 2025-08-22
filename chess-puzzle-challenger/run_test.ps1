# PowerShell script to run a comprehensive test with Stockfish

# Define parameters
$stockfishPath = "src\stockfish.exe"
$dbPath = "puzzles.db"
$outputDir = "reports"
$sampleSize = 100

# Check if the database exists
if (-not (Test-Path $dbPath)) {
    Write-Host "Database not found. Importing puzzles from lichess_db_puzzle.csv..."
    python -m src.main import-puzzles --file lichess_db_puzzle.csv --db $dbPath
}

# Make sure the output directory exists
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

# Run the comprehensive test
Write-Host "Running comprehensive test with Stockfish..."
python test_stockfish.py --stockfish $stockfishPath --db $dbPath --output $outputDir --sample-size $sampleSize

# Open the HTML report if it exists
$reportPath = Join-Path $outputDir "performance_report.html"
if (Test-Path $reportPath) {
    Write-Host "Opening performance report..."
    Start-Process $reportPath
}
