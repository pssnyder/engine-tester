#!/usr/bin/env python3
"""
Chess Analytics Dashboard Generator - Fixed Version
Creates an interactive HTML dashboard with visualizations and data insights.
"""
import json
import os
import numpy as np
import pandas as pd
import base64
from pathlib import Path
from io import BytesIO
from datetime import datetime

class ChessDashboardGenerator:
    def __init__(self, results_dir="results", vis_dir="visual_reports", output_file="chess_dashboard.html"):
        """Initialize the dashboard generator."""
        self.results_dir = results_dir
        self.vis_dir = os.path.join(results_dir, vis_dir)
        self.output_file = os.path.join(results_dir, output_file)
        self.data = {}
        
        # Load data
        print("Loading analysis data...")
        self.load_data()

    def load_data(self):
        """Load all available analysis data."""
        data_files = {
            "piece_heatmaps": "piece_heatmaps.json",
            "player_stats": "player_stats.json",
            "analysis_summary": "analysis_summary.json"
        }
        
        for key, filename in data_files.items():
            try:
                with open(os.path.join(self.results_dir, filename), encoding='utf-8') as f:
                    self.data[key] = json.load(f)
                    print(f"Loaded {filename}")
            except FileNotFoundError:
                print(f"Warning: {filename} not found!")
                self.data[key] = {}
            except json.JSONDecodeError:
                print(f"Error: {filename} has invalid JSON format!")
                self.data[key] = {}

    def image_to_base64(self, image_path):
        """Convert an image file to base64 for embedding in HTML."""
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
                return f"data:image/png;base64,{encoded_string}"
        except FileNotFoundError:
            print(f"Warning: Image not found at {image_path}")
            return ""
        except Exception as e:
            print(f"Error encoding image {image_path}: {str(e)}")
            return ""

    def create_piece_stats_tables(self):
        """Create HTML tables with piece movement statistics."""
        html = ""
        
        if "piece_heatmaps" in self.data and self.data["piece_heatmaps"]:
            for piece, squares in self.data["piece_heatmaps"].items():
                # Gather statistics
                total_moves = sum(data["frequency"] for data in squares.values())
                
                # Find top squares
                top_squares = sorted(
                    [(sq, data["frequency"]) for sq, data in squares.items()],
                    key=lambda x: x[1], 
                    reverse=True
                )[:10]
                
                # Create HTML table for this piece
                html += f"""
                <div class="card mb-4">
                    <div class="card-header">
                        <h3 class="card-title">{piece} Movement Statistics</h3>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h4>Top 10 Target Squares</h4>
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>Square</th>
                                            <th>Frequency</th>
                                            <th>Percentage</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                """
                
                for square, freq in top_squares:
                    percentage = (freq / total_moves) * 100 if total_moves > 0 else 0
                    html += f"""
                                        <tr>
                                            <td>{square}</td>
                                            <td>{freq}</td>
                                            <td>{percentage:.1f}%</td>
                                        </tr>
                    """
                
                html += """
                                    </tbody>
                                </table>
                            </div>
                            <div class="col-md-6">
                                <h4>Phase Distribution</h4>
                                <canvas id="phaseChart{piece}" width="400" height="300"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                """.replace("{piece}", piece)
        
        return html

    def generate_phase_chart_scripts(self):
        """Generate JavaScript for phase distribution charts."""
        scripts = []
        
        if "piece_heatmaps" in self.data and self.data["piece_heatmaps"]:
            for piece, squares in self.data["piece_heatmaps"].items():
                # Calculate phase totals
                phases = {"Opening": 0, "Middlegame": 0, "Endgame": 0}
                
                for square, data in squares.items():
                    if "phase_distribution" in data:
                        phase_dist = data["phase_distribution"]
                        phases["Opening"] += phase_dist.get("opening", 0)
                        phases["Middlegame"] += phase_dist.get("middlegame", 0)
                        phases["Endgame"] += phase_dist.get("endgame", 0)
                
                # Create chart script
                script = f"""
                (function() {{
                    var ctx = document.getElementById('phaseChart{piece}');
                    if (ctx) {{
                        var phaseChart{piece} = new Chart(ctx, {{
                            type: 'pie',
                            data: {{
                                labels: ['Opening', 'Middlegame', 'Endgame'],
                                datasets: [{{
                                    data: [{phases['Opening']}, {phases['Middlegame']}, {phases['Endgame']}],
                                    backgroundColor: ['#3498db', '#2ecc71', '#e74c3c']
                                }}]
                            }},
                            options: {{
                                responsive: true,
                                plugins: {{
                                    legend: {{
                                        position: 'bottom',
                                    }},
                                    title: {{
                                        display: true,
                                        text: '{piece} Usage by Game Phase'
                                    }}
                                }}
                            }}
                        }});
                    }}
                }})();
                """
                scripts.append(script)
        
        return "\n".join(scripts)

    def create_performance_stats(self):
        """Create HTML with performance statistics."""
        html = ""
        
        if "player_stats" in self.data and self.data["player_stats"]:
            stats = self.data["player_stats"]
            
            total_games = stats.get("total_games", 0)
            wins = stats.get("wins", 0)
            losses = stats.get("losses", 0)
            draws = stats.get("draws", 0)
            
            win_rate = (wins / total_games * 100) if total_games > 0 else 0
            
            html += f"""
            <div class="card mb-4">
                <div class="card-header">
                    <h3 class="card-title">Performance Overview</h3>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4">
                            <div class="stats-card text-center p-3 border rounded">
                                <h3>{total_games}</h3>
                                <p>Total Games</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="stats-card text-center p-3 border rounded">
                                <h3>{win_rate:.1f}%</h3>
                                <p>Win Rate</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="stats-card text-center p-3 border rounded">
                                <h3>{stats.get("avg_game_length", 0):.1f}</h3>
                                <p>Avg. Game Length</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row mt-4">
                        <div class="col-md-6">
                            <h4>Results Distribution</h4>
                            <canvas id="resultsChart" width="400" height="300"></canvas>
                        </div>
                        <div class="col-md-6">
                            <h4>Performance by Color</h4>
                            <canvas id="colorChart" width="400" height="300"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            """
        
        return html

    def generate_performance_scripts(self):
        """Generate JavaScript for performance charts."""
        scripts = []
        
        if "player_stats" in self.data and self.data["player_stats"]:
            stats = self.data["player_stats"]
            
            # Results pie chart
            results_script = f"""
            (function() {{
                var resultsCtx = document.getElementById('resultsChart');
                if (resultsCtx) {{
                    var resultsChart = new Chart(resultsCtx, {{
                        type: 'pie',
                        data: {{
                            labels: ['Wins', 'Losses', 'Draws'],
                            datasets: [{{
                                data: [{stats.get('wins', 0)}, {stats.get('losses', 0)}, {stats.get('draws', 0)}],
                                backgroundColor: ['#2ecc71', '#e74c3c', '#f1c40f']
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            plugins: {{
                                legend: {{
                                    position: 'bottom',
                                }}
                            }}
                        }}
                    }});
                }}
            }})();
            """
            scripts.append(results_script)
            
            # Color performance chart
            if "performance_by_color" in stats:
                color_stats = stats["performance_by_color"]
                white_wins = color_stats.get("white", {}).get("wins", 0)
                white_losses = color_stats.get("white", {}).get("losses", 0)
                white_draws = color_stats.get("white", {}).get("draws", 0)
                
                black_wins = color_stats.get("black", {}).get("wins", 0)
                black_losses = color_stats.get("black", {}).get("losses", 0)
                black_draws = color_stats.get("black", {}).get("draws", 0)
                
                color_script = f"""
                (function() {{
                    var colorCtx = document.getElementById('colorChart');
                    if (colorCtx) {{
                        var colorChart = new Chart(colorCtx, {{
                            type: 'bar',
                            data: {{
                                labels: ['White', 'Black'],
                                datasets: [
                                    {{
                                        label: 'Wins',
                                        data: [{white_wins}, {black_wins}],
                                        backgroundColor: '#2ecc71'
                                    }},
                                    {{
                                        label: 'Draws',
                                        data: [{white_draws}, {black_draws}],
                                        backgroundColor: '#f1c40f'
                                    }},
                                    {{
                                        label: 'Losses',
                                        data: [{white_losses}, {black_losses}],
                                        backgroundColor: '#e74c3c'
                                    }}
                                ]
                            }},
                            options: {{
                                responsive: true,
                                scales: {{
                                    x: {{
                                        stacked: true,
                                    }},
                                    y: {{
                                        stacked: true
                                    }}
                                }}
                            }}
                        }});
                    }}
                }})();
                """
                scripts.append(color_script)
            
            # Favorite openings chart
            if "favorite_openings" in stats:
                openings = list(stats["favorite_openings"].items())
                openings.sort(key=lambda x: x[1], reverse=True)
                top_openings = openings[:7]  # Take top 7
                
                opening_labels = [f'"{name}"' for name, _ in top_openings]
                opening_data = [count for _, count in top_openings]
                
                opening_script = f"""
                (function() {{
                    var openingCtx = document.getElementById('openingChart');
                    if (openingCtx) {{
                        var openingChart = new Chart(openingCtx, {{
                            type: 'bar',
                            data: {{
                                labels: [{', '.join(opening_labels)}],
                                datasets: [{{
                                    label: 'Games',
                                    data: [{', '.join(map(str, opening_data))}],
                                    backgroundColor: '#3498db'
                                }}]
                            }},
                            options: {{
                                responsive: true,
                                indexAxis: 'y',
                                plugins: {{
                                    title: {{
                                        display: true,
                                        text: 'Most Common Openings'
                                    }}
                                }}
                            }}
                        }});
                    }}
                }})();
                """
                scripts.append(opening_script)
        
        return "\n".join(scripts)

    def create_openings_section(self):
        """Create HTML section for openings analysis."""
        html = ""
        
        if "player_stats" in self.data and "favorite_openings" in self.data["player_stats"]:
            html += """
            <div class="card mb-4">
                <div class="card-header">
                    <h3 class="card-title">Opening Preferences</h3>
                </div>
                <div class="card-body">
                    <canvas id="openingChart" width="800" height="400"></canvas>
                </div>
            </div>
            """
        
        return html

    def create_visualization_section(self):
        """Create HTML section with embedded visualizations."""
        html = "<div class='row'>"
        
        # Find all PNG files in the visualization directory
        vis_files = {}
        if os.path.exists(self.vis_dir):
            for file in os.listdir(self.vis_dir):
                if file.endswith('.png'):
                    # Group files by type
                    if file.startswith('heatmap_'):
                        category = 'heatmap'
                        piece = file.split('_')[1].split('.')[0]
                        vis_files.setdefault(category, {})[piece] = file
                    else:
                        category = file.split('.')[0]
                        vis_files[category] = file
        
        # Piece heatmaps in a tabbed interface
        if 'heatmap' in vis_files:
            html += """
            <div class="col-12 mb-4">
                <div class="card">
                    <div class="card-header">
                        <h3>Piece Movement Heatmaps</h3>
                    </div>
                    <div class="card-body">
                        <ul class="nav nav-tabs" id="heatmapTabs" role="tablist">
            """
            
            # Create tabs
            first = True
            for piece in vis_files['heatmap']:
                active = 'active' if first else ''
                selected = 'true' if first else 'false'
                first = False
                
                html += f"""
                            <li class="nav-item" role="presentation">
                                <button class="nav-link {active}" id="tab-{piece}" data-bs-toggle="tab" 
                                    data-bs-target="#content-{piece}" type="button" role="tab" 
                                    aria-controls="content-{piece}" aria-selected="{selected}">
                                    {piece}
                                </button>
                            </li>
                """
            
            html += """
                        </ul>
                        <div class="tab-content" id="heatmapTabsContent">
            """
            
            # Create tab content
            first = True
            for piece, filename in vis_files['heatmap'].items():
                active = 'show active' if first else ''
                first = False
                
                image_path = os.path.join(self.vis_dir, filename)
                image_data = self.image_to_base64(image_path)
                
                html += f"""
                            <div class="tab-pane fade {active}" id="content-{piece}" role="tabpanel" aria-labelledby="tab-{piece}">
                                <div class="text-center mt-3">
                                    <img src="{image_data}" class="img-fluid" alt="Heatmap for {piece}">
                                </div>
                            </div>
                """
            
            html += """
                        </div>
                    </div>
                </div>
            </div>
            """
        
        # Other visualizations as cards
        for category, file in vis_files.items():
            if category == 'heatmap':
                continue
                
            if isinstance(file, str):
                image_path = os.path.join(self.vis_dir, file)
                image_data = self.image_to_base64(image_path)
                
                # Convert snake_case to Title Case for display
                title = ' '.join(word.capitalize() for word in category.split('_'))
                
                html += f"""
                <div class="col-md-6 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h3>{title}</h3>
                        </div>
                        <div class="card-body text-center">
                            <img src="{image_data}" class="img-fluid" alt="{title}">
                        </div>
                    </div>
                </div>
                """
        
        html += "</div>"
        return html

    def create_additional_insights(self):
        """Create HTML with additional data insights."""
        html = ""
        
        # Calculate piece usage stats
        if "piece_heatmaps" in self.data and self.data["piece_heatmaps"]:
            piece_moves = {}
            for piece, squares in self.data["piece_heatmaps"].items():
                total = sum(data["frequency"] for data in squares.values())
                piece_moves[piece] = total
            
            total_moves = sum(piece_moves.values())
            
            html += """
            <div class="card mb-4">
                <div class="card-header">
                    <h3 class="card-title">Piece Usage Analysis</h3>
                </div>
                <div class="card-body">
                    <canvas id="pieceUsageChart" width="400" height="300"></canvas>
                    <div class="mt-4">
                        <h4>Key Insights</h4>
                        <ul>
            """
            
            # Add some insights based on piece usage
            sorted_pieces = sorted(piece_moves.items(), key=lambda x: x[1], reverse=True)
            most_used = sorted_pieces[0][0]
            least_used = sorted_pieces[-1][0]
            
            html += f"""
                            <li>Your most frequently moved piece is <strong>{most_used}</strong> ({piece_moves[most_used]} moves, {piece_moves[most_used]/total_moves*100:.1f}% of all moves)</li>
                            <li>Your least frequently moved piece is <strong>{least_used}</strong> ({piece_moves[least_used]} moves, {piece_moves[least_used]/total_moves*100:.1f}% of all moves)</li>
            """
            
            # Check piece balance (knights vs bishops)
            if 'N' in piece_moves and 'B' in piece_moves:
                n_moves = piece_moves['N']
                b_moves = piece_moves['B']
                if n_moves > b_moves * 1.3:
                    html += f"<li>You strongly prefer knights over bishops (ratio {n_moves/b_moves:.1f}:1)</li>"
                elif b_moves > n_moves * 1.3:
                    html += f"<li>You strongly prefer bishops over knights (ratio {b_moves/n_moves:.1f}:1)</li>"
            
            html += """
                        </ul>
                    </div>
                </div>
            </div>
            """
        
        return html

    def generate_piece_usage_script(self):
        """Generate JavaScript for piece usage chart."""
        script = ""
        
        if "piece_heatmaps" in self.data and self.data["piece_heatmaps"]:
            piece_moves = {}
            for piece, squares in self.data["piece_heatmaps"].items():
                total = sum(data["frequency"] for data in squares.values())
                piece_moves[piece] = total
            
            # Define colors for pieces
            colors = {
                'P': '#3498db',  # Pawns - Blue
                'N': '#2ecc71',  # Knights - Green
                'B': '#9b59b6',  # Bishops - Purple
                'R': '#e74c3c',  # Rooks - Red
                'Q': '#f1c40f',  # Queen - Yellow
                'K': '#34495e',  # King - Dark Blue
                'p': '#2980b9',  # Black Pawns
                'n': '#27ae60',  # Black Knights
                'b': '#8e44ad',  # Black Bishops
                'r': '#c0392b',  # Black Rooks
                'q': '#f39c12',  # Black Queen
                'k': '#2c3e50'   # Black King
            }
            
            # Prepare data for the chart
            labels = []
            data = []
            chart_colors = []
            
            for piece, moves in piece_moves.items():
                labels.append(f'"{piece}"')
                data.append(str(moves))
                chart_colors.append(f'"{colors.get(piece, "#95a5a6")}"')
            
            script = f"""
            (function() {{
                var pieceUsageCtx = document.getElementById('pieceUsageChart');
                if (pieceUsageCtx) {{
                    var pieceUsageChart = new Chart(pieceUsageCtx, {{
                        type: 'bar',
                        data: {{
                            labels: [{', '.join(labels)}],
                            datasets: [{{
                                label: 'Number of Moves',
                                data: [{', '.join(data)}],
                                backgroundColor: [{', '.join(chart_colors)}]
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            plugins: {{
                                legend: {{
                                    display: false
                                }},
                                title: {{
                                    display: true,
                                    text: 'Piece Usage Distribution'
                                }}
                            }},
                            scales: {{
                                y: {{
                                    beginAtZero: true,
                                    title: {{
                                        display: true,
                                        text: 'Number of Moves'
                                    }}
                                }}
                            }}
                        }}
                    }});
                }}
            }})();
            """
        
        return script

    def generate_html(self):
        """Generate complete HTML dashboard."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Chess Analysis Dashboard</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{ padding-top: 20px; }}
                .stats-card {{ background-color: #f8f9fa; border-radius: 5px; }}
                .stats-card h3 {{ font-size: 2rem; color: #3498db; }}
                .card {{ margin-bottom: 20px; }}
                .card-header {{ background-color: #f1f1f1; }}
                .navbar-brand {{ font-weight: bold; }}
                #heatmapTabs {{ margin-bottom: 15px; }}
                .tab-content img {{ max-height: 500px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <!-- Header -->
                <header class="mb-4">
                    <nav class="navbar navbar-expand-lg navbar-light bg-light">
                        <div class="container-fluid">
                            <a class="navbar-brand" href="#">Chess Analytics Dashboard</a>
                            <span class="navbar-text">
                                Generated: {timestamp}
                            </span>
                        </div>
                    </nav>
                </header>
                
                <!-- Performance Statistics -->
                {self.create_performance_stats()}
                
                <!-- Opening Analysis -->
                {self.create_openings_section()}
                
                <!-- Piece Usage Analysis -->
                {self.create_additional_insights()}
                
                <!-- Piece Statistics -->
                {self.create_piece_stats_tables()}
                
                <!-- Visualizations -->
                <h2 class="mb-3">Visualizations</h2>
                {self.create_visualization_section()}
                
                <footer class="mt-5 mb-3 text-center text-muted">
                    <p>Copycat Chess Engine Analytics</p>
                </footer>
            </div>
            
            <!-- Scripts -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    // Performance charts
                    {self.generate_performance_scripts()}
                    
                    // Piece usage chart
                    {self.generate_piece_usage_script()}
                    
                    // Phase distribution charts
                    {self.generate_phase_chart_scripts()}
                }});
            </script>
        </body>
        </html>
        """
        
        return html

    def generate_dashboard(self):
        """Generate and save the HTML dashboard."""
        html = self.generate_html()
        
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"Dashboard generated at: {self.output_file}")
        return self.output_file

def main():
    generator = ChessDashboardGenerator()
    dashboard_path = generator.generate_dashboard()
    print(f"\nOpen this file in a web browser to view your dashboard: {dashboard_path}")

if __name__ == "__main__":
    main()
