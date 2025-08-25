#!/usr/bin/env python3
"""
📊 Terminal Dashboard for Engine Battle Framework
===============================================

Real-time monitoring and status display for ongoing engine battles.
Features progress bars, live statistics, and session overview.
"""

import os
import sys
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Try to import colorama for colored output (optional)
try:
    import colorama
    from colorama import Fore, Back, Style
    colorama.init()
    COLORS_AVAILABLE = True
except ImportError:
    # Fallback if colorama not available
    COLORS_AVAILABLE = False
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""
    class Back:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""
    class Style:
        BRIGHT = DIM = RESET_ALL = ""

@dataclass
class DashboardConfig:
    """Configuration for the dashboard display"""
    refresh_rate: float = 1.0  # seconds
    max_recent_results: int = 10
    show_detailed_metrics: bool = True
    show_progress_bars: bool = True
    compact_mode: bool = False
    auto_scroll: bool = True

class TerminalDashboard:
    """Real-time terminal dashboard for engine battles"""
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        self.config = config or DashboardConfig()
        self.running = False
        self.session_data = {}
        self.recent_results = []
        self.current_challenge = None
        self.start_time = None
        self.lock = threading.Lock()
        
        # Terminal dimensions
        self.update_terminal_size()
        
    def update_terminal_size(self):
        """Update terminal dimensions"""
        try:
            size = os.get_terminal_size()
            self.term_width = size.columns
            self.term_height = size.lines
        except:
            self.term_width = 80
            self.term_height = 24
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def move_cursor(self, row: int, col: int = 0):
        """Move cursor to specific position"""
        print(f"\033[{row};{col}H", end="")
    
    def hide_cursor(self):
        """Hide the cursor"""
        print("\033[?25l", end="")
    
    def show_cursor(self):
        """Show the cursor"""
        print("\033[?25h", end="")
    
    def create_progress_bar(self, progress: float, width: int = 30, 
                          completed_char: str = "█", incomplete_char: str = "░") -> str:
        """Create a visual progress bar"""
        if not self.config.show_progress_bars:
            return f"{progress:.1%}"
        
        filled = int(width * progress)
        bar = completed_char * filled + incomplete_char * (width - filled)
        return f"[{Fore.GREEN}{bar}{Fore.RESET}] {progress:.1%}"
    
    def format_time(self, seconds: float) -> str:
        """Format time duration"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.0f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def format_number(self, num: int) -> str:
        """Format large numbers with K/M suffixes"""
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        else:
            return str(num)
    
    def render_header(self) -> List[str]:
        """Render the dashboard header"""
        lines = []
        
        # Title
        title = "🎯 ENGINE BATTLE FRAMEWORK - LIVE DASHBOARD"
        padding = (self.term_width - len(title)) // 2
        lines.append(f"{Fore.CYAN}{Style.BRIGHT}{' ' * padding}{title}{Style.RESET_ALL}")
        
        # Current time and session info
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.start_time:
            elapsed = self.format_time(time.time() - self.start_time)
            session_info = f"Session Time: {elapsed}"
        else:
            session_info = "Session: Not Started"
        
        time_line = f"{Fore.WHITE}Time: {current_time}  |  {session_info}{Fore.RESET}"
        lines.append(time_line)
        
        # Separator
        lines.append(f"{Fore.BLUE}{'=' * self.term_width}{Fore.RESET}")
        
        return lines
    
    def render_current_challenge(self) -> List[str]:
        """Render current challenge information"""
        lines = []
        
        if not self.current_challenge:
            lines.append(f"{Fore.YELLOW}📋 No active challenge{Fore.RESET}")
            return lines
        
        challenge = self.current_challenge
        lines.append(f"{Fore.GREEN}{Style.BRIGHT}🎯 ACTIVE CHALLENGE{Style.RESET_ALL}")
        lines.append(f"  Type: {challenge.get('type', 'Unknown')}")
        lines.append(f"  Engines: {challenge.get('engine1', '?')} vs {challenge.get('engine2', '?')}")
        
        if 'progress' in challenge:
            progress_bar = self.create_progress_bar(challenge['progress'])
            lines.append(f"  Progress: {progress_bar}")
        
        if 'estimated_time' in challenge:
            est_time = self.format_time(challenge['estimated_time'])
            lines.append(f"  Estimated Time: {est_time}")
        
        if 'current_step' in challenge:
            lines.append(f"  Current: {challenge['current_step']}")
        
        return lines
    
    def render_session_summary(self) -> List[str]:
        """Render session summary statistics"""
        lines = []
        
        if not self.session_data:
            lines.append(f"{Fore.CYAN}📊 Session Summary: No data available{Fore.RESET}")
            return lines
        
        lines.append(f"{Fore.CYAN}{Style.BRIGHT}📊 SESSION SUMMARY{Style.RESET_ALL}")
        
        # Basic stats
        total_challenges = self.session_data.get('total_challenges', 0)
        completed = self.session_data.get('completed_challenges', 0)
        failed = self.session_data.get('failed_challenges', 0)
        
        lines.append(f"  Total Challenges: {total_challenges}")
        lines.append(f"  Completed: {Fore.GREEN}{completed}{Fore.RESET}")
        lines.append(f"  Failed: {Fore.RED}{failed}{Fore.RESET}")
        
        if total_challenges > 0:
            success_rate = completed / total_challenges
            success_bar = self.create_progress_bar(success_rate, width=20)
            lines.append(f"  Success Rate: {success_bar}")
        
        # Engine performance
        if 'engine_stats' in self.session_data:
            lines.append("")
            lines.append(f"  {Style.BRIGHT}Engine Performance:{Style.RESET_ALL}")
            for engine, stats in self.session_data['engine_stats'].items():
                wins = stats.get('wins', 0)
                total = stats.get('total_games', 0)
                if total > 0:
                    win_rate = wins / total
                    win_bar = self.create_progress_bar(win_rate, width=15)
                    lines.append(f"    {engine}: {wins}/{total} {win_bar}")
        
        return lines
    
    def render_recent_results(self) -> List[str]:
        """Render recent challenge results"""
        lines = []
        
        if not self.recent_results:
            lines.append(f"{Fore.YELLOW}🕐 No recent results{Fore.RESET}")
            return lines
        
        lines.append(f"{Fore.MAGENTA}{Style.BRIGHT}🕐 RECENT RESULTS{Style.RESET_ALL}")
        
        max_results = min(self.config.max_recent_results, len(self.recent_results))
        for i, result in enumerate(self.recent_results[-max_results:]):
            status_icon = "✅" if result.get('status') == 'completed' else "❌"
            winner = result.get('winner', 'Draw')
            challenge_type = result.get('challenge_type', 'Unknown')
            exec_time = self.format_time(result.get('execution_time', 0))
            
            timestamp = result.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_ago = datetime.now() - dt
                    if time_ago.total_seconds() < 60:
                        time_str = "Just now"
                    elif time_ago.total_seconds() < 3600:
                        time_str = f"{int(time_ago.total_seconds() // 60)}m ago"
                    else:
                        time_str = f"{int(time_ago.total_seconds() // 3600)}h ago"
                except:
                    time_str = "Unknown"
            else:
                time_str = "Unknown"
            
            result_line = f"  {status_icon} {challenge_type} | Winner: {winner} | {exec_time} | {time_str}"
            if len(result_line) > self.term_width - 2:
                result_line = result_line[:self.term_width - 5] + "..."
            
            lines.append(result_line)
        
        return lines
    
    def render_detailed_metrics(self) -> List[str]:
        """Render detailed performance metrics"""
        lines = []
        
        if not self.config.show_detailed_metrics or not self.session_data.get('detailed_metrics'):
            return lines
        
        lines.append(f"{Fore.BLUE}{Style.BRIGHT}📈 DETAILED METRICS{Style.RESET_ALL}")
        
        metrics = self.session_data.get('detailed_metrics', {})
        
        # Performance metrics
        if 'average_challenge_time' in metrics:
            avg_time = self.format_time(metrics['average_challenge_time'])
            lines.append(f"  Avg Challenge Time: {avg_time}")
        
        if 'total_nodes_analyzed' in metrics:
            total_nodes = self.format_number(metrics['total_nodes_analyzed'])
            lines.append(f"  Total Nodes: {total_nodes}")
        
        if 'average_depth' in metrics:
            avg_depth = metrics['average_depth']
            lines.append(f"  Avg Search Depth: {avg_depth:.1f}")
        
        # Challenge type breakdown
        if 'challenge_type_stats' in metrics:
            lines.append("")
            lines.append(f"  {Style.BRIGHT}Challenge Types:{Style.RESET_ALL}")
            for challenge_type, count in metrics['challenge_type_stats'].items():
                lines.append(f"    {challenge_type}: {count}")
        
        return lines
    
    def render_footer(self) -> List[str]:
        """Render dashboard footer"""
        lines = []
        
        # Controls and status
        controls = "Press 'q' to quit | 'r' to refresh | 'c' to clear"
        lines.append(f"{Fore.WHITE}{Style.DIM}{controls}{Style.RESET_ALL}")
        
        # Resource usage (if available)
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            mem_percent = memory.percent
            
            resource_info = f"CPU: {cpu_percent:.1f}% | Memory: {mem_percent:.1f}%"
            lines.append(f"{Fore.WHITE}{Style.DIM}{resource_info}{Style.RESET_ALL}")
        except ImportError:
            pass
        
        return lines
    
    def render_dashboard(self):
        """Render the complete dashboard"""
        self.update_terminal_size()
        
        all_lines = []
        
        # Collect all sections
        all_lines.extend(self.render_header())
        all_lines.append("")  # Spacer
        all_lines.extend(self.render_current_challenge())
        all_lines.append("")  # Spacer
        all_lines.extend(self.render_session_summary())
        all_lines.append("")  # Spacer
        all_lines.extend(self.render_recent_results())
        
        if self.config.show_detailed_metrics:
            all_lines.append("")  # Spacer
            all_lines.extend(self.render_detailed_metrics())
        
        # Calculate footer position
        footer_lines = self.render_footer()
        
        # Clear screen and render
        self.clear_screen()
        self.hide_cursor()
        
        # Render main content
        for i, line in enumerate(all_lines):
            if i >= self.term_height - len(footer_lines) - 1:
                break
            print(line[:self.term_width])
        
        # Render footer at bottom
        footer_start = self.term_height - len(footer_lines)
        for i, line in enumerate(footer_lines):
            self.move_cursor(footer_start + i)
            print(line[:self.term_width])
        
        # Reset cursor
        self.move_cursor(self.term_height)
        sys.stdout.flush()
    
    def update_session_data(self, data: Dict[str, Any]):
        """Update session data thread-safely"""
        with self.lock:
            self.session_data.update(data)
    
    def update_current_challenge(self, challenge_data: Optional[Dict[str, Any]]):
        """Update current challenge information"""
        with self.lock:
            self.current_challenge = challenge_data
    
    def add_result(self, result: Dict[str, Any]):
        """Add a new result to recent results"""
        with self.lock:
            self.recent_results.append(result)
            # Keep only the most recent results
            if len(self.recent_results) > self.config.max_recent_results * 2:
                self.recent_results = self.recent_results[-self.config.max_recent_results:]
    
    def start(self):
        """Start the dashboard"""
        self.running = True
        self.start_time = time.time()
        
        print(f"{Fore.GREEN}🚀 Starting Engine Battle Dashboard...{Fore.RESET}")
        time.sleep(1)
        
        try:
            while self.running:
                self.render_dashboard()
                time.sleep(self.config.refresh_rate)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def stop(self):
        """Stop the dashboard"""
        self.running = False
        self.show_cursor()
        self.clear_screen()
        print(f"{Fore.CYAN}📊 Dashboard stopped. Thanks for using Engine Battle Framework!{Fore.RESET}")

class DashboardManager:
    """Manager for coordinating dashboard with battle framework"""
    
    def __init__(self, dashboard: TerminalDashboard):
        self.dashboard = dashboard
        self.dashboard_thread = None
    
    def start_dashboard(self):
        """Start dashboard in separate thread"""
        if self.dashboard_thread and self.dashboard_thread.is_alive():
            return
        
        self.dashboard_thread = threading.Thread(target=self.dashboard.start, daemon=True)
        self.dashboard_thread.start()
    
    def stop_dashboard(self):
        """Stop the dashboard"""
        if self.dashboard:
            self.dashboard.stop()
        if self.dashboard_thread:
            self.dashboard_thread.join(timeout=2)
    
    def update_challenge_progress(self, challenge_type: str, engine1: str, engine2: str, 
                                progress: float, current_step: Optional[str] = None):
        """Update current challenge progress"""
        challenge_data = {
            'type': challenge_type,
            'engine1': engine1,
            'engine2': engine2,
            'progress': progress,
            'current_step': current_step
        }
        self.dashboard.update_current_challenge(challenge_data)
    
    def report_challenge_complete(self, result: Dict[str, Any]):
        """Report completed challenge"""
        self.dashboard.add_result(result)
        self.dashboard.update_current_challenge(None)  # Clear current challenge
    
    def update_session_stats(self, stats: Dict[str, Any]):
        """Update session statistics"""
        self.dashboard.update_session_data(stats)

# Example usage and testing
if __name__ == "__main__":
    import random
    import argparse
    
    parser = argparse.ArgumentParser(description="Engine Battle Dashboard Demo")
    parser.add_argument("--demo", action="store_true", help="Run demo mode with fake data")
    parser.add_argument("--compact", action="store_true", help="Use compact display mode")
    parser.add_argument("--no-colors", action="store_true", help="Disable colored output")
    args = parser.parse_args()
    
    # Configure dashboard
    config = DashboardConfig(
        compact_mode=args.compact,
        refresh_rate=0.5 if args.demo else 1.0
    )
    
    dashboard = TerminalDashboard(config)
    
    if args.demo:
        # Demo mode with simulated data
        print("🎮 Starting demo mode...")
        
        # Simulate session data
        dashboard.update_session_data({
            'total_challenges': 15,
            'completed_challenges': 12,
            'failed_challenges': 3,
            'engine_stats': {
                'V7P3R': {'wins': 7, 'total_games': 10},
                'SlowMate': {'wins': 3, 'total_games': 10},
                'C0BR4': {'wins': 2, 'total_games': 5}
            },
            'detailed_metrics': {
                'average_challenge_time': 45.2,
                'total_nodes_analyzed': 2_547_891,
                'average_depth': 12.4,
                'challenge_type_stats': {
                    'traditional_game': 8,
                    'speed_challenge': 4,
                    'puzzle_solve': 2,
                    'depth_challenge': 1
                }
            }
        })
        
        # Add some demo results
        for i in range(8):
            result = {
                'status': 'completed' if random.random() > 0.2 else 'failed',
                'winner': random.choice(['V7P3R', 'SlowMate', 'Draw']),
                'challenge_type': random.choice(['speed', 'traditional', 'puzzle', 'depth']),
                'execution_time': random.uniform(10, 120),
                'timestamp': (datetime.now() - timedelta(minutes=random.randint(1, 180))).isoformat()
            }
            dashboard.add_result(result)
        
        # Simulate current challenge
        dashboard.update_current_challenge({
            'type': 'Speed Challenge',
            'engine1': 'V7P3R',
            'engine2': 'SlowMate',
            'progress': 0.65,
            'current_step': 'Game 3 of 5',
            'estimated_time': 25.0
        })
        
        dashboard.start()
    else:
        # Normal mode - wait for external updates
        dashboard.start()
