#!/usr/bin/env python3
"""
Engine Landscape Visualizer

Creates advanced visualizations for engine behavioral analysis including:
- Engine style clustering
- Behavioral relationship maps
- Performance correlation heatmaps
- Engine development trajectories
- Venn diagrams for categorical relationships
"""

import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import networkx as nx
from typing import Dict, List, Any, Tuple
import os

class EngineLandscapeVisualizer:
    def __init__(self, results_dir='results'):
        self.results_dir = results_dir
        self.behavioral_data = self.load_behavioral_data()
        self.unified_data = self.load_unified_data()
        
    def load_behavioral_data(self) -> Dict:
        """Load behavioral analysis data"""
        try:
            with open(os.path.join(self.results_dir, 'behavioral_analysis.json'), 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ Behavioral analysis data not found. Run behavioral_analyzer.py first.")
            return {}
    
    def load_unified_data(self) -> Dict:
        """Load unified tournament data"""
        try:
            with open(os.path.join(self.results_dir, 'unified_tournament_analysis.json'), 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ Unified tournament data not found.")
            return {}
    
    def create_engine_style_landscape(self) -> go.Figure:
        """Create a 2D landscape showing engine behavioral clusters"""
        if not self.behavioral_data or 'behavioral_profiles' not in self.behavioral_data:
            return go.Figure().add_annotation(text="No behavioral data available", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        profiles = self.behavioral_data['behavioral_profiles']
        
        # Prepare data for clustering
        engines = []
        features = []
        
        for engine, profile in profiles.items():
            if not profile or 'behavioral_scores' not in profile:
                continue
                
            scores = profile['behavioral_scores']
            perf = profile['performance_metrics']
            
            feature_vector = [
                scores.get('aggression', 0),
                scores.get('decisiveness', 0),
                scores.get('piece_diversity', 0),
                perf.get('win_rate', 0),
                perf.get('avg_game_length', 0),
                perf.get('capture_rate', 0)
            ]
            
            engines.append(engine)
            features.append(feature_vector)
        
        if len(features) < 3:
            return go.Figure().add_annotation(text="Insufficient data for clustering", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        # Normalize features and apply PCA
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        pca = PCA(n_components=2)
        features_2d = pca.fit_transform(features_scaled)
        
        # Perform clustering
        n_clusters = min(5, len(engines))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(features_scaled)
        
        # Create scatter plot
        df = pd.DataFrame({
            'Engine': engines,
            'PC1': features_2d[:, 0],
            'PC2': features_2d[:, 1],
            'Cluster': [f'Cluster {i+1}' for i in clusters],
            'Aggression': [profiles[e]['behavioral_scores'].get('aggression', 0) for e in engines],
            'Win_Rate': [profiles[e]['performance_metrics'].get('win_rate', 0) for e in engines],
            'Style': [profiles[e]['playing_style'].get('primary_style', 'unknown') for e in engines]
        })
        
        fig = px.scatter(df, x='PC1', y='PC2', color='Cluster', 
                        hover_name='Engine',
                        hover_data=['Aggression', 'Win_Rate', 'Style'],
                        title='🗺️ Engine Behavioral Landscape',
                        labels={'PC1': f'PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)',
                               'PC2': f'PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)'})
        
        fig.update_traces(marker=dict(size=12, line=dict(width=2, color='white')))
        fig.update_layout(
            width=800, height=600,
            showlegend=True,
            font=dict(size=12)
        )
        
        return fig
    
    def create_performance_correlation_matrix(self) -> go.Figure:
        """Create correlation heatmap of performance metrics"""
        if not self.behavioral_data or 'behavioral_profiles' not in self.behavioral_data:
            return go.Figure().add_annotation(text="No behavioral data available", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        profiles = self.behavioral_data['behavioral_profiles']
        
        # Extract metrics for correlation analysis
        metrics_data = {}
        for engine, profile in profiles.items():
            if not profile or 'behavioral_scores' not in profile:
                continue
                
            metrics_data[engine] = {
                'Aggression': profile['behavioral_scores'].get('aggression', 0),
                'Decisiveness': profile['behavioral_scores'].get('decisiveness', 0),
                'Piece Diversity': profile['behavioral_scores'].get('piece_diversity', 0),
                'Win Rate': profile['performance_metrics'].get('win_rate', 0),
                'Capture Rate': profile['performance_metrics'].get('capture_rate', 0),
                'Game Length': profile['performance_metrics'].get('avg_game_length', 0),
                'Check Rate': profile['performance_metrics'].get('check_rate', 0)
            }
        
        if len(metrics_data) < 3:
            return go.Figure().add_annotation(text="Insufficient data for correlation analysis", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        df = pd.DataFrame(metrics_data).T
        correlation_matrix = df.corr()
        
        fig = px.imshow(correlation_matrix, 
                       text_auto=True,
                       aspect="auto",
                       color_continuous_scale='RdBu_r',
                       title='🔗 Performance Metrics Correlation Matrix')
        
        fig.update_layout(width=700, height=600)
        return fig
    
    def create_engine_family_progression(self) -> go.Figure:
        """Create visualization showing engine development progression"""
        if not self.unified_data or 'unified_rankings' not in self.unified_data:
            return go.Figure().add_annotation(text="No unified rankings available", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        rankings = self.unified_data['unified_rankings']
        
        # Group engines by family
        families = {}
        for engine_data in rankings:
            engine_name = engine_data.get('name', '')
            
            # Extract family name (base name without version)
            family_name = engine_name.split()[0] if engine_name else 'Unknown'
            
            if family_name not in families:
                families[family_name] = []
            
            families[family_name].append({
                'name': engine_name,
                'rating': engine_data.get('estimated_rating', 0),
                'games': engine_data.get('games', 0),
                'win_rate': engine_data.get('win_rate', 0)
            })
        
        # Create progression plot
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set3
        
        for i, (family, engines) in enumerate(families.items()):
            if len(engines) < 2:  # Skip families with only one engine
                continue
                
            # Sort by version (attempt to extract version numbers)
            engines_sorted = sorted(engines, key=lambda x: self.extract_version(x['name']))
            
            versions = [self.extract_version(e['name']) for e in engines_sorted]
            ratings = [e['rating'] for e in engines_sorted]
            names = [e['name'] for e in engines_sorted]
            
            fig.add_trace(go.Scatter(
                x=versions,
                y=ratings,
                mode='lines+markers',
                name=family,
                line=dict(color=colors[i % len(colors)], width=3),
                marker=dict(size=10),
                text=names,
                hovertemplate='<b>%{text}</b><br>Version: %{x}<br>Rating: %{y}<extra></extra>'
            ))
        
        fig.update_layout(
            title='📈 Engine Family Development Progression',
            xaxis_title='Version',
            yaxis_title='Estimated Rating',
            width=900, height=600,
            showlegend=True
        )
        
        return fig
    
    def extract_version(self, engine_name: str) -> float:
        """Extract version number from engine name for sorting"""
        import re
        version_match = re.search(r'(\d+\.?\d*)', engine_name)
        if version_match:
            return float(version_match.group(1))
        return 0.0
    
    def create_behavioral_venn_data(self) -> Dict:
        """Prepare data for Venn diagram-style analysis"""
        if not self.behavioral_data or 'behavioral_profiles' not in self.behavioral_data:
            return {}
        
        profiles = self.behavioral_data['behavioral_profiles']
        categories = self.behavioral_data.get('engine_categories', {})
        
        venn_data = {
            'aggressive_engines': [],
            'defensive_engines': [],
            'high_win_rate_engines': [],
            'tactical_engines': [],
            'positional_engines': []
        }
        
        for engine, profile in profiles.items():
            if not profile or 'behavioral_scores' not in profile:
                continue
                
            scores = profile['behavioral_scores']
            perf = profile['performance_metrics']
            style = profile['playing_style']
            
            # Categorize engines
            if scores.get('aggression', 0) > 10:
                venn_data['aggressive_engines'].append(engine)
            
            if style.get('primary_style') == 'defensive':
                venn_data['defensive_engines'].append(engine)
            
            if perf.get('win_rate', 0) > 50:
                venn_data['high_win_rate_engines'].append(engine)
            
            if style.get('primary_style') == 'tactical':
                venn_data['tactical_engines'].append(engine)
            
            if style.get('primary_style') == 'positional':
                venn_data['positional_engines'].append(engine)
        
        return venn_data
    
    def create_engine_strength_vs_style_plot(self) -> go.Figure:
        """Create scatter plot of engine strength vs behavioral style"""
        if not self.behavioral_data or not self.unified_data:
            return go.Figure().add_annotation(text="Missing data for analysis", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        profiles = self.behavioral_data['behavioral_profiles']
        rankings = {r['name']: r for r in self.unified_data.get('unified_rankings', [])}
        
        data = []
        for engine, profile in profiles.items():
            if not profile or 'behavioral_scores' not in profile:
                continue
                
            # Find corresponding ranking data
            ranking_data = None
            for rank_name, rank_info in rankings.items():
                if engine.lower() in rank_name.lower() or rank_name.lower() in engine.lower():
                    ranking_data = rank_info
                    break
            
            if not ranking_data:
                continue
            
            data.append({
                'Engine': engine,
                'Rating': ranking_data.get('estimated_rating', 0),
                'Aggression': profile['behavioral_scores'].get('aggression', 0),
                'Decisiveness': profile['behavioral_scores'].get('decisiveness', 0),
                'Win_Rate': profile['performance_metrics'].get('win_rate', 0),
                'Style': profile['playing_style'].get('primary_style', 'unknown'),
                'Games': ranking_data.get('games', 0)
            })
        
        if not data:
            return go.Figure().add_annotation(text="No matching data found", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        df = pd.DataFrame(data)
        
        fig = px.scatter(df, x='Aggression', y='Rating', 
                        color='Style', size='Games',
                        hover_name='Engine',
                        hover_data=['Decisiveness', 'Win_Rate'],
                        title='⚔️ Engine Strength vs Playing Style',
                        labels={'Rating': 'Estimated ELO Rating', 'Aggression': 'Aggression Score'})
        
        fig.update_traces(marker=dict(line=dict(width=1, color='white')))
        fig.update_layout(width=800, height=600)
        
        return fig
    
    def create_territorial_heatmap(self, piece_type: str = 'N') -> go.Figure:
        """Create heatmap showing piece territorial preferences"""
        if not self.behavioral_data or 'behavioral_profiles' not in self.behavioral_data:
            return go.Figure().add_annotation(text="No behavioral data available", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        profiles = self.behavioral_data['behavioral_profiles']
        
        # Aggregate territorial data across all engines
        territory_data = {}
        
        for engine, profile in profiles.items():
            if not profile or 'territorial_analysis' not in profile:
                continue
                
            territorial = profile['territorial_analysis']
            if piece_type in territorial:
                for square, percentage in territorial[piece_type].items():
                    if square not in territory_data:
                        territory_data[square] = []
                    territory_data[square].append(percentage)
        
        if not territory_data:
            return go.Figure().add_annotation(text=f"No territorial data for {piece_type}", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        # Calculate average usage per square
        avg_territory = {square: np.mean(percentages) for square, percentages in territory_data.items()}
        
        # Create 8x8 board matrix
        board_matrix = np.zeros((8, 8))
        
        for square, avg_usage in avg_territory.items():
            if len(square) == 2:
                file = ord(square[0]) - ord('a')  # a-h -> 0-7
                rank = int(square[1]) - 1         # 1-8 -> 0-7
                if 0 <= file < 8 and 0 <= rank < 8:
                    board_matrix[7-rank][file] = avg_usage  # Flip rank for display
        
        # Create labels for the heatmap
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
        
        fig = px.imshow(board_matrix,
                       x=files, y=ranks,
                       color_continuous_scale='YlOrRd',
                       aspect='equal',
                       title=f'🏰 {piece_type} Piece Territorial Heatmap (Average Usage %)')
        
        fig.update_layout(width=500, height=500)
        return fig

def create_all_visualizations(results_dir='results'):
    """Create all landscape visualizations and save them"""
    visualizer = EngineLandscapeVisualizer(results_dir)
    
    visualizations = {
        'style_landscape': visualizer.create_engine_style_landscape(),
        'correlation_matrix': visualizer.create_performance_correlation_matrix(),
        'family_progression': visualizer.create_engine_family_progression(),
        'strength_vs_style': visualizer.create_engine_strength_vs_style_plot(),
        'knight_territory': visualizer.create_territorial_heatmap('N'),
        'rook_territory': visualizer.create_territorial_heatmap('R'),
        'king_territory': visualizer.create_territorial_heatmap('K')
    }
    
    return visualizations

if __name__ == "__main__":
    visualizations = create_all_visualizations()
    print("✅ All landscape visualizations created!")
