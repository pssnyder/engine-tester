#!/usr/bin/env python3
"""
Quick Tournament Launcher
Load configuration from JSON and run tournament
"""

import json
import sys
from pathlib import Path
from tournament_manager import (
    TournamentManager, EngineConfig, TimeControl,
    ResignationRules, AdjudicationRules
)


def load_config(config_path: str):
    """Load tournament configuration from JSON"""
    with open(config_path, 'r') as f:
        return json.load(f)


def run_from_config(config_path: str = "tournament_config.json"):
    """Run tournament from configuration file"""
    print(f"Loading configuration from {config_path}...")
    config = load_config(config_path)
    
    # Parse engines
    engines = [
        EngineConfig(
            name=e["name"],
            path=e["path"],
            short_name=e.get("short_name", e["name"][:8]),
            expected_elo=e.get("expected_elo", 1500)
        )
        for e in config["engines"]
    ]
    
    # Parse time control
    time_control = TimeControl.from_string(config["time_control"])
    
    # Parse rules
    resignation_rules = ResignationRules(**config["resignation_rules"])
    adjudication_rules = AdjudicationRules(**config["adjudication_rules"])
    
    # Create tournament
    tournament = TournamentManager(
        engines=engines,
        time_control=time_control,
        starting_positions_dir=config["starting_positions"]["pgn_directory"],
        num_games_per_pairing=config["games_per_pairing"],
        parallel_games=config["parallel_games"],
        resignation_rules=resignation_rules,
        adjudication_rules=adjudication_rules
    )
    
    # Run tournament
    tournament.run_tournament()


if __name__ == "__main__":
    config_file = sys.argv[1] if len(sys.argv) > 1 else "tournament_config.json"
    run_from_config(config_file)
