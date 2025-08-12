#!/usr/bin/env python3

"""Debug script to investigate engine consolidation issues"""

import json
from unified_tournament_analyzer import UnifiedTournamentAnalyzer, normalize_engine_name

def debug_consolidation():
    """Debug the engine consolidation process"""
    
    # Load the existing analysis
    try:
        with open('results/unified_tournament_analysis.json', 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading analysis: {e}")
        return
    
    print("=== CONSOLIDATION DEBUG REPORT ===\n")
    
    # Check consolidation mapping
    consolidations = data.get('name_consolidation', {}).get('consolidations', {})
    print(f"📋 CONSOLIDATION MAPPING ({len(consolidations)} groups):")
    for canonical, variants in consolidations.items():
        print(f"  {canonical} ← {len(variants)} variants: {', '.join(variants)}")
    print()
    
    # Check what's in unified_rankings
    rankings = data.get('unified_rankings', [])
    print(f"🏆 UNIFIED RANKINGS ({len(rankings)} engines):")
    all_ranking_names = [r['name'] for r in rankings]
    print("Engine families in rankings:")
    families = {}
    for name in all_ranking_names:
        family = name.split('_')[0]
        families[family] = families.get(family, 0) + 1
    
    for family, count in sorted(families.items()):
        print(f"  {family}: {count} engines")
    print()
    
    # Check if consolidated engines are missing
    print("🔍 MISSING CONSOLIDATED ENGINES:")
    for canonical in consolidations.keys():
        if canonical not in all_ranking_names:
            print(f"  ❌ {canonical} - NOT in rankings!")
        else:
            print(f"  ✅ {canonical} - in rankings")
    print()
    
    # Test normalization function directly
    print("🧪 TESTING NORMALIZATION FUNCTION:")
    test_names = [
        "Cece v2.0", "Cece_v2.0", 
        "Copycat_v1.0", "Copycat v1.0", "Copycat_uci",
        "Stockfish 1%", "Stockfish",
        "Random_Opponent", "Random Playing Opponent"
    ]
    
    for name in test_names:
        identity = normalize_engine_name(name)
        print(f"  '{name}' → '{identity.canonical_name}'")
    print()

if __name__ == "__main__":
    debug_consolidation()
