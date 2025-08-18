#!/usr/bin/env python3
"""
Simplified Chess Engine Analysis Dashboard

Streamlined web interface focusing on key metrics:
- Engine Rankings (ELO-based)
- Head-to-Head Performance
- Tournament Performance
- Engine Development Progress

Ensures consistent naming consolidation throughout all views.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from typing import Dict, List, Any, Optional

# Page configuration
st.set_page_config(
    page_title="Chess Engine Analysis Dashboard",
    page_icon="♞",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_unified_data(results_dir='data'):
    """Load the unified tournament analysis data"""
    try:
        unified_path = os.path.join(results_dir, 'unified_tournament_analysis.json')
        if os.path.exists(unified_path):
            with open(unified_path, 'r') as f:
                return json.load(f)
        else:
            st.error("Unified tournament analysis data not found. Please run the analyzer first.")
            return None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def parse_engine_family(engine_name: str) -> str:
    """Extract engine family from consolidated name"""
    # The consolidated names should already be clean, just extract family
    if 'SlowMate' in engine_name:
        return 'SlowMate'
    elif 'Cece' in engine_name:
        return 'Cece'
    elif 'V7P3R' in engine_name:
        return 'V7P3R'
    elif 'C0BR4' in engine_name:
        return 'C0BR4'
    elif 'Copycat' in engine_name:
        return 'Copycat'
    elif 'Cecilia' in engine_name:
        return 'Cecilia'
    elif 'Stockfish' in engine_name:
        return 'Stockfish'
    elif 'Random' in engine_name:
        return 'Random'
    else:
        return 'Other'

def show_engine_rankings(data):
    """Display unified engine rankings"""
    st.header("🏆 Engine Rankings")
    
    rankings = data.get('unified_rankings', [])
    if not rankings:
        st.warning("No ranking data available")
        return
    
    # Create main rankings table
    df = pd.DataFrame(rankings)
    df['Family'] = df['name'].apply(parse_engine_family)
    
    # Key metrics columns
    display_cols = ['rank', 'name', 'estimated_rating', 'games', 'win_rate', 'score_percentage', 'tournaments', 'reliability_score']
    
    # Format the display
    df_display = df[display_cols].copy()
    df_display['win_rate'] = (df_display['win_rate'] * 100).round(1)
    df_display['score_percentage'] = df_display['score_percentage'].round(1)
    df_display['reliability_score'] = df_display['reliability_score'].round(3)
    
    # Rename columns for better display
    df_display.columns = ['Rank', 'Engine', 'Rating', 'Games', 'Win %', 'Score %', 'Tournaments', 'Reliability']
    
    st.dataframe(df_display, use_container_width=True, height=400)
    
    # Top performers chart
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 10 by Rating")
        top_10 = df.head(10)
        fig = px.bar(top_10, x='name', y='estimated_rating', 
                     title='Top 10 Engine Ratings',
                     color='Family')
        fig.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Rating vs Games Played")
        fig = px.scatter(df, x='games', y='estimated_rating', 
                        color='Family', hover_name='name',
                        title='Rating vs Experience',
                        size='reliability_score', size_max=20)
        st.plotly_chart(fig, use_container_width=True)

def show_family_progress(data):
    """Show development progress by engine family"""
    st.header("📈 Engine Family Development")
    
    rankings = data.get('unified_rankings', [])
    if not rankings:
        st.warning("No ranking data available")
        return
    
    df = pd.DataFrame(rankings)
    df['Family'] = df['name'].apply(parse_engine_family)
    
    # Group by family
    families = df[df['Family'] != 'Other']['Family'].unique()
    selected_family = st.selectbox("Select Engine Family:", families)
    
    if selected_family:
        family_engines = df[df['Family'] == selected_family].sort_values('name')
        
        if len(family_engines) > 1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"{selected_family} Rating Progression")
                fig = px.line(family_engines, x='name', y='estimated_rating', 
                             title=f'{selected_family} Development Progress',
                             markers=True)
                fig.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader(f"{selected_family} Performance Metrics")
                metrics_df = family_engines[['name', 'estimated_rating', 'games', 'win_rate']].copy()
                metrics_df['win_rate'] = (metrics_df['win_rate'] * 100).round(1)
                st.dataframe(metrics_df, use_container_width=True)
        else:
            st.info(f"Only one {selected_family} engine found in data.")

def show_tournament_breakdown(data):
    """Show tournament-specific performance"""
    st.header("🏟️ Tournament Performance")
    
    tournaments = data.get('tournaments', {})
    if not tournaments:
        st.warning("No tournament data available")
        return
    
    # Tournament selector
    tournament_names = list(tournaments.keys())
    selected_tournament = st.selectbox("Select Tournament:", tournament_names)
    
    if selected_tournament:
        tournament_data = tournaments[selected_tournament]
        st.subheader(f"Tournament: {selected_tournament}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Games", tournament_data.get('games', 0))
        with col2:
            st.metric("Engines Participated", len(tournament_data.get('engines', [])))
        with col3:
            st.metric("File", tournament_data.get('file', 'Unknown'))
        
        # Engine performance in this tournament
        rankings = data.get('unified_rankings', [])
        tournament_performance = []
        
        for engine in rankings:
            if 'tournament_breakdown' in engine and selected_tournament in engine['tournament_breakdown']:
                perf = engine['tournament_breakdown'][selected_tournament]
                tournament_performance.append({
                    'Engine': engine['name'],
                    'Games': perf.get('games', 0),
                    'Wins': perf.get('wins', 0),
                    'Losses': perf.get('losses', 0),
                    'Draws': perf.get('draws', 0),
                    'Score %': round((perf.get('wins', 0) + 0.5 * perf.get('draws', 0)) / max(perf.get('games', 1), 1) * 100, 1)
                })
        
        if tournament_performance:
            df_tournament = pd.DataFrame(tournament_performance)
            df_tournament = df_tournament.sort_values('Score %', ascending=False).reset_index(drop=True)
            df_tournament.index += 1  # Start ranking from 1
            st.dataframe(df_tournament, use_container_width=True)

def show_head_to_head(data):
    """Show head-to-head performance between engines"""
    st.header("⚔️ Head-to-Head Performance")
    
    rankings = data.get('unified_rankings', [])
    if not rankings:
        st.warning("No ranking data available")
        return
    
    engine_names = [engine['name'] for engine in rankings]
    
    col1, col2 = st.columns(2)
    with col1:
        engine1 = st.selectbox("Engine 1:", engine_names, key='h2h_engine1')
    with col2:
        engine2 = st.selectbox("Engine 2:", engine_names, key='h2h_engine2')
    
    if engine1 and engine2 and engine1 != engine2:
        # Find head-to-head data
        engine1_data = next((e for e in rankings if e['name'] == engine1), None)
        engine2_data = next((e for e in rankings if e['name'] == engine2), None)
        
        if engine1_data and engine2_data:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(f"{engine1} Rating", f"{engine1_data['estimated_rating']:.0f}")
                st.metric(f"{engine1} Total Games", engine1_data['games'])
            
            with col2:
                st.subheader("VS")
                # You could add specific head-to-head stats here if available in the data
                
            with col3:
                st.metric(f"{engine2} Rating", f"{engine2_data['estimated_rating']:.0f}")
                st.metric(f"{engine2} Total Games", engine2_data['games'])

def show_stockfish_achievers(data):
    """Show engines that have achieved wins/draws against Stockfish"""
    st.header("🏅 Stockfish Achievers")
    
    achievers = data.get('stockfish_achievers', [])
    if not achievers:
        st.info("No Stockfish achievement data available")
        return
    
    # Filter out engines with no games against Stockfish
    achievers_with_games = [a for a in achievers if a.get('stockfish_games', 0) > 0]
    
    if achievers_with_games:
        df_achievers = pd.DataFrame(achievers_with_games)
        df_achievers['Success Rate'] = ((df_achievers['wins_vs_stockfish'] + 0.5 * df_achievers['draws_vs_stockfish']) / df_achievers['stockfish_games'] * 100).round(2)
        df_achievers = df_achievers.sort_values('Success Rate', ascending=False)
        
        st.dataframe(df_achievers[['name', 'stockfish_games', 'wins_vs_stockfish', 'draws_vs_stockfish', 'losses_vs_stockfish', 'Success Rate']], 
                    use_container_width=True)
    else:
        st.info("No engines have played against Stockfish yet")

def main():
    st.title("♞ Chess Engine Analysis Dashboard")
    st.markdown("*Simplified dashboard focusing on key performance metrics*")
    
    # Load data
    data = load_unified_data()
    if not data:
        st.stop()
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select View:", [
        "🏆 Engine Rankings",
        "📈 Family Progress", 
        "🏟️ Tournament Performance",
        "⚔️ Head-to-Head",
        "🏅 Stockfish Achievers"
    ])
    
    # Show data freshness
    st.sidebar.markdown("---")
    st.sidebar.subheader("Data Info")
    analysis_date = data.get('analysis_date', 'Unknown')
    if analysis_date != 'Unknown':
        try:
            from datetime import datetime
            date_obj = datetime.fromisoformat(analysis_date.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
            st.sidebar.info(f"Last Updated: {formatted_date}")
        except:
            st.sidebar.info(f"Last Updated: {analysis_date}")
    
    summary = data.get('summary', {})
    st.sidebar.metric("Total Games", summary.get('total_games', 0))
    st.sidebar.metric("Total Engines", summary.get('total_engines', 0))
    st.sidebar.metric("Total Tournaments", summary.get('total_tournaments', 0))
    
    # Show selected page
    if page == "🏆 Engine Rankings":
        show_engine_rankings(data)
    elif page == "📈 Family Progress":
        show_family_progress(data)
    elif page == "🏟️ Tournament Performance":
        show_tournament_breakdown(data)
    elif page == "⚔️ Head-to-Head":
        show_head_to_head(data)
    elif page == "🏅 Stockfish Achievers":
        show_stockfish_achievers(data)

if __name__ == "__main__":
    main()
