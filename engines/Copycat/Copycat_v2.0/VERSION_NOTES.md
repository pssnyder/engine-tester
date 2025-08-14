# Copycat Chess Engine v2.0.0 - Expanded Dataset Edition

## What's New
- **Massively Expanded Training Data**: Now trained on 2.27 million games from 125 different PGN files
- **Comprehensive Pattern Learning**: Analyzes ALL games rather than player-specific data for broader tactical knowledge
- **Enhanced Opening Library**: Covers a much wider range of openings and variations
- **Improved Move Selection**: Better move quality due to expanded statistical base

## Technical Changes
- Analysis dataset increased from ~100K games to 2.27M games
- Enhanced metadata analyzer with threading support for faster processing
- Incremental file processing system for efficient dataset updates
- More robust error handling for diverse PGN formats

## Performance
- Same UCI interface as v1.0 - drop-in replacement
- Analysis file size: ~1.1GB (expanded from previous versions)
- No changes to core engine algorithms - only expanded knowledge base

## Tournament Usage
This version can be run alongside v1.0 for comparison testing. The engine will identify itself as "Copycat Chess Engine v2.0.0" in tournaments.

## Files Changed from v1.0
- `results/enhanced_analysis.json` - Replaced with expanded 2.27M game dataset
- `copycat_uci.py` - Version number updated to 2.0.0
- This README added

Generated: August 13, 2025
