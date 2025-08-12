#!/usr/bin/env python3
"""
Test script to check engine name normalization
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unified_tournament_analyzer import normalize_engine_name

# Test engine names that should be consolidated
test_names = [
    "SlowMate_v1.0_RELEASE",
    "SlowMate v1.0",
    "SlowMate_v1.0",
    "SlowMate_v1.0_Release",
    "SlowMate_v0.2.0_BETA",
    "SlowMate_v0.2.0_Beta",
    "Cece_v1.0",
    "Cece v1.0",
    "Cecilia_v0.1.0_Basic",
    "Stockfish",
    "Random_Opponent",
    "Copycat_v1.0",
    "Copycat v1.0",
    "V7P3RAI_v1.0"
]

print("Engine Name Normalization Test")
print("=" * 50)

consolidation_groups = {}

for name in test_names:
    identity = normalize_engine_name(name)
    canonical = identity.canonical_name
    
    if canonical not in consolidation_groups:
        consolidation_groups[canonical] = []
    consolidation_groups[canonical].append(name)
    
    print(f"{name:<30} → {canonical}")

print("\nConsolidation Groups:")
print("=" * 50)

for canonical, raw_names in consolidation_groups.items():
    if len(raw_names) > 1:
        print(f"\n{canonical}:")
        for raw_name in raw_names:
            print(f"  ← {raw_name}")
