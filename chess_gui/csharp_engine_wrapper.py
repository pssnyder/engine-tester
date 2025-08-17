"""
C# Chess Engine Wrapper
Provides interface between Python chess testing framework and C# chess engines
"""

import subprocess
import json
import os
import tempfile
from typing import Optional, Dict, List, Any
import chess
import chess.engine
from pathlib import Path
from engine_interface import EngineInterface

class CSharpEngineWrapper:
    """Wrapper for C# chess engines using Chess Challenge API"""
    
    def __init__(self, bot_file_path: str, bot_name: str, working_dir: Optional[str] = None):
        self.bot_file_path = Path(bot_file_path)
        self.bot_name = bot_name
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.temp_dir = None
        self.compiled_exe = None
        self.process = None
        
    def __enter__(self):
        """Context manager entry"""
        self.setup()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
        
    def setup(self):
        """Set up the C# engine for use"""
        self.temp_dir = Path(tempfile.mkdtemp(prefix=f"chess_engine_{self.bot_name}_"))
        self._create_project()
        self._compile_engine()
        
    def cleanup(self):
        """Clean up temporary files and processes"""
        if self.process:
            self.process.terminate()
            self.process = None
        # Note: We'll leave temp files for debugging, but could clean them up here
        
    def _create_project(self):
        """Create a standalone C# project for the bot"""
        project_template = '''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net6.0</TargetFramework>
    <ImplicitUsings>disable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <AllowUnsafeBlocks>True</AllowUnsafeBlocks>
  </PropertyGroup>
</Project>'''
        
        # Create project file
        project_file = self.temp_dir / f"{self.bot_name}.csproj"
        with open(project_file, 'w') as f:
            f.write(project_template)
            
        # Copy the Chess Challenge API (we'll need to extract this)
        self._copy_chess_api()
        
        # Copy the bot file
        self._copy_and_adapt_bot()
        
    def _copy_chess_api(self):
        """Copy Chess Challenge API to temp directory"""
        # This will need to be implemented - extract API from source_repos
        api_dir = self.temp_dir / "API"
        api_dir.mkdir(exist_ok=True)
        
        # For now, create a placeholder
        # TODO: Extract actual API files from Chess-Challenge repo
        pass
        
    def _copy_and_adapt_bot(self):
        """Copy bot file and adapt it for standalone use"""
        # Read original bot
        with open(self.bot_file_path, 'r') as f:
            bot_content = f.read()
            
        # Create main program wrapper
        main_program = f'''
using System;
using System.Text.Json;

namespace ChessEngineWrapper
{{
    class Program
    {{
        static void Main(string[] args)
        {{
            var engine = new EngineInterface();
            engine.Run();
        }}
    }}
    
    class EngineInterface
    {{
        public void Run()
        {{
            string line;
            while ((line = Console.ReadLine()) != null)
            {{
                try
                {{
                    var command = JsonSerializer.Deserialize<EngineCommand>(line);
                    ProcessCommand(command);
                }}
                catch (Exception ex)
                {{
                    Console.WriteLine(JsonSerializer.Serialize(new {{ error = ex.Message }}));
                }}
            }}
        }}
        
        private void ProcessCommand(EngineCommand command)
        {{
            switch (command.Type)
            {{
                case "ping":
                    Console.WriteLine(JsonSerializer.Serialize(new {{ response = "pong" }}));
                    break;
                case "get_move":
                    // TODO: Implement move calculation
                    Console.WriteLine(JsonSerializer.Serialize(new {{ move = "e2e4" }}));
                    break;
                default:
                    Console.WriteLine(JsonSerializer.Serialize(new {{ error = "Unknown command" }}));
                    break;
            }}
        }}
    }}
    
    class EngineCommand
    {{
        public string Type {{ get; set; }}
        public string Fen {{ get; set; }}
        public int TimeMs {{ get; set; }}
    }}
}}

{bot_content}
'''
        
        # Write adapted bot
        program_file = self.temp_dir / "Program.cs"
        with open(program_file, 'w') as f:
            f.write(main_program)
            
    def _compile_engine(self):
        """Compile the C# engine"""
        try:
            result = subprocess.run(
                ["dotnet", "build", "-c", "Release"],
                cwd=self.temp_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Find compiled executable
            bin_dir = self.temp_dir / "bin" / "Release" / "net6.0"
            self.compiled_exe = bin_dir / f"{self.bot_name}.exe"
            
            if not self.compiled_exe.exists():
                self.compiled_exe = bin_dir / f"{self.bot_name}.dll"
                
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to compile engine: {e.stderr}")
            
    def start_engine(self):
        """Start the engine process"""
        if not self.compiled_exe:
            raise RuntimeError("Engine not compiled")
            
        cmd = ["dotnet", str(self.compiled_exe)] if self.compiled_exe.suffix == ".dll" else [str(self.compiled_exe)]
        
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
    def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send command to engine and get response"""
        if not self.process:
            self.start_engine()
            
        command_json = json.dumps(command)
        self.process.stdin.write(command_json + "\n")
        self.process.stdin.flush()
        
        response_line = self.process.stdout.readline()
        return json.loads(response_line)
        
    def get_move(self, fen: str, time_ms: int = 1000) -> str:
        """Get next move from engine"""
        command = {
            "type": "get_move",
            "fen": fen,
            "time_ms": time_ms
        }
        
        response = self.send_command(command)
        if "error" in response:
            raise RuntimeError(f"Engine error: {response['error']}")
            
        return response.get("move", "")
        
    def ping(self) -> bool:
        """Test if engine is responding"""
        try:
            response = self.send_command({"type": "ping"})
            return response.get("response") == "pong"
        except:
            return False


class CSharpEngineAdapter(EngineInterface):
    """Adapter to make C# engines work with python-chess"""
    
    def __init__(self, wrapper: CSharpEngineWrapper):
        super().__init__(wrapper.bot_name)
        self.wrapper = wrapper
        
    def start(self) -> bool:
        """Start the C# engine"""
        try:
            self.wrapper.setup()
            return True
        except Exception as e:
            print(f"Failed to start C# engine: {e}")
            return False
        
    def stop(self):
        """Stop the C# engine"""
        self.wrapper.cleanup()
        
    def get_move(self, board: chess.Board, time_limit: float = 1.0, depth: Optional[int] = None) -> Optional[str]:
        """Get next move from C# engine"""
        try:
            fen = board.fen()
            time_ms = int(time_limit * 1000)
            move_str = self.wrapper.get_move(fen, time_ms)
            return move_str
        except Exception as e:
            print(f"Error getting move from C# engine: {e}")
            return None
        
    def evaluate_position(self, board: chess.Board, depth: Optional[int] = None) -> Dict[str, Any]:
        """Evaluate position using C# engine"""
        try:
            # For now, just get a move as evaluation
            move = self.get_move(board, 0.1, depth)
            return {
                "best_move": move,
                "score": "unknown",
                "depth": depth or 1
            }
        except Exception as e:
            print(f"Error evaluating position with C# engine: {e}")
            return {}
        
    def is_ready(self) -> bool:
        """Check if C# engine is ready"""
        return self.wrapper.ping()


def create_csharp_engine(bot_path: str, bot_name: str) -> CSharpEngineAdapter:
    """Create a C# engine adapter"""
    wrapper = CSharpEngineWrapper(bot_path, bot_name)
    wrapper.setup()
    return CSharpEngineAdapter(wrapper)
