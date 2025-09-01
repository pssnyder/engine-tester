#!/usr/bin/env python3
"""
Quick V7P3R v9.5 Decisiveness Test
Tests if engine consistently returns moves within time limits
"""

import subprocess
import time
import sys

def quick_decisiveness_test():
    """Quick test to verify V7P3R returns moves consistently"""
    
    engine_path = r's:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\v7p3r\V7P3R_v9.5.exe'
    
    # Test positions that previously caused issues
    test_positions = [
        {
            'name': 'Starting Position',
            'fen': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
        },
        {
            'name': 'Middlegame',
            'fen': 'r1bq1rk1/ppp2ppp/2n2n2/3p4/2PP4/3BPN2/PP3PPP/RNBQ1RK1 w - - 0 8'
        },
        {
            'name': 'Complex Position',
            'fen': 'r4rk1/pp1bq1bp/3p1np1/2pPp3/2P1P3/2N2NQP/PP1B1PP1/2R2RK1 w - - 0 15'
        }
    ]
    
    print("QUICK V7P3R v9.5 DECISIVENESS TEST")
    print("=" * 45)
    
    results = []
    time_limit = 10  # 10 second time limit
    
    for i, position in enumerate(test_positions, 1):
        print(f"\nTest {i}/3: {position['name']}")
        
        # Start engine process
        process = subprocess.Popen([engine_path], 
                                 stdin=subprocess.PIPE, 
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        try:
            # UCI handshake with timeout
            process.stdin.write('uci\n')
            process.stdin.flush()
            
            # Wait for uciok with timeout
            uci_ready = False
            start_time = time.time()
            while time.time() - start_time < 5:  # 5 second timeout for UCI
                line = process.stdout.readline()
                if 'uciok' in line:
                    uci_ready = True
                    break
                if not line:
                    break
            
            if not uci_ready:
                print(f"  ✗ FAILED: UCI handshake timeout")
                results.append({'test': position['name'], 'success': False, 'reason': 'UCI_TIMEOUT'})
                continue
            
            # Set position
            process.stdin.write(f'position fen {position["fen"]}\n')
            process.stdin.flush()
            
            # Start search
            start_time = time.time()
            process.stdin.write(f'go movetime {time_limit * 1000}\n')
            process.stdin.flush()
            
            # Wait for bestmove with timeout
            best_move = None
            search_timeout = False
            
            while time.time() - start_time < time_limit + 3:  # +3 second safety
                line = process.stdout.readline()
                if line.startswith('bestmove'):
                    best_move = line.split()[1] if len(line.split()) > 1 else None
                    break
                if not line:
                    break
            
            actual_time = time.time() - start_time
            
            if best_move is None:
                search_timeout = True
            
            # Record result
            success = best_move is not None and not search_timeout
            result = {
                'test': position['name'],
                'success': success,
                'move': best_move,
                'time': actual_time,
                'reason': 'SUCCESS' if success else ('NO_MOVE' if not best_move else 'TIMEOUT')
            }
            results.append(result)
            
            # Print result
            status = "✓ SUCCESS" if success else "✗ FAILED"
            move_str = best_move if best_move else "None"
            print(f"  {status} | Move: {move_str} | Time: {actual_time:.2f}s")
            
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results.append({'test': position['name'], 'success': False, 'reason': f'ERROR: {e}'})
            
        finally:
            # Clean shutdown
            try:
                process.stdin.write('quit\n')
                process.stdin.close()
                process.wait(timeout=2)
            except:
                process.kill()
    
    # Summary
    print("\n" + "=" * 45)
    print("QUICK TEST SUMMARY")
    print("=" * 45)
    
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    
    print(f"Tests passed: {successful}/{total} ({successful/total*100:.1f}%)")
    
    if successful < total:
        print("\nFailures:")
        for result in results:
            if not result['success']:
                print(f"  {result['test']}: {result['reason']}")
    
    # Check if the main issue is resolved
    if successful == total:
        print("\n✓ ALL TESTS PASSED - Engine is returning moves consistently!")
    else:
        print(f"\n⚠ {total - successful} FAILURES - Engine has decisiveness issues")
    
    return results

if __name__ == "__main__":
    quick_decisiveness_test()
