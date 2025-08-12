#!/usr/bin/env python3

"""
Updated name normalization system using manual mapping file
"""

import json
import re
from typing import Dict, List, Optional

def load_name_mapping(mapping_file: str = "results/name_consolidation.json") -> tuple[Dict[str, str], Dict[str, float]]:
    """Load the manual name mapping from JSON file, returns (name_mapping, rating_overrides)"""
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Build reverse mapping: raw_name -> canonical_name
        name_mapping = {}
        rating_overrides = {}
        consolidations = data.get('name_consolidation', {}).get('consolidations', {})
        
        for canonical_name, config in consolidations.items():
            # Handle both old array format and new object format
            if isinstance(config, list):
                # Old format: "canonical_name": ["variant1", "variant2"]
                raw_names = config
                rating_override = None
            else:
                # New format: "canonical_name": {"variants": [...], "rating_override": 1234}
                raw_names = config.get('variants', [])
                rating_override = config.get('rating_override')
                
                if rating_override is not None:
                    rating_overrides[canonical_name] = float(rating_override)
            
            for raw_name in raw_names:
                name_mapping[raw_name] = canonical_name
                # Also add case-insensitive variants
                name_mapping[raw_name.lower()] = canonical_name
                name_mapping[raw_name.upper()] = canonical_name
                # Handle space/underscore variants
                name_mapping[raw_name.replace('_', ' ')] = canonical_name
                name_mapping[raw_name.replace(' ', '_')] = canonical_name
        
        print(f"✅ Loaded {len(consolidations)} consolidation groups covering {len(name_mapping)} name variants")
        if rating_overrides:
            print(f"📊 Found {len(rating_overrides)} rating overrides: {', '.join(rating_overrides.keys())}")
        return name_mapping, rating_overrides
        
    except FileNotFoundError:
        print(f"⚠️  Warning: Mapping file {mapping_file} not found. Using fallback normalization.")
        return {}, {}
    except Exception as e:
        print(f"❌ Error loading mapping file: {e}")
        return {}, {}

def normalize_engine_name_with_mapping(raw_name: str, name_mapping: Dict[str, str]) -> str:
    """Normalize engine name using manual mapping with fallback logic"""
    
    # First try exact match (case-sensitive)
    if raw_name in name_mapping:
        return name_mapping[raw_name]
    
    # Try case-insensitive match
    lower_name = raw_name.lower()
    if lower_name in name_mapping:
        return name_mapping[lower_name]
    
    # Try with space/underscore normalization
    space_normalized = raw_name.replace('_', ' ')
    if space_normalized in name_mapping:
        return name_mapping[space_normalized]
    
    underscore_normalized = raw_name.replace(' ', '_')
    if underscore_normalized in name_mapping:
        return name_mapping[underscore_normalized]
    
    # Try partial matching for engines with extra suffixes
    clean_name = clean_engine_name(raw_name)
    if clean_name in name_mapping:
        return name_mapping[clean_name]
    
    # Try to match by removing common suffixes and normalizing
    for suffix in ['_BETA', '_ALPHA', '_RELEASE', '_ENHANCED', '_BASIC', '_ADVANCED', '_FIXED', 
                   '_PURE_RANDOM', '_ENHANCED_INTELLIGENCE', '_OPENING_BOOK', '_TACTICAL_INTELLIGENCE',
                   '_TACTICS', '_OPENING_ENDGAME', '_MIDDLEGAME', '_ENHANCED_SEARCH', '_TIME_MANAGEMENT',
                   '_ENHANCED_ENDGAME', '_VERSION_VS_VERSION_NUCLEAR_FIX', '_DELTA', '_UCI']:
        if raw_name.endswith(suffix):
            base_name = raw_name[:-len(suffix)]
            if base_name in name_mapping:
                return name_mapping[base_name]
            # Try case variations
            if base_name.lower() in name_mapping:
                return name_mapping[base_name.lower()]
    
    # Fallback: return the original name cleaned up
    print(f"⚠️  No mapping found for '{raw_name}', using fallback normalization")
    return fallback_normalize(raw_name)

def clean_engine_name(name: str) -> str:
    """Clean engine name by removing common variations"""
    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name.strip())
    
    # Handle version patterns
    # SlowMate_v1.0_RELEASE -> SlowMate_v1.0
    name = re.sub(r'(_v?\d+\.\d+(?:\.\d+)?)_[A-Z_]+$', r'\1', name)
    
    return name

def fallback_normalize(raw_name: str) -> str:
    """Fallback normalization for unmapped names"""
    # Basic cleanup
    name = clean_engine_name(raw_name)
    
    # Handle common patterns
    if 'slowmate' in name.lower():
        # Extract version if present
        version_match = re.search(r'v?(\d+)\.(\d+)(?:\.(\d+))?', name, re.IGNORECASE)
        if version_match:
            major, minor, patch = version_match.groups()
            if patch and patch != '0':
                return f"SlowMate {major}.{minor}.{patch}"
            else:
                return f"SlowMate {major}.{minor}"
        return "SlowMate Unknown"
    
    return name

def test_name_mapping():
    """Test the name mapping system"""
    print("=== TESTING NAME MAPPING SYSTEM ===\n")
    
    # Load mapping
    name_mapping, rating_overrides = load_name_mapping()
    
    # Test cases
    test_names = [
        "SlowMate_v1.0_RELEASE",
        "SlowMate v1.0", 
        "Slowmate_current",
        "Cece_v2.0",
        "Cece v2.0",
        "Copycat_uci",
        "Copycat_v1.0",
        "Random_Opponent",
        "Random Playing Opponent",
        "Stockfish 1%",
        "Stockfish",
        "V7P3RAI_v1.0",
        "V7P3RAI v1.0",
        "SlowMate_v0.1.02_OPENING_ENDGAME",
        "Unknown_Engine_v1.0"
    ]
    
    print("🧪 TESTING NAME NORMALIZATION:")
    for name in test_names:
        normalized = normalize_engine_name_with_mapping(name, name_mapping)
        rating = rating_overrides.get(normalized, "No override")
        print(f"  '{name}' → '{normalized}' (Rating: {rating})")
    
    print(f"\n✅ Mapping covers {len(name_mapping)} name variants")
    if rating_overrides:
        print(f"📊 Rating overrides: {rating_overrides}")

if __name__ == "__main__":
    test_name_mapping()
