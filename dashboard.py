#!/usr/bin/env python3
"""
Chess Engine Analysis Dashboard

Streamlit web interface for visualizing engine test results, tournament performance,
and data insights from the engine analysis system.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import re
import os
import glob
import datetime
from typing import Dict, List, Any, Tuple, Optional

# Page configuration
st.set_page_config(
    page_title="Chess Engine Analysis Dashboard",
    page_icon="♞",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_unified_data(results_dir='results'):
    """Load the unified tournament analysis data"""
    try:
        unified_path = os.path.join(results_dir, 'unified_tournament_analysis.json')
        if os.path.exists(unified_path):
            with open(unified_path, 'r') as f:
                unified_data = json.load(f)
        else:
            unified_data = None
            
        # Also load appendix for additional insights
        appendix_path = os.path.join(results_dir, 'results_appendix.json')
        if os.path.exists(appendix_path):
            with open(appendix_path, 'r') as f:
                appendix_data = json.load(f)
        else:
            appendix_data = {"engine_insights": {}}
            
        return unified_data, appendix_data
    except Exception as e:
        st.error(f"Error loading unified data: {e}")
        return None, None

@st.cache_data  
def load_data(tournament_folder=None):
    """Legacy function for backward compatibility - redirects to unified data"""
    return load_unified_data()

def parse_engine_family(engine_name):
    """Extract engine family for grouping"""
    if 'SlowMate' in engine_name:
        return 'SlowMate'
    elif 'Cece' in engine_name:
        return 'Cece'  
    elif 'Cecilia' in engine_name:
        return 'Cecilia'
    else:
        return 'Other'

def parse_version_number(engine_name):
    """Extract version number for sorting"""
    patterns = [
        r'v(\d+)\.(\d+)\.(\d+)',
        r'v(\d+)\.(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, engine_name)
        if match:
            parts = match.groups()
            if len(parts) == 3:
                return f"{int(parts[0])}.{int(parts[1])}.{int(parts[2])}"
            else:
                return f"{int(parts[0])}.{int(parts[1])}.0"
    return "0.0.0"

def create_unified_overview(unified_data):
    """Create comprehensive overview across all tournaments"""
    st.header("🏆 Unified Engine Rankings - All Tournaments")
    
    if not unified_data:
        st.error("No unified tournament data available")
        return
    
    # Summary metrics
    summary = unified_data.get('summary', {})
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Games", summary.get('total_games', 0))
    with col2:
        st.metric("Total Engines", summary.get('total_engines', 0))
    with col3:
        st.metric("Tournaments", summary.get('total_tournaments', 0))
    with col4:
        st.metric("Engines with Data", summary.get('engines_with_sufficient_data', 0))
    
    # Stockfish Achievement Highlight
    stockfish_achievers = unified_data.get('stockfish_achievers', [])
    if stockfish_achievers:
        st.subheader("🎯 STOCKFISH ACHIEVEMENT UNLOCKED!")
        st.success("Your engines have successfully drawn against Stockfish 1%!")
        
        for achiever in stockfish_achievers:
            st.info(f"**{achiever['name']}**: {achiever['draws_vs_stockfish']} draws out of {achiever['stockfish_games']} games vs Stockfish (Rating: {achiever['estimated_rating']:.0f})")
    
    # Top Rankings
    rankings = unified_data.get('unified_rankings', [])
    if rankings:
        st.subheader("🏅 Top Engine Rankings by Estimated ELO")
        
        # Create DataFrame for top engines
        top_engines = rankings[:15]
        df_rankings = pd.DataFrame(top_engines)
        
        # Add family classification
        df_rankings['family'] = df_rankings['name'].apply(parse_engine_family)
        df_rankings['display_name'] = df_rankings['name'].str.replace('_', ' ')
        
        # Rating vs Games scatter plot
        fig_scatter = px.scatter(
            df_rankings,
            x='games',
            y='estimated_rating',
            color='family',
            size='reliability_score',
            hover_data=['name', 'win_rate', 'tournaments', 'stockfish_games'],
            title="Engine Rating vs Experience",
            labels={
                'games': 'Total Games Played',
                'estimated_rating': 'Estimated ELO Rating',
                'reliability_score': 'Reliability Score'
            },
            color_discrete_map={'SlowMate': '#1f77b4', 'Cece': '#ff7f0e', 'Cecilia': '#2ca02c', 'Other': '#d62728'}
        )
        fig_scatter.update_layout(height=500)
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Rankings table
        st.subheader("📊 Detailed Rankings")
        display_df = df_rankings[['name', 'estimated_rating', 'games', 'win_rate', 'score_percentage', 'tournaments', 'reliability_score', 'stockfish_games']].copy()
        display_df.columns = ['Engine', 'ELO Rating', 'Games', 'Win Rate %', 'Score %', 'Tournaments', 'Reliability', 'Stockfish Games']
        display_df = display_df.round({'ELO Rating': 0, 'Win Rate %': 1, 'Score %': 1, 'Reliability': 3})
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)

def create_stockfish_analysis(unified_data):
    """Detailed analysis of Stockfish achievements"""
    st.header("⚔️ Stockfish Achievement Analysis")
    
    stockfish_achievers = unified_data.get('stockfish_achievers', [])
    
    if not stockfish_achievers:
        st.info("No engines have notable results against Stockfish yet.")
        return
    
    st.subheader("🎖️ Hall of Fame: Engines That Drew Stockfish")
    
    for achiever in stockfish_achievers:
        with st.expander(f"🏆 {achiever['name']} - {achiever['draws_vs_stockfish']} draws vs Stockfish"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Draws vs Stockfish", achiever['draws_vs_stockfish'])
                st.metric("Total Games vs Stockfish", achiever['stockfish_games'])
                st.metric("Estimated Rating", f"{achiever['estimated_rating']:.0f}")
            
            with col2:
                # Calculate survival rate against Stockfish
                survival_rate = (achiever['draws_vs_stockfish'] / achiever['stockfish_games']) * 100
                st.metric("Survival Rate vs Stockfish", f"{survival_rate:.1f}%")
                
                # Show what this means in context
                if survival_rate > 10:
                    st.success("🔥 Exceptional performance!")
                elif survival_rate > 5:
                    st.info("✨ Strong showing!")
                else:
                    st.info("💪 Respectable effort!")
    
    # Rating implications
    st.subheader("📈 What This Means")
    st.markdown("""
    Drawing against Stockfish 1% is a significant achievement because:
    - **Stockfish 1%** ≈ 2200+ ELO (still very strong!)
    - **Your engines** are estimated around 1200-1280 ELO
    - **Rating gap** of ~1000 points typically means 0.1% chance of non-loss
    - **Your achievement** suggests either:
      - Engines are stronger than estimated
      - Stockfish had tactical oversights in specific positions
      - Excellent defensive play in drawn endgames
    """)

def create_rating_progression(unified_data):
    """Show engine development progression"""
    st.header("📈 Engine Development Progression")
    
    rankings = unified_data.get('unified_rankings', [])
    engine_details = unified_data.get('engine_details', {})
    
    # Focus on SlowMate progression
    slowmate_engines = [e for e in rankings if 'SlowMate' in e['name']]
    
    if not slowmate_engines:
        st.info("No SlowMate engines found for progression analysis.")
        return
    
    # Create progression DataFrame
    progression_data = []
    for engine in slowmate_engines:
        # Extract version for sorting
        version_match = re.search(r'v?(\d+)\.(\d+)\.?(\d*)', engine['name'])
        if version_match:
            major, minor, patch = version_match.groups()
            version_sort = f"{int(major):03d}.{int(minor):03d}.{int(patch) if patch else 0:03d}"
        else:
            version_sort = "999.999.999"
        
        progression_data.append({
            'name': engine['name'],
            'version_sort': version_sort,
            'rating': engine['estimated_rating'],
            'games': engine['games'],
            'win_rate': engine['win_rate'],
            'tournaments': engine['tournaments'],
            'reliability': engine['reliability_score']
        })
    
    df_progression = pd.DataFrame(progression_data)
    df_progression = df_progression.sort_values('version_sort')
    
    # Version progression chart
    fig_progression = go.Figure()
    
    fig_progression.add_trace(go.Scatter(
        x=df_progression['name'],
        y=df_progression['rating'],
        mode='lines+markers',
        name='Estimated Rating',
        line=dict(color='blue', width=3),
        marker=dict(size=8)
    ))
    
    fig_progression.update_layout(
        title="SlowMate Version Rating Progression",
        xaxis_title="Version",
        yaxis_title="Estimated ELO Rating",
        height=500,
        xaxis={'tickangle': 45}
    )
    
    st.plotly_chart(fig_progression, use_container_width=True)
    
    # Highlight best and worst performers
    col1, col2 = st.columns(2)
    
    with col1:
        best_engine = max(slowmate_engines, key=lambda e: e['estimated_rating'])
        st.success(f"🏆 **Best SlowMate**: {best_engine['name']}")
        st.write(f"Rating: {best_engine['estimated_rating']:.0f}")
        st.write(f"Games: {best_engine['games']}")
        st.write(f"Win Rate: {best_engine['win_rate']:.1f}%")
    
    with col2:
        worst_engine = min(slowmate_engines, key=lambda e: e['estimated_rating'])
        st.warning(f"📉 **Needs Work**: {worst_engine['name']}")
        st.write(f"Rating: {worst_engine['estimated_rating']:.0f}")
        st.write(f"Games: {worst_engine['games']}")
        st.write(f"Win Rate: {worst_engine['win_rate']:.1f}%")
    
def create_tournament_breakdown(unified_data):
    """Show performance breakdown by tournament"""
    st.header("🏟️ Tournament Breakdown")
    
    tournaments = unified_data.get('tournaments', {})
    engine_details = unified_data.get('engine_details', {})
    
    if not tournaments:
        st.info("No tournament data available.")
        return
    
    st.subheader("Tournament Summary")
    
    # Tournament overview table
    tournament_data = []
    for name, data in tournaments.items():
        tournament_data.append({
            'Tournament': name,
            'Games': data['games'],
            'Engines': len(data['engines']),
            'File': data['file']
        })
    
    df_tournaments = pd.DataFrame(tournament_data)
    st.dataframe(df_tournaments, use_container_width=True, hide_index=True)
    
    # Select tournament for detailed view
    selected_tournament = st.selectbox("Select tournament for detailed analysis:", list(tournaments.keys()))
    
    if selected_tournament:
        st.subheader(f"Detailed Analysis: {selected_tournament}")
        
        tournament_engines = tournaments[selected_tournament]['engines']
        
        # Show engine performance in this tournament
        tournament_performance = []
        for engine_name in tournament_engines:
            if engine_name in engine_details:
                engine = engine_details[engine_name]
                if selected_tournament in engine['tournament_breakdown']:
                    perf = engine['tournament_breakdown'][selected_tournament]
                    tournament_performance.append({
                        'Engine': engine_name,
                        'Games': perf['games'],
                        'Wins': perf['wins'],
                        'Losses': perf['losses'],
                        'Draws': perf['draws'],
                        'Score': perf['wins'] + 0.5 * perf['draws'],
                        'Win Rate': round((perf['wins'] / perf['games']) * 100, 1) if perf['games'] > 0 else 0
                    })
        
        if tournament_performance:
            df_perf = pd.DataFrame(tournament_performance)
            df_perf = df_perf.sort_values('Score', ascending=False)
            st.dataframe(df_perf, use_container_width=True, hide_index=True)

def create_engine_deep_dive(unified_data):
    """Deep dive analysis for individual engines"""
    st.header("� Engine Deep Dive")
    
    rankings = unified_data.get('unified_rankings', [])
    engine_details = unified_data.get('engine_details', {})
    
    if not rankings:
        st.info("No engine data available.")
        return
    
    # Engine selection
    engine_names = [e['name'] for e in rankings]
    selected_engine = st.selectbox("Select engine for analysis:", engine_names)
    
    if selected_engine and selected_engine in engine_details:
        engine_data = engine_details[selected_engine]
        engine_summary = next(e for e in rankings if e['name'] == selected_engine)
        
        st.subheader(f"Analysis: {selected_engine}")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Estimated Rating", f"{engine_summary['estimated_rating']:.0f}")
        with col2:
            st.metric("Total Games", engine_summary['games'])
        with col3:
            st.metric("Win Rate", f"{engine_summary['win_rate']:.1f}%")
        with col4:
            st.metric("Reliability Score", f"{engine_summary['reliability_score']:.3f}")
        
        # Opponent analysis
        st.subheader("🎯 Head-to-Head Records")
        
        opponents_data = []
        for opponent, record in engine_data['opponents'].items():
            total_games = record['wins'] + record['losses'] + record['draws']
            if total_games > 0:
                win_rate = (record['wins'] / total_games) * 100
                score = record['wins'] + 0.5 * record['draws']
                opponents_data.append({
                    'Opponent': opponent,
                    'Games': total_games,
                    'Wins': record['wins'],
                    'Losses': record['losses'],
                    'Draws': record['draws'],
                    'Score': score,
                    'Win Rate %': round(win_rate, 1)
                })
        
        if opponents_data:
            df_opponents = pd.DataFrame(opponents_data)
            df_opponents = df_opponents.sort_values('Games', ascending=False)
            st.dataframe(df_opponents, use_container_width=True, hide_index=True)
        
        # Tournament participation
        st.subheader("🏟️ Tournament Performance")
        
        tournament_data = []
        for tournament, record in engine_data['tournament_breakdown'].items():
            if record['games'] > 0:
                win_rate = (record['wins'] / record['games']) * 100
                score = record['wins'] + 0.5 * record['draws']
                tournament_data.append({
                    'Tournament': tournament,
                    'Games': record['games'],
                    'Wins': record['wins'],
                    'Losses': record['losses'],
                    'Draws': record['draws'],
                    'Score': score,
                    'Win Rate %': round(win_rate, 1)
                })
        
        if tournament_data:
            df_tournaments = pd.DataFrame(tournament_data)
            st.dataframe(df_tournaments, use_container_width=True, hide_index=True)

# Remove old functions that are no longer needed
# (keeping parse_engine_family and parse_version_number as they're still used)

def main():
    st.title("♞ Chess Engine Analysis Dashboard")
    st.markdown("Comprehensive analysis of chess engine performance across all tournaments")
    
    # Load unified data
    unified_data, appendix_data = load_unified_data()
    
    if not unified_data:
        st.error("Failed to load unified tournament data. Please run unified_tournament_analyzer.py first.")
        return
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # Analysis date info
    analysis_date = unified_data.get('analysis_date', 'Unknown')
    if analysis_date != 'Unknown':
        formatted_date = datetime.datetime.fromisoformat(analysis_date.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
        st.sidebar.info(f"📅 Analysis Date: {formatted_date}")
    
    # Page selection
    page = st.sidebar.selectbox(
        "Choose Analysis View",
        [
            "Unified Rankings",
            "Stockfish Achievements",
            "Rating Progression",
            "Tournament Breakdown", 
            "Engine Deep Dive"
        ]
    )
    
    # Filter options
    st.sidebar.subheader("Filters")
    
    rankings = unified_data.get('unified_rankings', [])
    if rankings:
        # Engine family filter
        all_engines = [e['name'] for e in rankings]
        families = list(set([parse_engine_family(name) for name in all_engines]))
        selected_families = st.sidebar.multiselect(
            "Engine Families",
            families,
            default=families
        )
        
        # Minimum games filter
        min_games = st.sidebar.slider(
            "Minimum Games Played",
            min_value=1,
            max_value=500,
            value=10,
            help="Filter engines with fewer than this many games"
        )
        
        # Rating range filter
        if rankings:
            min_rating = min(e['estimated_rating'] for e in rankings)
            max_rating = max(e['estimated_rating'] for e in rankings)
            rating_range = st.sidebar.slider(
                "Rating Range",
                min_value=int(min_rating),
                max_value=int(max_rating),
                value=(int(min_rating), int(max_rating)),
                help="Filter engines by estimated rating"
            )
    else:
        st.sidebar.warning("No ranking data available for filtering.")
    
    # Display selected page
    if page == "Unified Rankings":
        create_unified_overview(unified_data)
    elif page == "Stockfish Achievements":
        create_stockfish_analysis(unified_data)
    elif page == "Rating Progression":
        create_rating_progression(unified_data)
    elif page == "Tournament Breakdown":
        create_tournament_breakdown(unified_data)
    elif page == "Engine Deep Dive":
        create_engine_deep_dive(unified_data)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Data Sources:**")
    summary = unified_data.get('summary', {})
    st.sidebar.markdown(f"- {summary.get('total_games', 0)} games analyzed")
    st.sidebar.markdown(f"- {summary.get('total_tournaments', 0)} tournaments")
    st.sidebar.markdown(f"- {summary.get('total_engines', 0)} engines total")
    if unified_data.get('stockfish_achievers'):
        st.sidebar.markdown("🏆 Stockfish draws achieved!")

if __name__ == "__main__":
    main()
