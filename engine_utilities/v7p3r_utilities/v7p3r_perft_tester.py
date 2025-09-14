#!/usr/bin/env python3
"""
V7P3R Comprehensive Perft Testing Tool
========================================

This tool performs comprehensive perft (performance test) validation on V7P3R chess engine.
Perft tests verify move generation correctness by counting all possible positions at various depths.

Usage:
    python v7p3r_perft_tester.py [--engine ENGINE_PATH] [--depth MAX_DEPTH] [--output OUTPUT_FILE]

Features:
- Tests multiple standard perft positions from start position and tricky positions
- Validates move generation accuracy against known perft results
- Measures performance at different depths
- Generates detailed reports for version tracking
- Supports timeout handling for long-running tests
"""

import subprocess
import time
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
import threading
import queue

class V7P3RPerftTester:
    """Comprehensive perft testing for V7P3R chess engine."""
    
    def __init__(self, engine_path, timeout=300):
        """Initialize with engine path and timeout settings."""
        self.engine_path = Path(engine_path)
        self.timeout = timeout
        self.results = {}
        
        # Standard perft test positions with known results
        self.test_positions = {
            "startpos": {
                "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "name": "Starting Position",
                "known_results": {
                    1: 20,
                    2: 400,
                    3: 8902,
                    4: 197281,
                    5: 4865609,
                    6: 119060324,
                    7: 3195901860
                }
            },
            "kiwipete": {
                "fen": "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
                "name": "Kiwipete Position",
                "known_results": {
                    1: 48,
                    2: 2039,
                    3: 97862,
                    4: 4085603,
                    5: 193690690
                }
            },
            "position3": {
                "fen": "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
                "name": "Position 3",
                "known_results": {
                    1: 14,
                    2: 191,
                    3: 2812,
                    4: 43238,
                    5: 674624,
                    6: 11030083,
                    7: 178633661
                }
            },
            "position4": {
                "fen": "r3k2r/8/3Q4/8/8/5q2/8/R3K2R b KQkq - 0 1",
                "name": "Position 4",
                "known_results": {
                    1: 6,
                    2: 35,
                    3: 495,
                    4: 8349,
                    5: 166741,
                    6: 3404411
                }
            },
            "position5": {
                "fen": "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
                "name": "Position 5",
                "known_results": {
                    1: 44,
                    2: 1486,
                    3: 62379,
                    4: 2103487,
                    5: 89941194
                }
            },
            "position6": {
                "fen": "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
                "name": "Position 6",
                "known_results": {
                    1: 46,
                    2: 2079,
                    3: 89890,
                    4: 3894594,
                    5: 164075551
                }
            }
        }
    
    def communicate_with_engine(self, commands, timeout=None):
        """Send commands to engine and get responses with timeout."""
        if timeout is None:
            timeout = self.timeout
            
        try:
            process = subprocess.Popen(
                [str(self.engine_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            # Use a queue to collect output with timeout
            output_queue = queue.Queue()
            
            def read_output():
                try:
                    while True:
                        line = process.stdout.readline()
                        if not line:
                            break
                        output_queue.put(line.strip())
                except:
                    pass
            
            # Start reading thread
            reader_thread = threading.Thread(target=read_output)
            reader_thread.daemon = True
            reader_thread.start()
            
            # Send commands
            output_lines = []
            for command in commands:
                print(f"→ {command}")
                process.stdin.write(command + "\n")
                process.stdin.flush()
                time.sleep(0.1)  # Small delay for processing
            
            # Collect responses with timeout
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    line = output_queue.get(timeout=1)
                    output_lines.append(line)
                    print(f"← {line}")
                    
                    # Check for completion indicators
                    if any(keyword in line.lower() for keyword in ['nodes searched', 'perft', 'ready']):
                        # Wait a bit more for any remaining output
                        time.sleep(0.5)
                        try:
                            while True:
                                line = output_queue.get(timeout=0.5)
                                output_lines.append(line)
                                print(f"← {line}")
                        except:
                            break
                        break
                        
                except queue.Empty:
                    continue
            
            # Cleanup
            try:
                process.stdin.write("quit\n")
                process.stdin.flush()
            except:
                pass
                
            process.terminate()
            process.wait(timeout=5)
            
            return output_lines
            
        except Exception as e:
            print(f"❌ Error communicating with engine: {e}")
            return []
    
    def extract_perft_result(self, output_lines, depth):
        """Extract perft node count from engine output."""
        for line in output_lines:
            line_lower = line.lower()
            if 'nodes searched' in line_lower or 'perft' in line_lower:
                # Look for numbers in the line
                import re
                numbers = re.findall(r'\d+', line)
                if numbers:
                    # Usually the last/largest number is the node count
                    return int(numbers[-1])
        
        # Fallback: look for any large numbers that might be node counts
        for line in output_lines:
            import re
            numbers = re.findall(r'\b\d{3,}\b', line)  # Look for numbers with at least 3 digits
            if numbers:
                return int(numbers[-1])
        
        return None
    
    def test_position(self, position_key, max_depth=5):
        """Test a specific position up to max_depth."""
        position = self.test_positions[position_key]
        print(f"\n🧪 Testing {position['name']}")
        print(f"   FEN: {position['fen']}")
        
        results = {
            'name': position['name'],
            'fen': position['fen'],
            'depths': {},
            'errors': [],
            'timestamp': datetime.now().isoformat()
        }
        
        for depth in range(1, max_depth + 1):
            if depth in position['known_results']:
                expected = position['known_results'][depth]
                print(f"\n  📊 Depth {depth} (expected: {expected:,})")
                
                start_time = time.time()
                
                # Test using UCI perft command
                commands = [
                    "uci",
                    f"position fen {position['fen']}",
                    f"go perft {depth}",
                    "isready"
                ]
                
                output = self.communicate_with_engine(commands, timeout=max(60, depth * 30))
                elapsed = time.time() - start_time
                
                # Extract result
                actual = self.extract_perft_result(output, depth)
                
                if actual is not None:
                    success = actual == expected
                    nps = int(actual / elapsed) if elapsed > 0 else 0
                    
                    print(f"     Result: {actual:,} nodes")
                    print(f"     Time: {elapsed:.2f}s")
                    print(f"     NPS: {nps:,}")
                    print(f"     Status: {'✅ PASS' if success else '❌ FAIL'}")
                    
                    results['depths'][depth] = {
                        'expected': expected,
                        'actual': actual,
                        'success': success,
                        'time': elapsed,
                        'nps': nps,
                        'output': output
                    }
                    
                    if not success:
                        error_msg = f"Depth {depth}: Expected {expected}, got {actual}"
                        results['errors'].append(error_msg)
                        print(f"     ⚠️  {error_msg}")
                
                else:
                    print(f"     ❌ No result found in output")
                    results['depths'][depth] = {
                        'expected': expected,
                        'actual': None,
                        'success': False,
                        'time': elapsed,
                        'nps': 0,
                        'output': output,
                        'error': 'No result extracted'
                    }
                    results['errors'].append(f"Depth {depth}: No result extracted")
            
            else:
                print(f"  ⚪ Depth {depth} (no known result)")
                
        return results
    
    def run_comprehensive_test(self, max_depth=5, positions=None):
        """Run comprehensive perft test suite."""
        print(f"🚀 V7P3R Comprehensive Perft Test")
        print(f"Engine: {self.engine_path}")
        print(f"Max Depth: {max_depth}")
        print(f"Timeout: {self.timeout}s")
        print("=" * 50)
        
        # Test engine connectivity first
        print("🔗 Testing engine connectivity...")
        output = self.communicate_with_engine(["uci", "isready"], timeout=10)
        if not output or not any("readyok" in line.lower() or "uciok" in line.lower() for line in output):
            print("❌ Engine not responding properly to UCI commands")
            return None
        
        print("✅ Engine responding to UCI commands")
        
        # Select positions to test
        if positions is None:
            positions = list(self.test_positions.keys())
        
        test_results = {
            'engine_path': str(self.engine_path),
            'engine_version': self.engine_path.stem,
            'test_timestamp': datetime.now().isoformat(),
            'max_depth': max_depth,
            'timeout': self.timeout,
            'positions': {},
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'error_positions': [],
                'performance_summary': {}
            }
        }
        
        # Test each position
        for pos_key in positions:
            if pos_key in self.test_positions:
                results = self.test_position(pos_key, max_depth)
                test_results['positions'][pos_key] = results
                
                # Update summary
                for depth, result in results['depths'].items():
                    test_results['summary']['total_tests'] += 1
                    if result['success']:
                        test_results['summary']['passed_tests'] += 1
                    else:
                        test_results['summary']['failed_tests'] += 1
                
                if results['errors']:
                    test_results['summary']['error_positions'].append(pos_key)
        
        # Calculate performance summary
        all_nps = []
        for pos_results in test_results['positions'].values():
            for depth_result in pos_results['depths'].values():
                if depth_result['nps'] > 0:
                    all_nps.append(depth_result['nps'])
        
        if all_nps:
            test_results['summary']['performance_summary'] = {
                'avg_nps': int(sum(all_nps) / len(all_nps)),
                'max_nps': max(all_nps),
                'min_nps': min(all_nps)
            }
        
        return test_results
    
    def generate_report(self, results, output_file=None):
        """Generate detailed test report."""
        if not results:
            print("❌ No results to report")
            return
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_file is None:
            engine_name = results['engine_version']
            output_file = f"v7p3r_perft_results_{engine_name}_{timestamp}.json"
        
        # Save JSON results
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Generate summary report
        summary_file = output_path.with_suffix('.md')
        
        summary = results['summary']
        
        report_content = f"""# V7P3R Perft Test Report

## Test Summary
- **Engine**: {results['engine_version']}
- **Test Date**: {results['test_timestamp']}
- **Max Depth**: {results['max_depth']}
- **Total Tests**: {summary['total_tests']}
- **Passed**: {summary['passed_tests']} ✅
- **Failed**: {summary['failed_tests']} ❌
- **Success Rate**: {(summary['passed_tests'] / summary['total_tests'] * 100):.1f}%

"""
        
        if 'performance_summary' in summary:
            perf = summary['performance_summary']
            report_content += f"""## Performance Summary
- **Average NPS**: {perf['avg_nps']:,}
- **Max NPS**: {perf['max_nps']:,}
- **Min NPS**: {perf['min_nps']:,}

"""

        report_content += "## Position Results\n\n"
        
        for pos_key, pos_results in results['positions'].items():
            report_content += f"### {pos_results['name']}\n"
            report_content += f"**FEN**: `{pos_results['fen']}`\n\n"
            
            if pos_results['depths']:
                report_content += "| Depth | Expected | Actual | Status | Time (s) | NPS |\n"
                report_content += "|-------|----------|--------|--------|----------|-----|\n"
                
                for depth, result in pos_results['depths'].items():
                    status_icon = "✅" if result['success'] else "❌"
                    expected = f"{result['expected']:,}" if result['expected'] else "N/A"
                    actual = f"{result['actual']:,}" if result['actual'] else "N/A"
                    nps = f"{result['nps']:,}" if result['nps'] > 0 else "N/A"
                    
                    report_content += f"| {depth} | {expected} | {actual} | {status_icon} | {result['time']:.2f} | {nps} |\n"
            
            if pos_results['errors']:
                report_content += "\n**Errors**:\n"
                for error in pos_results['errors']:
                    report_content += f"- {error}\n"
            
            report_content += "\n"
        
        if summary['error_positions']:
            report_content += "## Failed Positions\n"
            for pos in summary['error_positions']:
                report_content += f"- {pos}\n"
            report_content += "\n"
        
        report_content += """## Notes
- Perft tests validate move generation correctness
- Any failures indicate potential bugs in move generation
- Performance (NPS) can vary based on system load
- This report can be used to track performance across versions
"""
        
        with open(summary_file, 'w') as f:
            f.write(report_content)
        
        print(f"\n📊 Test Results Summary:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed_tests']} ✅")
        print(f"   Failed: {summary['failed_tests']} ❌")
        print(f"   Success Rate: {(summary['passed_tests'] / summary['total_tests'] * 100):.1f}%")
        
        if 'performance_summary' in summary:
            perf = summary['performance_summary']
            print(f"   Average NPS: {perf['avg_nps']:,}")
        
        print(f"\n📁 Reports saved:")
        print(f"   JSON: {output_path}")
        print(f"   Markdown: {summary_file}")
        
        return output_path, summary_file

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="V7P3R Comprehensive Perft Testing Tool")
    parser.add_argument("--engine", default="engines/V7P3R/V7P3R_v10.2.exe", 
                       help="Path to V7P3R engine executable")
    parser.add_argument("--depth", type=int, default=5, 
                       help="Maximum depth to test (default: 5)")
    parser.add_argument("--timeout", type=int, default=300,
                       help="Timeout per test in seconds (default: 300)")
    parser.add_argument("--output", help="Output file path (auto-generated if not specified)")
    parser.add_argument("--positions", nargs="+", 
                       choices=["startpos", "kiwipete", "position3", "position4", "position5", "position6"],
                       help="Specific positions to test (default: all)")
    
    args = parser.parse_args()
    
    # Validate engine path
    engine_path = Path(args.engine)
    if not engine_path.exists():
        print(f"❌ Engine not found: {engine_path}")
        print("Available V7P3R engines:")
        v7p3r_dir = Path("engines/V7P3R")
        if v7p3r_dir.exists():
            for exe in v7p3r_dir.glob("*.exe"):
                print(f"   {exe}")
        sys.exit(1)
    
    # Create tester
    tester = V7P3RPerftTester(engine_path, timeout=args.timeout)
    
    # Run tests
    print(f"🎯 Starting comprehensive perft test for {engine_path.name}")
    results = tester.run_comprehensive_test(max_depth=args.depth, positions=args.positions)
    
    if results:
        # Generate reports
        tester.generate_report(results, args.output)
    else:
        print("❌ Test failed - no results generated")
        sys.exit(1)

if __name__ == "__main__":
    main()
