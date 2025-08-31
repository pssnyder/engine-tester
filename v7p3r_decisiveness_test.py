#!/usr/bin/env python3
"""
V7P3R v9.5 Time Management Test
Tests decisiveness in complex positions and time management
"""

import subprocess
import time
import sys

def test_engine_decisiveness():
    """Test V7P3R v9.5 on complex positions with various time limits"""
    
    engine_path = r's:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\v7p3r\V7P3R_v9.5.exe'
    
    # Complex positions that might cause timeout issues
    test_positions = [
        {
            'name': 'Complex Middlegame',
            'fen': 'r1bq1rk1/ppp2ppp/2n2n2/3p4/2PP4/3BPN2/PP3PPP/RNBQ1RK1 w - - 0 8',
            'description': 'Standard middlegame with many options'
        },
        {
            'name': 'Tactical Complexity',
            'fen': 'r4rk1/pp1bq1bp/3p1np1/2pPp3/2P1P3/2N2NQP/PP1B1PP1/2R2RK1 w - - 0 15',
            'description': 'Tactical middlegame position'
        },
        {
            'name': 'Sharp Opening',
            'fen': 'rnbqk2r/pp2ppbp/3p1np1/2pP4/4P3/2N2N2/PPP2PPP/R1BQKB1R w KQkq c6 0 6',
            'description': 'Sharp King\'s Indian Defense position'
        },
        {
            'name': 'Endgame Complexity',
            'fen': '4r1k1/pp1r1pp1/2n4p/2Pp4/1P1Pn3/P1N1P2P/2R2PP1/1R4K1 w - - 0 25',
            'description': 'Complex rook endgame'
        },
        {
            'name': 'Queen Endgame',
            'fen': '4q1k1/5pp1/7p/3Q4/8/6P1/5P1P/6K1 w - - 0 40',
            'description': 'Queen endgame requiring precise calculation'
        }
    ]
    
    time_limits = [5, 10, 15, 20]  # Test different time limits
    
    print("V7P3R v9.5 DECISIVENESS TEST")
    print("=" * 50)
    
    results = []
    
    for position in test_positions:
        print(f"\nTesting: {position['name']}")
        print(f"Description: {position['description']}")
        print(f"FEN: {position['fen']}")
        
        for time_limit in time_limits:
            print(f"\n  Time limit: {time_limit}s")
            
            # Start engine process
            process = subprocess.Popen([engine_path], 
                                     stdin=subprocess.PIPE, 
                                     stdout=subprocess.PIPE,
                                     text=True)
            
            try:
                # UCI handshake
                process.stdin.write('uci\n')
                process.stdin.flush()
                
                # Wait for uciok
                while True:
                    line = process.stdout.readline()
                    if 'uciok' in line:
                        break
                    if not line:  # Process ended unexpectedly
                        break
                
                # Set position
                process.stdin.write(f'position fen {position["fen"]}\n')
                process.stdin.flush()
                
                # Start search with time limit
                start_time = time.time()
                process.stdin.write(f'go movetime {time_limit * 1000}\n')  # Convert to milliseconds
                process.stdin.flush()
                
                # Wait for bestmove
                best_move = None
                timeout_occurred = False
                
                while True:
                    line = process.stdout.readline()
                    elapsed = time.time() - start_time
                    
                    if line.startswith('bestmove'):
                        best_move = line.split()[1] if len(line.split()) > 1 else None
                        break
                    
                    # Safety timeout (time_limit + 5 seconds grace)
                    if elapsed > time_limit + 5:
                        timeout_occurred = True
                        break
                        
                    if not line:  # Process ended
                        break
                
                actual_time = time.time() - start_time
                
                # Record result
                result = {
                    'position': position['name'],
                    'time_limit': time_limit,
                    'actual_time': actual_time,
                    'returned_move': best_move is not None,
                    'move': best_move,
                    'timeout': timeout_occurred,
                    'success': best_move is not None and not timeout_occurred
                }
                results.append(result)
                
                # Print result
                status = "✓ SUCCESS" if result['success'] else "✗ FAILED"
                move_str = best_move if best_move else "None"
                print(f"    Result: {status} | Move: {move_str} | Time: {actual_time:.2f}s")
                
                if timeout_occurred:
                    print(f"    ⚠ TIMEOUT: Engine exceeded {time_limit + 5}s safety limit")
                elif not best_move:
                    print(f"    ⚠ NO MOVE: Engine failed to return a move")
                
            except Exception as e:
                print(f"    ✗ ERROR: {e}")
                
            finally:
                # Clean shutdown
                try:
                    process.stdin.write('quit\n')
                    process.stdin.close()
                    process.wait(timeout=2)
                except:
                    process.kill()
    
    # Summary
    print("\n" + "=" * 50)
    print("DECISIVENESS TEST SUMMARY")
    print("=" * 50)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    failed_tests = total_tests - successful_tests
    
    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests} ({successful_tests/total_tests*100:.1f}%)")
    print(f"Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
    
    # Break down failures
    timeouts = sum(1 for r in results if r['timeout'])
    no_moves = sum(1 for r in results if not r['returned_move'] and not r['timeout'])
    
    if failed_tests > 0:
        print(f"\nFailure breakdown:")
        print(f"  Timeouts: {timeouts}")
        print(f"  No moves returned: {no_moves}")
        
        print(f"\nProblematic positions:")
        for result in results:
            if not result['success']:
                reason = "TIMEOUT" if result['timeout'] else "NO_MOVE"
                print(f"  {result['position']} ({result['time_limit']}s): {reason}")
    
    # Time analysis
    avg_times = {}
    for time_limit in time_limits:
        times = [r['actual_time'] for r in results if r['time_limit'] == time_limit and r['success']]
        if times:
            avg_times[time_limit] = sum(times) / len(times)
    
    print(f"\nAverage response times:")
    for time_limit, avg_time in avg_times.items():
        efficiency = (avg_time / time_limit) * 100
        print(f"  {time_limit}s limit: {avg_time:.2f}s average ({efficiency:.1f}% of allocated time)")
    
    return results

if __name__ == "__main__":
    test_engine_decisiveness()
