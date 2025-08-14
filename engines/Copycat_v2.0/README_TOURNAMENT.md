# Copycat Chess Engine v2.0.0 - Tournament Package

## Installation for Arena Chess GUI

1. **Copy this entire folder** to your Chess Engines directory:
   ```
   Copy "Copycat_v2.0" folder to: 
   [Arena Installation]/Engines/Copycat_v2.0/
   ```

2. **Add to Arena:**
   - Open Arena Chess GUI
   - Go to Engines → Install New Engine
   - Navigate to: `[Arena Installation]/Engines/Copycat_v2.0/`
   - Select: `CopycatChess_v2.0.0.exe`
   - Engine Name: `Copycat Chess v2.0.0`

## Engine Details

- **Name**: Copycat Chess Engine (Data Analytics Edition)
- **Version**: 2.0.0
- **Author**: v7p3r (Analytics by GitHub Copilot)
- **Protocol**: UCI
- **Training Data**: 2.27 million games from 125 PGN files
- **File Size**: ~180MB (includes embedded analysis data)

## UCI Options

- **Hash**: Memory for transposition table (1-1024 MB, default: 16)
- **Style Consistency**: How closely to follow analyzed patterns (0-100, default: 50)
- **Decisiveness**: Preference for tactical vs positional play (0-100, default: 50)
- **Debug**: Enable debug output (true/false, default: false)

## Tournament Usage

This engine can run alongside Copycat v1.0 for comparison matches:
- **v1.0**: Trained on ~100K games (original dataset)
- **v2.0**: Trained on 2.27M games (expanded dataset)

The engines will show different playing styles due to the vastly different training data.

## Technical Notes

- **No Installation Required**: Self-contained executable with embedded data
- **No Dependencies**: All required libraries included
- **Platform**: Windows x64
- **Time Control**: Supports all standard time controls
- **Opening Book**: Built-in pattern-based opening selection

## Support

For issues or questions, refer to the version notes included in this package.

---
Generated: August 13, 2025
Package: Tournament Distribution v2.0.0
