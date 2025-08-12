#!/usr/bin/env python3

"""Check the actual rankings to see where non-SlowMate engines rank"""

import json

def check_rankings():
    """Check the full rankings to see where other engines rank"""
    
    # Load the existing analysis
    try:
        with open('results/unified_tournament_analysis.json', 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading analysis: {e}")
        return
    
    rankings = data.get('unified_rankings', [])
    
    print("=== FULL RANKINGS ANALYSIS ===\n")
    print(f"Total engines in rankings: {len(rankings)}")
    print()
    
    print("📊 TOP 20 ENGINES BY ELO:")
    for i, engine in enumerate(rankings[:20]):
        family = engine['name'].split('_')[0]
        star = "⭐" if family != "SlowMate" else ""
        print(f"  {i+1:2d}. {engine['name']:<35} | {engine['estimated_rating']:4.0f} ELO | {engine['games']:3d} games {star}")
    print()
    
    print("🔍 NON-SLOWMATE ENGINES IN FULL RANKINGS:")
    non_slowmate = []
    for i, engine in enumerate(rankings):
        if not engine['name'].startswith('SlowMate'):
            non_slowmate.append((i+1, engine))
    
    print(f"Found {len(non_slowmate)} non-SlowMate engines:")
    for rank, engine in non_slowmate:
        print(f"  {rank:2d}. {engine['name']:<35} | {engine['estimated_rating']:4.0f} ELO | {engine['games']:3d} games")
    print()
    
    print("📈 FAMILY BREAKDOWN:")
    families = {}
    for engine in rankings:
        family = engine['name'].split('_')[0]
        if family not in families:
            families[family] = []
        families[family].append(engine)
    
    for family, engines in sorted(families.items()):
        avg_rating = sum(e['estimated_rating'] for e in engines) / len(engines)
        total_games = sum(e['games'] for e in engines)
        print(f"  {family:<15} | {len(engines):2d} engines | Avg: {avg_rating:4.0f} ELO | Total: {total_games:4d} games")

if __name__ == "__main__":
    check_rankings()
