#!/usr/bin/env python3
"""
V7P3R Analysis Runner
Convenient script to run both historical game analysis and engine performance analysis
for V7P3R v11 development baseline establishment.

Author: Pat Snyder
Created: September 7, 2025
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


def run_historical_analysis(args):
    """Run the historical game analyzer"""
    print("🔍 Starting Historical Game Analysis...")
    print("="*50)
    
    # Default paths
    pgn_dir = args.pgn_dir or r"s:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-metrics\game_records"
    stockfish_path = args.stockfish_path or r"s:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\downloaded_engines\stockfish\stockfish.exe"
    output_dir = args.output_dir or "analysis_output"
    
    # Construct command
    cmd = [
        sys.executable,
        "historical_game_analyzer.py",
        "--pgn-dir", pgn_dir,
        "--stockfish-path", stockfish_path,
        "--output-dir", output_dir,
        "--depth", str(args.depth),
        "--min-eval-improvement", str(args.min_eval_improvement),
        "--max-rank", str(args.max_rank),
        "--min-frequency", str(args.min_frequency)
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print(f"PGN Directory: {pgn_dir}")
    print(f"Stockfish Path: {stockfish_path}")
    print(f"Output Directory: {output_dir}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Historical analysis completed successfully!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Historical analysis failed!")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"❌ Error running historical analysis: {e}")
        return False


def run_performance_analysis(args):
    """Run the engine performance analyzer"""
    print("⚡ Starting Engine Performance Analysis...")
    print("="*50)
    
    # Default paths
    engine_dir = args.engine_dir or r"s:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\V7P3R"
    output_dir = args.output_dir or "analysis_output"
    
    # Construct command
    cmd = [
        sys.executable,
        "engine_performance_analyzer.py",
        "--engine-dir", engine_dir,
        "--output-dir", output_dir,
        "--timeout", str(args.timeout)
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print(f"Engine Directory: {engine_dir}")
    print(f"Output Directory: {output_dir}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Performance analysis completed successfully!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Performance analysis failed!")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"❌ Error running performance analysis: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='V7P3R Analysis Runner for v11 Development')
    parser.add_argument('--mode', choices=['historical', 'performance', 'both'], default='both',
                       help='Analysis mode to run')
    
    # Common arguments
    parser.add_argument('--output-dir', default='analysis_output',
                       help='Output directory for all results')
    
    # Historical analysis arguments
    parser.add_argument('--pgn-dir', 
                       help='Directory containing PGN files (default: engine-metrics/game_records)')
    parser.add_argument('--stockfish-path',
                       help='Path to Stockfish executable (default: auto-detect)')
    parser.add_argument('--depth', type=int, default=15,
                       help='Stockfish analysis depth (default: 15)')
    parser.add_argument('--min-eval-improvement', type=float, default=0.1,
                       help='Minimum eval improvement threshold (default: 0.1)')
    parser.add_argument('--max-rank', type=int, default=3,
                       help='Maximum Stockfish rank for good moves (default: 3)')
    parser.add_argument('--min-frequency', type=int, default=2,
                       help='Minimum frequency for nudge entries (default: 2)')
    
    # Performance analysis arguments
    parser.add_argument('--engine-dir',
                       help='Directory containing V7P3R engines (default: engine-tester/engines/V7P3R)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Timeout for engine tests (default: 30)')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("🚀 V7P3R v11 Development Analysis Suite")
    print("="*50)
    print(f"Mode: {args.mode}")
    print(f"Output Directory: {args.output_dir}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = True
    
    if args.mode in ['historical', 'both']:
        success &= run_historical_analysis(args)
        print()
    
    if args.mode in ['performance', 'both']:
        success &= run_performance_analysis(args)
        print()
    
    if success:
        print("🎉 All analyses completed successfully!")
        print(f"📁 Results saved to: {args.output_dir}")
        print()
        print("📋 Next Steps for V7P3R v11 Development:")
        print("1. Review historical analysis results for nudge system patterns")
        print("2. Examine performance baselines for improvement targets") 
        print("3. Begin Phase 1 implementation (Core Performance & Search Optimization)")
        print("4. Use baseline metrics to measure v11 enhancements")
    else:
        print("❌ Some analyses failed. Check the logs for details.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
