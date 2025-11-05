# RANDOM OPPONENT ENGINE
This is a simple chess engine that selects moves randomly from the list of legal moves. It is designed to be used as an opponent in chess software that supports the UCI (Universal Chess Interface) protocol.

## Features
- **Random Move Selection**: Chooses moves uniformly at random from all legal moves.
- **UCI Compatibility**: Can be integrated with any chess GUI that supports UCI.
- **Lightweight**: Minimal computational overhead, making it suitable for quick testing or casual play.

## Usage
### UCI Interface
```bash
./RandomOpponent.bat
```

### Direct API
```python
from random_opponent import RandomOpponent

engine = RandomOpponent()