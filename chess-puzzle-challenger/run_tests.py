"""
Test runner script for Puzzle Challenger.
Runs all tests or specific test modules.
"""

import os
import sys
import argparse
import unittest
import pytest

def run_pytest(args):
    """Run tests using pytest."""
    pytest_args = []
    
    if args.verbose:
        pytest_args.append('-v')
    
    if args.test_file:
        pytest_args.append(args.test_file)
    else:
        pytest_args.append('tests/')
    
    return pytest.main(pytest_args)

def run_stockfish_test(args):
    """Run comprehensive stockfish tests."""
    from tests.test_stockfish import run_comprehensive_test
    
    stockfish_path = args.stockfish or "src/stockfish.exe"
    db_path = args.db or "puzzles.db"
    output_dir = args.output or "reports"
    sample_size = args.sample_size or 10
    
    run_comprehensive_test(
        stockfish_path,
        db_path,
        output_dir,
        sample_size,
        args.themes
    )
    return 0

def main():
    parser = argparse.ArgumentParser(description="Run tests for Puzzle Challenger")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Unit tests command
    unit_parser = subparsers.add_parser("unit", help="Run unit tests")
    unit_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    unit_parser.add_argument("test_file", nargs="?", help="Specific test file to run")
    
    # Stockfish tests command
    stockfish_parser = subparsers.add_parser("stockfish", help="Run Stockfish comprehensive tests")
    stockfish_parser.add_argument("--stockfish", type=str, help="Path to Stockfish executable")
    stockfish_parser.add_argument("--db", type=str, help="Path to puzzle database")
    stockfish_parser.add_argument("--output", type=str, help="Directory to save reports")
    stockfish_parser.add_argument("--sample-size", type=int, help="Number of puzzles to sample")
    stockfish_parser.add_argument("--themes", type=str, nargs="+", help="Specific themes to test")
    
    args = parser.parse_args()
    
    if args.command == "unit":
        return run_pytest(args)
    elif args.command == "stockfish":
        return run_stockfish_test(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
