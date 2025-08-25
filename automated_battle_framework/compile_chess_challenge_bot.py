#!/usr/bin/env python3
"""
Chess Challenge Bot Compiler
Compiles rated C# Chess Challenge bots into UCI-compatible engines for testing
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
import json

class ChessChallengeBotCompiler:
    def __init__(self):
        self.engine_tester_root = Path("s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester")
        self.chess_challenge_source = self.engine_tester_root / "source_repos" / "Chess-Challenge" / "Chess-Challenge"
        self.opponents_dir = self.engine_tester_root / "engines" / "Opponents"
        self.compiled_engines_dir = self.engine_tester_root / "engines" / "compiled_cs_bots"
        
        # Ensure compiled engines directory exists
        self.compiled_engines_dir.mkdir(exist_ok=True)
        
    def find_rated_bots(self):
        """Find all rated C# bots in the Opponents directory"""
        bots = []
        for difficulty in ['beginner', 'intermediate', 'advanced', 'expert']:
            difficulty_dir = self.opponents_dir / difficulty
            if difficulty_dir.exists():
                for cs_file in difficulty_dir.glob("*.cs"):
                    bot_name = cs_file.stem
                    bots.append({
                        'name': bot_name,
                        'path': cs_file,
                        'difficulty': difficulty
                    })
        return bots
    
    def load_bot_ratings(self):
        """Load bot ratings from opponent_config.json"""
        config_file = self.opponents_dir / "opponent_config.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def compile_bot(self, bot_info):
        """Compile a single C# bot into a UCI engine"""
        print(f"🔨 Compiling {bot_info['name']} ({bot_info['difficulty']})...")
        
        # Create temporary working directory
        with tempfile.TemporaryDirectory(prefix=f"compile_{bot_info['name']}_") as temp_dir:
            temp_path = Path(temp_dir)
            
            # Copy Chess Challenge framework
            framework_dest = temp_path / "Chess-Challenge"
            shutil.copytree(self.chess_challenge_source, framework_dest)
            
            # Copy bot file to My Bot directory
            my_bot_dir = framework_dest / "src" / "My Bot"
            bot_dest = my_bot_dir / "MyBot.cs"
            
            # Read and adapt bot content
            with open(bot_info['path'], 'r') as f:
                bot_content = f.read()
            
            # Replace the bot class name with MyBot for framework compatibility
            original_class = f"Bot_{bot_info['name'].split('_')[-1]}"
            adapted_content = bot_content.replace(f"class {original_class}", "class MyBot")
            adapted_content = adapted_content.replace(f"public class {original_class}", "public class MyBot")
            
            # Write adapted bot
            with open(bot_dest, 'w') as f:
                f.write(adapted_content)
            
            # Build the project
            try:
                result = subprocess.run(
                    ["dotnet", "build", "-c", "Release"],
                    cwd=framework_dest,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Find the compiled executable
                bin_dir = framework_dest / "bin" / "Release" / "net6.0"
                source_exe = bin_dir / "Chess-Challenge.exe"
                
                if not source_exe.exists():
                    # Try .dll
                    source_exe = bin_dir / "Chess-Challenge.dll"
                
                if source_exe.exists():
                    # Copy to compiled engines directory
                    dest_name = f"{bot_info['name']}.{source_exe.suffix}"
                    dest_path = self.compiled_engines_dir / dest_name
                    shutil.copy2(source_exe, dest_path)
                    
                    print(f"✅ Successfully compiled {bot_info['name']} -> {dest_name}")
                    return dest_path
                else:
                    print(f"❌ Could not find compiled executable for {bot_info['name']}")
                    return None
                    
            except subprocess.CalledProcessError as e:
                print(f"❌ Compilation failed for {bot_info['name']}: {e.stderr}")
                return None
    
    def compile_all_bots(self):
        """Compile all rated bots"""
        bots = self.find_rated_bots()
        ratings = self.load_bot_ratings()
        
        compiled_bots = []
        
        print(f"🎯 Found {len(bots)} rated bots to compile...")
        
        for bot_info in bots:
            compiled_path = self.compile_bot(bot_info)
            if compiled_path:
                # Get rating info
                bot_rating_info = None
                for rating_entry in ratings.get('opponents', []):
                    if bot_info['name'] in rating_entry.get('name', ''):
                        bot_rating_info = rating_entry
                        break
                
                compiled_bots.append({
                    'name': bot_info['name'],
                    'path': compiled_path,
                    'difficulty': bot_info['difficulty'],
                    'rating': bot_rating_info.get('elo', 'Unknown') if bot_rating_info else 'Unknown',
                    'description': bot_rating_info.get('description', '') if bot_rating_info else ''
                })
        
        # Save compilation results
        results_file = self.compiled_engines_dir / "compiled_bots.json"
        with open(results_file, 'w') as f:
            json.dump(compiled_bots, f, indent=2)
        
        print(f"\n🏆 Compilation Summary:")
        print(f"Successfully compiled: {len(compiled_bots)}/{len(bots)} bots")
        
        for bot in compiled_bots:
            print(f"  ✅ {bot['name']} (ELO: {bot['rating']}) -> {bot['path'].name}")
        
        return compiled_bots
    
    def test_single_bot(self, bot_name):
        """Compile and test a single bot"""
        bots = self.find_rated_bots()
        target_bot = None
        
        for bot in bots:
            if bot_name.lower() in bot['name'].lower():
                target_bot = bot
                break
        
        if not target_bot:
            print(f"❌ Bot '{bot_name}' not found!")
            available = [bot['name'] for bot in bots]
            print(f"Available bots: {', '.join(available)}")
            return None
        
        return self.compile_bot(target_bot)


if __name__ == "__main__":
    compiler = ChessChallengeBotCompiler()
    
    # Start with a simple test - compile BongcloudEnthusiast (307 ELO)
    print("🚀 Starting with BongcloudEnthusiast (307 ELO) as test...")
    test_result = compiler.test_single_bot("BongcloudEnthusiast")
    
    if test_result:
        print(f"\n🎉 Test compilation successful!")
        print(f"Next step: Test V7P3R v7.0 vs {test_result.name}")
    else:
        print("\n❌ Test compilation failed. Need to debug the compilation process.")
