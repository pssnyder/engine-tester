"""
Godot Opponent Extractor
Extracts opponent bots from Tiny-Chess-Godot repository and organizes them by difficulty
"""

import json
import shutil
from pathlib import Path
import os

def extract_godot_opponents():
    """Extract and organize Godot opponents"""
    
    # Paths
    base_dir = Path(__file__).parent
    source_dir = base_dir / "source_repos" / "Tiny-Chess-Godot" / "scripts" / "chess-challenge" / "Bots"
    config_file = base_dir / "engines" / "Opponents" / "opponent_config.json"
    opponents_dir = base_dir / "engines" / "Opponents"
    
    # Load configuration
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    extraction_log = []
    
    for difficulty, bots in config["godot_opponents"].items():
        difficulty_dir = opponents_dir / difficulty
        difficulty_dir.mkdir(exist_ok=True)
        
        print(f"\nExtracting {difficulty} opponents:")
        
        for bot_info in bots:
            bot_id = bot_info["bot_id"]
            bot_name = bot_info["name"]
            source_file = source_dir / f"Bot_{bot_id}.cs"
            
            if source_file.exists():
                # Create destination file with descriptive name
                dest_file = difficulty_dir / f"{bot_name}_Bot_{bot_id}.cs"
                
                # Copy the file
                shutil.copy2(source_file, dest_file)
                
                # Create metadata file
                metadata = {
                    "name": bot_name,
                    "bot_id": bot_id,
                    "elo": bot_info["elo"],
                    "description": bot_info["description"],
                    "personality": bot_info["personality"],
                    "difficulty": difficulty,
                    "test_focus": bot_info["test_focus"],
                    "source_file": str(source_file),
                    "extracted_file": str(dest_file)
                }
                
                metadata_file = difficulty_dir / f"{bot_name}_Bot_{bot_id}_metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                print(f"  ✓ {bot_name} (Bot_{bot_id}) - {bot_info['elo']} ELO")
                extraction_log.append(metadata)
                
            else:
                print(f"  ✗ {bot_name} (Bot_{bot_id}) - SOURCE FILE NOT FOUND")
                extraction_log.append({
                    "name": bot_name,
                    "bot_id": bot_id,
                    "error": "Source file not found"
                })
    
    # Save extraction log
    log_file = opponents_dir / "extraction_log.json"
    with open(log_file, 'w') as f:
        json.dump(extraction_log, f, indent=2)
    
    print(f"\nExtraction complete. Log saved to: {log_file}")
    return extraction_log

def create_opponent_readme():
    """Create README for opponents directory"""
    
    base_dir = Path(__file__).parent
    config_file = base_dir / "engines" / "Opponents" / "opponent_config.json"
    readme_file = base_dir / "engines" / "Opponents" / "README.md"
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    readme_content = """# Chess Engine Opponents

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

"""
    
    for difficulty, bots in config["godot_opponents"].items():
        readme_content += f"\n### {difficulty.title()} ({config['difficulty_ranges'][difficulty]})\n\n"
        
        for bot in bots:
            readme_content += f"**{bot['name']}** (Bot_{bot['bot_id']}) - {bot['elo']} ELO\n"
            readme_content += f"- *Personality*: {bot['personality']}\n"
            readme_content += f"- *Description*: {bot['description']}\n"
            readme_content += f"- *Test Focus*: {', '.join(bot['test_focus'])}\n\n"
    
    readme_content += """
## Test Categories

"""
    
    for category, description in config["test_categories"].items():
        readme_content += f"**{category.replace('_', ' ').title()}**: {description}\n\n"
    
    readme_content += """
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

"""

    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"README created: {readme_file}")

if __name__ == "__main__":
    print("Extracting Godot opponents...")
    extraction_log = extract_godot_opponents()
    
    print("\nCreating documentation...")
    create_opponent_readme()
    
    print("\nSummary:")
    print(f"Successfully extracted: {len([log for log in extraction_log if 'error' not in log])} opponents")
    print(f"Failed extractions: {len([log for log in extraction_log if 'error' in log])} opponents")
