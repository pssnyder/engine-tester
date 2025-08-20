#!/usr/bin/env python3
"""
Chess Game Analysis Visualizer
Creates visualizations from enhanced game analysis data.
"""
import json
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set(style="whitegrid")

class ChessVisualizer:
    def __init__(self, results_dir="results", output_dir="visual_reports"):
        """Initialize the visualizer with paths."""
        self.results_dir = results_dir
        self.vis_dir = os.path.join(results_dir, output_dir)
        os.makedirs(self.vis_dir, exist_ok=True)
        
        # Load data
        print("Loading analysis data...")
        self.load_data()

    def load_data(self):
        """Load analysis results from JSON files."""
        try:
            with open(os.path.join(self.results_dir, "piece_heatmaps.json")) as f:
                self.heatmaps = json.load(f)
        except FileNotFoundError:
            print("Warning: piece_heatmaps.json not found!")
            self.heatmaps = {}
            
        try:
            with open(os.path.join(self.results_dir, "player_stats.json")) as f:
                self.player_stats = json.load(f)
        except FileNotFoundError:
            print("Warning: player_stats.json not found!")
            self.player_stats = {}
            
        try:
            with open(os.path.join(self.results_dir, "analysis_summary.json")) as f:
                self.summary = json.load(f)
        except FileNotFoundError:
            print("Warning: analysis_summary.json not found!")
            self.summary = {}

    def create_piece_heatmaps(self):
        """Generate heatmaps for all pieces' movement patterns."""
        print("Generating piece heatmaps...")
        for piece_symbol in self.heatmaps.keys():
            piece_data = self.heatmaps[piece_symbol]
            
            # Create 8x8 matrix for the board
            matrix = np.zeros((8, 8))
            
            # Fill matrix with frequency data
            for square, data in piece_data.items():
                if len(square) == 2:  # Valid chess square (e.g., "e4")
                    try:
                        file_idx = ord(square[0]) - ord('a')
                        rank_idx = int(square[1]) - 1
                        if 0 <= file_idx < 8 and 0 <= rank_idx < 8:
                            matrix[7-rank_idx][file_idx] = data["frequency"]
                    except (IndexError, ValueError):
                        continue
            
            plt.figure(figsize=(10, 8))
            ax = sns.heatmap(matrix, cmap='YlOrRd', square=True)
            
            # Customize the heatmap
            plt.title(f'{piece_symbol} Movement Patterns', fontsize=16)
            ax.set_xticks(np.arange(8) + 0.5)
            ax.set_yticks(np.arange(8) + 0.5)
            ax.set_xticklabels(list('abcdefgh'))
            ax.set_yticklabels(['8', '7', '6', '5', '4', '3', '2', '1'])
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.vis_dir, f'heatmap_{piece_symbol}.png'), dpi=300)
            plt.close()

    def create_timing_distribution(self):
        """Generate overall move timing distribution."""
        print("Generating timing distribution...")
        all_times = []
        
        for piece_symbol, piece_data in self.heatmaps.items():
            for square_data in piece_data.values():
                times = square_data["timing"]["times_list"]
                if times:  # Only add if we have timing data
                    all_times.extend(times)
        
        if all_times:
            plt.figure(figsize=(12, 6))
            sns.histplot(all_times, bins=50, kde=True)
            plt.title('Move Timing Distribution', fontsize=14)
            plt.xlabel('Time (seconds)', fontsize=12)
            plt.ylabel('Frequency', fontsize=12)
            
            # Add median and mean lines
            if len(all_times) > 0:
                median_time = float(np.median(all_times))
                mean_time = float(np.mean(all_times))
                plt.axvline(median_time, color='r', linestyle='--', label=f'Median: {median_time:.1f}s')
                plt.axvline(mean_time, color='g', linestyle='--', label=f'Mean: {mean_time:.1f}s')
                plt.legend()
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.vis_dir, 'timing_distribution.png'), dpi=300)
            plt.close()

    def create_phase_distribution_charts(self):
        """Generate phase distribution charts for each piece."""
        print("Generating phase distribution charts...")
        piece_phases = {}
        
        for piece_symbol, piece_data in self.heatmaps.items():
            phases = {"Opening": 0, "Middlegame": 0, "Endgame": 0}
            
            for square_data in piece_data.values():
                phase_dist = square_data["phase_distribution"]
                phases["Opening"] += phase_dist["opening"]
                phases["Middlegame"] += phase_dist["middlegame"]
                phases["Endgame"] += phase_dist["endgame"]
            
            piece_phases[piece_symbol] = phases
        
        # Create a single figure with multiple subplots
        piece_symbols = list(piece_phases.keys())
        if len(piece_symbols) > 0:
            # Calculate grid dimensions
            n = len(piece_symbols)
            cols = 3
            rows = (n + cols - 1) // cols
            
            fig = plt.figure(figsize=(15, 4 * rows))
            for i, piece in enumerate(piece_symbols):
                phases = piece_phases[piece]
                if sum(phases.values()) > 0:
                    ax = fig.add_subplot(rows, cols, i + 1)
                    ax.pie(phases.values(), labels=phases.keys(), autopct='%1.1f%%',
                          explode=(0.05, 0.05, 0.05), colors=['#3498db', '#2ecc71', '#e74c3c'])
                    ax.set_title(f'{piece} Usage by Game Phase')
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.vis_dir, 'phase_distribution.png'), dpi=300)
            plt.close()

    def create_performance_summary(self):
        """Generate overall performance visualization."""
        print("Generating performance summary...")
        if not self.player_stats:
            print("No player stats data available for performance summary")
            return
            
        # Create figure with multiple subplots
        fig = plt.figure(figsize=(15, 10))
        
        # Check if we have the required data
        if all(key in self.player_stats for key in ["wins", "losses", "draws"]):
            # Overall results pie chart
            ax1 = plt.subplot(2, 2, 1)
            results = [
                self.player_stats["wins"],
                self.player_stats["losses"],
                self.player_stats["draws"]
            ]
            labels = ['Wins', 'Losses', 'Draws']
            colors = ['#2ecc71', '#e74c3c', '#f1c40f']
            ax1.pie(results, labels=labels, colors=colors, autopct='%1.1f%%',
                    explode=(0.05, 0.05, 0.05))
            ax1.set_title('Overall Results', fontsize=14)
        
        # Performance by color
        if "performance_by_color" in self.player_stats:
            ax2 = plt.subplot(2, 2, 2)
            color_stats = self.player_stats["performance_by_color"]
            colors = ['white', 'black']
            
            wins = [color_stats[c]["wins"] for c in colors]
            draws = [color_stats[c]["draws"] for c in colors]
            losses = [color_stats[c]["losses"] for c in colors]
            
            x = np.arange(len(colors))
            width = 0.25
            
            ax2.bar(x - width, wins, width, label='Wins', color='#2ecc71')
            ax2.bar(x, draws, width, label='Draws', color='#f1c40f')
            ax2.bar(x + width, losses, width, label='Losses', color='#e74c3c')
            
            ax2.set_xticks(x)
            ax2.set_xticklabels(['White', 'Black'])
            ax2.set_title('Performance by Color', fontsize=14)
            ax2.legend()
        
        # Top openings
        if "favorite_openings" in self.player_stats:
            ax3 = plt.subplot(2, 1, 2)
            openings = list(self.player_stats["favorite_openings"].items())
            openings.sort(key=lambda x: x[1], reverse=True)
            top_openings = openings[:10]
            
            y_pos = np.arange(len(top_openings))
            counts = [count for _, count in top_openings]
            
            ax3.barh(y_pos, counts, color='#3498db')
            ax3.set_yticks(y_pos)
            ax3.set_yticklabels([name for name, _ in top_openings])
            ax3.set_title('Most Played Openings', fontsize=14)
            ax3.set_xlabel('Number of Games', fontsize=12)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.vis_dir, 'performance_summary.png'), dpi=300)
        plt.close()

    def create_all_visualizations(self):
        """Generate all visualizations."""
        self.create_piece_heatmaps()
        self.create_timing_distribution()
        self.create_phase_distribution_charts()
        self.create_performance_summary()
        
        print(f"\nVisualizations saved to: {self.vis_dir}")

def main():
    visualizer = ChessVisualizer()
    visualizer.create_all_visualizations()

if __name__ == "__main__":
    main()
