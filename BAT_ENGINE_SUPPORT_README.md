# Universal Puzzle Analyzer - .bat Engine Support Update

## Overview
Updated the Universal Puzzle Analyzer to support both .exe and .bat engine files, enabling testing of Python-based chess engines that run through batch files.

## Changes Made

### 1. Engine Type Detection
- Added `_detect_engine_type()` method to automatically detect .bat vs .exe files
- Added `_build_engine_command()` method to construct proper launch commands

### 2. Process Launch Updates
- **For .bat files**: Uses `['cmd.exe', '/c', bat_path]` command
- **For .exe files**: Uses `[exe_path]` command (unchanged)
- **Working directory**: Sets proper `cwd` for .bat files to ensure relative paths work

### 3. Updated Methods
- `get_engine_info()` - Updated subprocess.Popen call
- `get_engine_move()` - Updated subprocess.Popen call  
- `get_engine_move_with_time_control()` - Updated subprocess.Popen call

### 4. Documentation Updates
- Updated argument parser description to mention .bat support
- Updated help text for --engine parameter

## Technical Details

### Engine Detection Logic
```python
def _detect_engine_type(self, engine_path: str) -> str:
    path_lower = engine_path.lower()
    if path_lower.endswith('.bat'):
        return 'bat'
    elif path_lower.endswith('.exe'):
        return 'exe'
    else:
        return 'exe'  # Default
```

### Command Building Logic
```python
def _build_engine_command(self, engine_path: str) -> List[str]:
    if self.engine_type == 'bat':
        return ['cmd.exe', '/c', engine_path]
    else:
        return [engine_path]
```

### Process Launch Example
```python
process = subprocess.Popen(
    self.engine_command,  # ['cmd.exe', '/c', 'engine.bat'] or ['engine.exe']
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=0,
    cwd=os.path.dirname(self.engine_path) if self.engine_type == 'bat' else None
)
```

## Testing Results

### V7P3R v14.2 (.bat engine)
- ✅ Engine type detected: bat
- ✅ UCI communication: "id name V7P3R v12.6"
- ✅ Move generation: f2f3 (starting position), d7d5 (after 1.e4)

### Stockfish (.exe engine) 
- ✅ Engine type detected: exe
- ✅ UCI communication: "id name Stockfish 17.1"
- ✅ Move generation: e2e4 (starting position), e7e5 (after 1.e4)

## Usage Examples

### With .bat Engine (NEW)
```bash
python -m engine_utilities.universal_puzzle_analyzer \
  --engine engines\V7P3R\V7P3R_v14.2\V7P3R_v14.2.bat \
  --puzzles 100 --time 10
```

### With .exe Engine (Still Works)
```bash
python -m engine_utilities.universal_puzzle_analyzer \
  --engine engines\Stockfish\stockfish.exe \
  --puzzles 100 --time 5
```

## Benefits

1. **Cloud Deployment Ready**: Python engines can run on cloud VMs without compilation
2. **Development Friendly**: Easy debugging and modification of engine code
3. **Version Control**: Engine source code is directly version-controlled
4. **Cross-Platform**: Python engines work across different operating systems
5. **Backward Compatible**: All existing .exe engines continue to work unchanged

## Files Modified

- `engine_utilities/universal_puzzle_analyzer.py` - Main analyzer with .bat support
- Added demonstration scripts to verify functionality

The Universal Puzzle Analyzer now seamlessly supports both .exe and .bat engines, enabling comprehensive testing of both compiled and Python-based chess engines.