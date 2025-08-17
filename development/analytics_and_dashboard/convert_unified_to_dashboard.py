#!/usr/bin/env python3
"""
Convert unified tournament analysis data to dashboard-compatible format
"""

import json
import os
from datetime import datetime

def load_unified_analysis():
    """Load the unified tournament analysis data"""
    unified_path = "results/unified_tournament_analysis.json"
    if not os.path.exists(unified_path):
        print(f"Error: {unified_path} not found")
        return None
    
    with open(unified_path, 'r') as f:
        return json.load(f)

def create_analysis_summary(unified_data):
    """Create analysis_summary.json from unified data"""
    summary_data = unified_data.get("summary", {})
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_games": summary_data.get("total_games", 0),
        "total_tournaments": summary_data.get("total_tournaments", 0),
        "total_engines": summary_data.get("total_engines", 0),
        "date_range": {
            "start": unified_data.get("earliest_game", ""),
            "end": unified_data.get("latest_game", "")
        }
    }
    
    # Save to file
    with open("results/analysis_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Created analysis_summary.json with {summary['total_games']} games")
    return summary

def create_player_stats(unified_data):
    """Create player_stats.json from unified data"""
    engine_details = unified_data.get("engine_details", {})
    
    player_stats = {}
    for engine_name, details in engine_details.items():
        performance = details.get("performance", {})
        player_stats[engine_name] = {
            "games_played": performance.get("total_games", 0),
            "wins": performance.get("wins", 0),
            "draws": performance.get("draws", 0),
            "losses": performance.get("losses", 0),
            "win_rate": performance.get("win_rate", 0),
            "estimated_rating": performance.get("estimated_rating", 1200),
            "performance_rating": performance.get("performance_rating", 1200),
            "tournaments": len(details.get("tournaments", []))
        }
    
    # Save to file
    with open("results/player_stats.json", 'w') as f:
        json.dump(player_stats, f, indent=2)
    
    print(f"✅ Created player_stats.json with {len(player_stats)} engines")
    return player_stats

def create_piece_heatmaps():
    """Create basic piece_heatmaps.json if it doesn't exist"""
    heatmap_path = "results/piece_heatmaps.json"
    if os.path.exists(heatmap_path):
        print("✅ piece_heatmaps.json already exists")
        return
    
    # Create basic heatmap structure
    heatmaps = {
        "white": {
            "pawn": [[0 for _ in range(8)] for _ in range(8)],
            "knight": [[0 for _ in range(8)] for _ in range(8)],
            "bishop": [[0 for _ in range(8)] for _ in range(8)],
            "rook": [[0 for _ in range(8)] for _ in range(8)],
            "queen": [[0 for _ in range(8)] for _ in range(8)],
            "king": [[0 for _ in range(8)] for _ in range(8)]
        },
        "black": {
            "pawn": [[0 for _ in range(8)] for _ in range(8)],
            "knight": [[0 for _ in range(8)] for _ in range(8)],
            "bishop": [[0 for _ in range(8)] for _ in range(8)],
            "rook": [[0 for _ in range(8)] for _ in range(8)],
            "queen": [[0 for _ in range(8)] for _ in range(8)],
            "king": [[0 for _ in range(8)] for _ in range(8)]
        }
    }
    
    with open(heatmap_path, 'w') as f:
        json.dump(heatmaps, f, indent=2)
    
    print("✅ Created basic piece_heatmaps.json")

def main():
    """Main conversion function"""
    print("🔄 Converting unified tournament analysis to dashboard format...")
    
    # Load unified data
    unified_data = load_unified_analysis()
    if not unified_data:
        return False
    
    # Create dashboard-compatible files
    create_analysis_summary(unified_data)
    create_player_stats(unified_data)
    create_piece_heatmaps()
    
    print("✅ Conversion complete! Dashboard files updated.")
    return True

if __name__ == "__main__":
    main()
