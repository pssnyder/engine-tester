# 🤖 Automated Engine Battle Framework

A comprehensive, modular system for automated chess engine testing and comparison. Features real-time monitoring, multiple challenge types, and extensible architecture.

## 🎯 Quick Start

### Run a Demo Battle
```bash
cd automated_battle_framework
python battle_runner.py --mode demo
```

### Run with Real-time Dashboard
```bash
python battle_runner.py --mode demo --dashboard
```

### Run Comprehensive Battle
```bash
python battle_runner.py --mode comprehensive --dashboard
```

### Run Engine Gauntlet
```bash
python battle_runner.py --mode gauntlet --engines V7P3R SlowMate C0BR4
```

## 📁 Framework Structure

```
automated_battle_framework/
├── engine_battle_framework.py     # Core framework and UCI engine handling
├── advanced_challenges.py         # Extended challenge types (puzzles, depth, tactical)
├── terminal_dashboard.py          # Real-time monitoring dashboard
├── battle_runner.py              # Simple runner script (recommended)
├── enhanced_battle_framework.py   # Full-featured framework (advanced)
└── battle_results/               # Results directory (auto-created)
```

## 🎮 Available Challenge Types

### Core Challenges (Implemented)
- **Speed Challenge**: Fast-paced games with time constraints
- **Traditional Game**: Standard chess games with move limits
- **Puzzle Solving**: Tactical puzzle recognition and solving
- **Depth Analysis**: Search depth comparison under time limits
- **Position Analysis**: Evaluation accuracy on known positions  
- **Tactical Challenge**: Pattern recognition (pins, forks, discoveries)

### Future Challenges (Planned)
- Endgame challenges
- Opening book analysis
- Time management evaluation
- Blunder detection and recovery

## 🖥️ Dashboard Features

The terminal dashboard provides real-time monitoring with:

- **Live Progress**: Current challenge progress and status
- **Session Summary**: Win/loss statistics and performance metrics
- **Recent Results**: Last 10-15 challenge outcomes
- **Detailed Metrics**: Nodes per second, search depth, accuracy
- **Resource Usage**: CPU and memory utilization (if available)

### Dashboard Controls
- `q` - Quit dashboard
- `r` - Refresh display
- `c` - Clear screen

## 🔧 Engine Configuration

The framework automatically detects and configures engines based on standard paths:

### Supported Engines
- **V7P3R**: Python-based engine with advanced search
- **SlowMate**: Educational Python engine with clear algorithms
- **C0BR4**: Control engine (C# executable) for baseline metrics

### Adding New Engines
```python
from engine_battle_framework import EngineConfig

new_engine = EngineConfig(
    name="MyEngine",
    path="/path/to/engine/directory",
    executable="python",  # or direct executable path
    args=["my_engine.py"],  # command line arguments
    type="python"  # or "executable"
)
```

## 📊 Results and Metrics

### Session Results
All battle sessions are saved in JSON format in the `battle_results/` directory:

```json
{
  "session_id": "battle_1234567890",
  "name": "Comprehensive_Engine_Battle",
  "start_time": "2024-01-15T10:30:00",
  "total_duration": 45.6,
  "engines": [...],
  "challenges": [...]
}
```

### Key Metrics Tracked
- **Win/Loss Records**: Per engine across all challenge types
- **Execution Time**: Time taken for each challenge
- **Search Metrics**: Nodes analyzed, search depth achieved
- **Accuracy Scores**: Puzzle solving and position evaluation accuracy
- **Performance Trends**: Speed and efficiency over time

## 🛠️ Development and Extension

### Adding New Challenge Types

1. Create a new challenge class inheriting from `ChallengeBase`:

```python
class MyCustomChallenge(ChallengeBase):
    def __init__(self):
        super().__init__(ChallengeType.MY_CUSTOM)
    
    async def execute(self, engine1: UCIEngine, engine2: UCIEngine, **kwargs) -> ChallengeResult:
        # Implement your challenge logic
        pass
```

2. Register the challenge in the framework:

```python
framework.challenges[ChallengeType.MY_CUSTOM] = MyCustomChallenge()
```

### Dashboard Customization

The dashboard is highly configurable:

```python
config = DashboardConfig(
    refresh_rate=0.5,        # Update frequency (seconds)
    max_recent_results=20,   # Number of recent results to show
    show_detailed_metrics=True,  # Show advanced metrics
    compact_mode=False       # Use compact display
)
```

## 🐛 Troubleshooting

### Common Issues

1. **Engine Not Found**: Ensure engine paths are correct and engines are UCI-compatible
2. **Dashboard Not Working**: Install colorama: `pip install colorama`
3. **Timeouts**: Increase time limits for slower engines or complex positions
4. **Memory Issues**: Run fewer concurrent challenges or reduce search depth

### Debug Mode
Enable detailed logging by setting the log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Engine Validation
Test individual engines before running battles:

```bash
# Test V7P3R
cd "path/to/v7p3r"
python play_chess.py

# Test SlowMate  
cd "path/to/slowmate/src"
python slowmate_uci.py
```

## 📋 Requirements

- Python 3.8+
- asyncio support
- pathlib
- Optional: colorama (for colored dashboard output)
- Optional: psutil (for resource monitoring)

## 🎨 Usage Examples

### Basic Demo
```bash
python battle_runner.py --mode demo
```

### Comprehensive with Dashboard
```bash
python battle_runner.py --mode comprehensive --dashboard
```

### Custom Gauntlet
```bash
python battle_runner.py --mode gauntlet --engines V7P3R SlowMate C0BR4 --dashboard
```

### Dashboard Demo Mode
```bash
python terminal_dashboard.py --demo
```

## 🔮 Future Enhancements

- **Web Dashboard**: Browser-based monitoring interface
- **Tournament Brackets**: Swiss system and round-robin tournaments
- **Historical Analysis**: Compare engine versions over time
- **Cloud Integration**: Distribute battles across multiple machines
- **Machine Learning**: Analyze engine behavior patterns
- **Opening Book Testing**: Compare opening repertoires
- **Endgame Tablebase**: Verify endgame play accuracy

## 📄 License

This framework is designed for educational and research purposes. Ensure you have appropriate rights to use the chess engines you test.

---

🎯 **Ready to battle?** Start with `python battle_runner.py --mode demo --dashboard` and watch your engines compete in real-time!
