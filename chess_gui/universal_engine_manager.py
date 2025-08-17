"""
Universal Engine Discovery and Management System
Automatically discovers and configures available chess engines
"""

import os
import json
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass
from engine_interface import EngineInterface, UCIEngine, ChessAIEngine, create_engine_interface

@dataclass
class EngineConfig:
    """Configuration for a chess engine"""
    name: str
    type: str  # 'python', 'uci', 'csharp', 'executable'
    path: Optional[str] = None
    module_name: Optional[str] = None
    executable: Optional[str] = None
    description: str = ""
    version: str = "unknown"
    capabilities: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []

class UniversalEngineManager:
    """Enhanced engine manager with automatic discovery"""
    
    def __init__(self):
        self.engines: Dict[str, EngineInterface] = {}
        self.current_engine: Optional[str] = None
        self.available_configs: Dict[str, EngineConfig] = {}
        self.base_path = Path(__file__).parent.parent
        
        # Discover available engines
        self.discover_engines()
        
    def discover_engines(self):
        """Discover all available engines"""
        print("Discovering available chess engines...")
        
        # 1. Discover Python engines
        self._discover_python_engines()
        
        # 2. Discover UCI engines
        self._discover_uci_engines()
        
        # 3. Discover C# engines (our extracted opponents)
        self._discover_csharp_engines()
        
        # 4. Discover executable engines
        self._discover_executable_engines()
        
        print(f"Found {len(self.available_configs)} available engines")
        
    def _discover_python_engines(self):
        """Discover Python-based engines"""
        
        # Check for chess-ai engine (your main engine)
        # For now, we'll skip this since the module doesn't exist yet
        # You can uncomment this when you have a chess_ai module
        # try:
        #     import chess_ai
        #     config = EngineConfig(
        #         name="chess-ai",
        #         type="python",
        #         module_name="chess_ai",
        #         description="Your main chess engine with advanced features",
        #         capabilities=["detailed_metrics", "live_info", "time_control", "depth_control"]
        #     )
        #     self.available_configs["chess-ai"] = config
        #     print("  ✓ Found chess-ai (Python engine)")
        # except ImportError:
        #     print("  - chess-ai not available")
        pass
            
        # Check for engines in your engines directory
        engines_dir = self.base_path / "engines"
        if engines_dir.exists():
            for engine_path in engines_dir.iterdir():
                if engine_path.is_dir() and not engine_path.name.startswith('.'):
                    # Look for Python engines
                    main_py = engine_path / "main.py"
                    engine_py = engine_path / f"{engine_path.name}.py"
                    
                    if main_py.exists() or engine_py.exists():
                        config = EngineConfig(
                            name=engine_path.name,
                            type="python",
                            path=str(engine_path),
                            description=f"Python engine: {engine_path.name}",
                            capabilities=["basic"]
                        )
                        self.available_configs[engine_path.name] = config
                        print(f"  ✓ Found {engine_path.name} (Python engine)")
                        
    def _discover_uci_engines(self):
        """Discover UCI engines"""
        
        # Check common UCI engine locations
        uci_paths = [
            "C:/Program Files/Stockfish/stockfish.exe",
            "stockfish.exe",
            "./stockfish.exe",
            "/usr/local/bin/stockfish",
            "/usr/bin/stockfish"
        ]
        
        for path in uci_paths:
            if os.path.exists(path):
                engine_name = Path(path).stem.title()
                config = EngineConfig(
                    name=engine_name,
                    type="uci",
                    executable=path,
                    description=f"UCI engine: {engine_name}",
                    capabilities=["uci_standard"]
                )
                self.available_configs[engine_name] = config
                print(f"  ✓ Found {engine_name} (UCI engine)")
                
        # Check downloaded engines
        downloaded_dir = self.base_path / "downloaded_engines"
        if downloaded_dir.exists():
            for engine_path in downloaded_dir.iterdir():
                if engine_path.is_dir():
                    # Look for executables
                    for exe_file in engine_path.glob("*.exe"):
                        config = EngineConfig(
                            name=f"{engine_path.name}-{exe_file.stem}",
                            type="uci",
                            executable=str(exe_file),
                            description=f"Downloaded UCI engine: {exe_file.stem}",
                            capabilities=["uci_standard"]
                        )
                        self.available_configs[config.name] = config
                        print(f"  ✓ Found {config.name} (Downloaded UCI)")
                        
    def _discover_csharp_engines(self):
        """Discover C# engines (our extracted opponents)"""
        
        opponents_dir = self.base_path / "engines" / "Opponents"
        if not opponents_dir.exists():
            return
            
        # Load opponent configuration
        config_file = opponents_dir / "opponent_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    opponent_config = json.load(f)
                    
                for difficulty, bots in opponent_config["godot_opponents"].items():
                    for bot_info in bots:
                        bot_name = f"{bot_info['name']} ({bot_info['elo']} ELO)"
                        cs_file = opponents_dir / difficulty / f"{bot_info['name']}_Bot_{bot_info['bot_id']}.cs"
                        
                        if cs_file.exists():
                            config = EngineConfig(
                                name=bot_name,
                                type="csharp",
                                path=str(cs_file),
                                description=f"{bot_info['description']} (Difficulty: {difficulty})",
                                capabilities=["csharp_challenge_api"],
                                version=f"Bot_{bot_info['bot_id']}"
                            )
                            self.available_configs[bot_name] = config
                            print(f"  ✓ Found {bot_name} (C# opponent)")
                            
            except Exception as e:
                print(f"  - Error loading opponent config: {e}")
                
    def _discover_executable_engines(self):
        """Discover standalone executable engines"""
        
        # Check your compiled engines
        engines_dir = self.base_path / "engines"
        if engines_dir.exists():
            for engine_path in engines_dir.iterdir():
                if engine_path.is_dir():
                    # Look for compiled executables
                    for exe_file in engine_path.glob("*.exe"):
                        config = EngineConfig(
                            name=f"{engine_path.name}-{exe_file.stem}",
                            type="executable",
                            executable=str(exe_file),
                            description=f"Compiled engine: {exe_file.stem}",
                            capabilities=["executable"]
                        )
                        self.available_configs[config.name] = config
                        print(f"  ✓ Found {config.name} (Executable)")
                        
    def get_available_engines(self) -> Dict[str, EngineConfig]:
        """Get all available engine configurations"""
        return self.available_configs.copy()
        
    def load_engine(self, engine_name: str) -> bool:
        """Load an engine by name"""
        if engine_name not in self.available_configs:
            print(f"Engine {engine_name} not found in available configurations")
            return False
            
        config = self.available_configs[engine_name]
        
        try:
            if config.type == "python":
                if config.module_name == "chess_ai":
                    interface = create_engine_interface("chess-ai")
                else:
                    # Generic Python engine loading
                    interface = self._load_python_engine(config)
                    
            elif config.type == "uci":
                interface = create_engine_interface("uci", 
                                                  name=config.name, 
                                                  path=config.executable)
                                                  
            elif config.type == "csharp":
                # Use our C# wrapper
                if config.path:  # Check that path is not None
                    from csharp_engine_wrapper import create_csharp_engine
                    interface = create_csharp_engine(config.path, config.name)
                else:
                    print(f"C# engine {config.name} has no path configured")
                    return False
                
            elif config.type == "executable":
                # Try to treat as UCI first
                interface = create_engine_interface("uci",
                                                  name=config.name,
                                                  path=config.executable)
            else:
                print(f"Unsupported engine type: {config.type}")
                return False
                
            if interface and self.add_engine(interface):
                return True
                
        except Exception as e:
            print(f"Failed to load engine {engine_name}: {e}")
            
        return False
        
    def _load_python_engine(self, config: EngineConfig) -> Optional[EngineInterface]:
        """Load a generic Python engine"""
        # This would need to be implemented based on your Python engine standards
        # For now, return None as a placeholder
        print(f"Generic Python engine loading not yet implemented for {config.name}")
        return None
        
    def add_engine(self, interface: EngineInterface) -> bool:
        """Add an engine interface"""
        if interface.start():
            self.engines[interface.name] = interface
            if not self.current_engine:
                self.current_engine = interface.name
            print(f"Engine {interface.name} loaded successfully")
            return True
        else:
            print(f"Failed to start engine {interface.name}")
            return False
            
    def remove_engine(self, name: str):
        """Remove an engine interface"""
        if name in self.engines:
            self.engines[name].stop()
            del self.engines[name]
            if self.current_engine == name:
                self.current_engine = list(self.engines.keys())[0] if self.engines else None
                
    def set_current_engine(self, name: str) -> bool:
        """Set the current active engine"""
        if name in self.engines:
            self.current_engine = name
            print(f"Switched to engine: {name}")
            return True
        elif name in self.available_configs:
            # Try to load the engine
            if self.load_engine(name):
                self.current_engine = name
                return True
        return False
        
    def get_current_engine(self) -> Optional[EngineInterface]:
        """Get the current active engine"""
        if self.current_engine and self.current_engine in self.engines:
            return self.engines[self.current_engine]
        return None
        
    def list_engines(self) -> List[str]:
        """List all loaded engines"""
        return list(self.engines.keys())
        
    def list_available_engines(self) -> List[str]:
        """List all available engines (loaded and unloaded)"""
        return list(self.available_configs.keys())
        
    def get_engine_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about an engine"""
        if name in self.available_configs:
            config = self.available_configs[name]
            loaded = name in self.engines
            
            return {
                "name": config.name,
                "type": config.type,
                "description": config.description,
                "capabilities": config.capabilities,
                "loaded": loaded,
                "active": name == self.current_engine
            }
        return None
        
    def stop_all(self):
        """Stop all engines"""
        for engine in self.engines.values():
            engine.stop()
        self.engines.clear()
        self.current_engine = None
        
    def auto_load_default_engines(self):
        """Automatically load a reasonable set of default engines"""
        
        # Priority order for auto-loading
        preferred_engines = [
            "SlowMate-Slowmate_v1.0",  # User's preferred engine
            "chess-ai",  # Your main engine (if available)
        ]
        
        # Try to load at least one engine
        loaded_count = 0
        for engine_name in preferred_engines:
            if engine_name in self.available_configs:
                if self.load_engine(engine_name):
                    loaded_count += 1
                    break
                    
        # If no preferred engine loaded, try the first available
        if loaded_count == 0 and self.available_configs:
            # Try UCI engines first as they're most reliable
            uci_engines = [name for name, config in self.available_configs.items() if config.type == "uci"]
            if uci_engines:
                self.load_engine(uci_engines[0])
                loaded_count += 1
            else:
                # Try any available engine
                first_engine = list(self.available_configs.keys())[0]
                if self.load_engine(first_engine):
                    loaded_count += 1
                    
        print(f"Auto-loaded {loaded_count} engine(s)")
        return loaded_count > 0 or len(self.engines) > 0
