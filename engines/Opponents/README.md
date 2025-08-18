# Chess Engine Opponents

This directory contains extracted opponent bots from Sebastian Lague's Tiny Chess Godot project, organized by difficulty level for progressive testing.

## Directory Structure

```
Opponents/
├── beginner/     # 192-500 ELO - Basic patterns and exploitable weaknesses
├── intermediate/ # 501-1300 ELO - Tactical awareness and basic strategy  
├── advanced/     # 1301-2200 ELO - Advanced positioning and search depth
├── expert/       # 2201+ ELO - Master-level play and optimization
└── opponent_config.json # Configuration and metadata
```

## Opponents by Difficulty


### Beginner (192-500 ELO - Basic patterns and exploitable weaknesses)

**CopyCat** (Bot_17) - 192 ELO
- *Personality*: copycat
- *Description*: Mirrors opponent moves - perfect for testing pattern recognition
- *Test Focus*: pattern_recognition, move_mirroring

**BongcloudEnthusiast** (Bot_278) - 307 ELO
- *Personality*: opening_specialist
- *Description*: Always plays bongcloud opening - tests opening exploitation
- *Test Focus*: opening_exploitation, poor_opening_punishment


### Intermediate (501-1300 ELO - Tactical awareness and basic strategy)

**WhateverBot** (Bot_153) - 677 ELO
- *Personality*: basic_tactical
- *Description*: 1-move lookahead with basic tactics
- *Test Focus*: basic_tactics, piece_development, safety

**applemethod** (Bot_70) - 1085 ELO
- *Personality*: material_tempo
- *Description*: Material and tempo focused with multi-move search
- *Test Focus*: material_evaluation, tempo, multi_move_search

**Squeedo** (Bot_253) - 1276 ELO
- *Personality*: positional
- *Description*: Pawn advancement and piece development focused
- *Test Focus*: pawn_structure, piece_development, mobility


### Advanced (1301-2200 ELO - Advanced positioning and search depth)

**Monstrosity200** (Bot_425) - 1569 ELO
- *Personality*: efficient
- *Description*: 200-token efficiency challenge - mobility focused
- *Test Focus*: code_efficiency, mobility, material

**GameTechExplained** (Bot_266) - 1713 ELO
- *Personality*: positional_advanced
- *Description*: Positional understanding and piece placement
- *Test Focus*: positional_understanding, piece_placement

**ElectricShockwaveGambit** (Bot_303) - 2001 ELO
- *Personality*: mobility_safety
- *Description*: Mobility and safety focused with deep search
- *Test Focus*: piece_mobility, piece_safety, deep_search

**KingGambotIV** (Bot_628) - 2172 ELO
- *Personality*: aggressive_king
- *Description*: Aggressive king play with deep search techniques
- *Test Focus*: aggressive_play, king_activity, unconventional_strategies


### Expert (2201+ ELO - Master-level play and optimization)

**NNBot** (Bot_529) - 2246 ELO
- *Personality*: neural_network
- *Description*: Neural network evaluation with compressed AI
- *Test Focus*: neural_evaluation, tempo, advanced_positioning

**TinyHugeBot** (Bot_610) - 2513 ELO
- *Personality*: search_optimized
- *Description*: Code compression exploit with optimized deep search
- *Test Focus*: deep_search, search_optimization, piece_placement

**Boychesser** (Bot_614) - 2772 ELO
- *Personality*: tactical_master
- *Description*: Tournament winner - tactical excellence and deep search
- *Test Focus*: tactical_combinations, deep_search, positional_mastery, endgame


## Test Categories

**Pattern Recognition**: Tests engine's ability to recognize and counter repetitive patterns

**Opening Exploitation**: Tests engine's ability to punish poor opening choices

**Basic Tactics**: Tests fundamental tactical awareness (pins, forks, skewers)

**Material Evaluation**: Tests accurate piece value assessment

**Tempo**: Tests understanding of move timing and initiative

**Pawn Structure**: Tests pawn formation and advancement strategies

**Piece Development**: Tests proper piece placement and development

**Mobility**: Tests preference for piece activity and movement options

**Piece Safety**: Tests ability to protect pieces and avoid blunders

**Positional Understanding**: Tests long-term strategic planning

**Deep Search**: Tests engine's search depth and calculation ability

**Aggressive Play**: Tests response to unconventional aggressive strategies

**Neural Evaluation**: Tests against AI-based position evaluation

**Search Optimization**: Tests against highly optimized search algorithms

**Tactical Combinations**: Tests complex tactical sequence recognition

**Endgame**: Tests endgame technique and conversion ability


## Usage

Each opponent bot comes with:
- `.cs` file: C# source code
- `_metadata.json` file: Detailed information about the bot

Use the C# Engine Wrapper in `chess_gui/csharp_engine_wrapper.py` to integrate these opponents with your testing framework.

## Integration

These opponents are designed to test specific aspects of your chess engine:

1. **Progressive Difficulty**: Start with beginner bots and work your way up
2. **Personality Testing**: Each bot has unique characteristics to exploit or counter
3. **Focused Testing**: Use the test_focus categories to target specific engine capabilities

