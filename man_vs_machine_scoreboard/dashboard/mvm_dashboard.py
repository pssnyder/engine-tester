#!/usr/bin/env python3
"""
Man vs Machine Scoreboard Dashboard

Specialized Streamlit dashboard for tracking V7P3R vs SlowMate competition.
Focuses on head-to-head performance, version tracking, and competitive metrics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Page configuration
st.set_page_config(
    page_title="Man vs Machine Scoreboard",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_mvm_data(data_file='data/mvm_analysis.json'):
    """Load the Man vs Machine analysis data"""
    try:
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                return json.load(f)
        else:
            st.error("Man vs Machine analysis data not found. Please run the analyzer first.")
            return None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def show_main_scoreboard(data):
    """Display the main competitive scoreboard"""
    st.header("⚔️ Main Scoreboard: V7P3R vs SlowMate")
    
    h2h = data.get("head_to_head_summary", {})
    v7p3r = data.get("v7p3r_summary", {})
    slowmate = data.get("slowmate_summary", {})
    
    if "error" in h2h:
        st.warning(f"Head-to-head data: {h2h['error']}")
        return
    
    # Main metrics display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🤖 V7P3R Score",
            value=f"{h2h.get('v7p3r_score_percentage', 0):.1f}%",
            delta=f"{h2h.get('v7p3r_wins', 0)} wins"
        )
        st.metric(
            label="Decisive Wins",
            value=f"{h2h.get('v7p3r_decisive', 0)}",
            delta=f"{h2h.get('v7p3r_decisive', 0)}/{h2h.get('v7p3r_wins', 1)} wins"
        )
    
    with col2:
        st.metric(
            label="🥊 Total H2H Games",
            value=f"{h2h.get('total_games', 0)}",
            delta=f"{h2h.get('draws', 0)} draws"
        )
        st.metric(
            label="Draw Rate",
            value=f"{h2h.get('draw_rate', 0):.1f}%",
            delta="Tactical battles"
        )
    
    with col3:
        st.metric(
            label="🧠 SlowMate Score",
            value=f"{h2h.get('slowmate_score_percentage', 0):.1f}%",
            delta=f"{h2h.get('slowmate_wins', 0)} wins"
        )
        st.metric(
            label="Decisive Wins",
            value=f"{h2h.get('slowmate_decisive', 0)}",
            delta=f"{h2h.get('slowmate_decisive', 0)}/{h2h.get('slowmate_wins', 1)} wins"
        )
    
    # Visual scoreboard
    st.subheader("📊 Visual Scoreboard")
    
    if h2h.get('total_games', 0) > 0:
        # Create pie chart for results
        labels = ['V7P3R Wins', 'SlowMate Wins', 'Draws']
        values = [h2h.get('v7p3r_wins', 0), h2h.get('slowmate_wins', 0), h2h.get('draws', 0)]
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker_colors=colors,
            textinfo='label+percent+value'
        )])
        
        fig.update_layout(
            title="Head-to-Head Results Distribution",
            font_size=14,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance comparison bars
        col1, col2 = st.columns(2)
        
        with col1:
            # Score percentages
            fig_scores = go.Figure()
            engines = ['V7P3R', 'SlowMate']
            scores = [h2h.get('v7p3r_score_percentage', 0), h2h.get('slowmate_score_percentage', 0)]
            
            fig_scores.add_trace(go.Bar(
                x=engines,
                y=scores,
                marker_color=['#1f77b4', '#ff7f0e'],
                text=[f"{score:.1f}%" for score in scores],
                textposition='auto'
            ))
            
            fig_scores.update_layout(
                title="Score Percentage Comparison",
                yaxis_title="Score %",
                showlegend=False
            )
            
            st.plotly_chart(fig_scores, use_container_width=True)
        
        with col2:
            # Decisive wins comparison
            fig_decisive = go.Figure()
            decisive_wins = [h2h.get('v7p3r_decisive', 0), h2h.get('slowmate_decisive', 0)]
            
            fig_decisive.add_trace(go.Bar(
                x=engines,
                y=decisive_wins,
                marker_color=['#1f77b4', '#ff7f0e'],
                text=decisive_wins,
                textposition='auto'
            ))
            
            fig_decisive.update_layout(
                title="Decisive Wins (Checkmates)",
                yaxis_title="Checkmate Wins",
                showlegend=False
            )
            
            st.plotly_chart(fig_decisive, use_container_width=True)

def show_overall_performance(data):
    """Show overall performance beyond head-to-head"""
    st.header("📈 Overall Performance Analysis")
    
    v7p3r = data.get("v7p3r_summary", {})
    slowmate = data.get("slowmate_summary", {})
    
    # Overall statistics table
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🤖 V7P3R Overall Stats")
        if v7p3r:
            v7p3r_df = pd.DataFrame([
                ["Total Games", v7p3r.get('total_games', 0)],
                ["Wins", v7p3r.get('wins', 0)],
                ["Losses", v7p3r.get('losses', 0)],
                ["Draws", v7p3r.get('draws', 0)],
                ["Win Rate", f"{v7p3r.get('win_rate', 0):.1%}"],
                ["Score %", f"{v7p3r.get('score_percentage', 0):.1f}%"],
                ["Decisive Wins", v7p3r.get('decisive_wins', 0)],
                ["Decisive Win Rate", f"{v7p3r.get('decisive_win_rate', 0):.1%}"],
                ["Missed Wins", v7p3r.get('missed_wins', 0)],
                ["Avg Moves/Game", f"{v7p3r.get('average_moves', 0):.1f}"]
            ], columns=["Metric", "Value"])
            
            st.dataframe(v7p3r_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("🧠 SlowMate Overall Stats")
        if slowmate:
            slowmate_df = pd.DataFrame([
                ["Total Games", slowmate.get('total_games', 0)],
                ["Wins", slowmate.get('wins', 0)],
                ["Losses", slowmate.get('losses', 0)],
                ["Draws", slowmate.get('draws', 0)],
                ["Win Rate", f"{slowmate.get('win_rate', 0):.1%}"],
                ["Score %", f"{slowmate.get('score_percentage', 0):.1f}%"],
                ["Decisive Wins", slowmate.get('decisive_wins', 0)],
                ["Decisive Win Rate", f"{slowmate.get('decisive_win_rate', 0):.1%}"],
                ["Missed Wins", slowmate.get('missed_wins', 0)],
                ["Avg Moves/Game", f"{slowmate.get('average_moves', 0):.1f}"]
            ], columns=["Metric", "Value"])
            
            st.dataframe(slowmate_df, use_container_width=True, hide_index=True)
    
    # Performance comparison chart
    if v7p3r and slowmate:
        st.subheader("📊 Performance Comparison")
        
        metrics = ['Score %', 'Win Rate', 'Decisive Win Rate']
        v7p3r_values = [
            v7p3r.get('score_percentage', 0),
            v7p3r.get('win_rate', 0) * 100,
            v7p3r.get('decisive_win_rate', 0) * 100
        ]
        slowmate_values = [
            slowmate.get('score_percentage', 0),
            slowmate.get('win_rate', 0) * 100,
            slowmate.get('decisive_win_rate', 0) * 100
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='V7P3R',
            x=metrics,
            y=v7p3r_values,
            marker_color='#1f77b4'
        ))
        
        fig.add_trace(go.Bar(
            name='SlowMate',
            x=metrics,
            y=slowmate_values,
            marker_color='#ff7f0e'
        ))
        
        fig.update_layout(
            title="Key Performance Metrics Comparison",
            yaxis_title="Percentage",
            barmode='group',
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)

def show_version_tracking(data):
    """Show version tracking and development progress"""
    st.header("🔄 Version Tracking & Development Progress")
    
    version_data = data.get("version_tracking", {})
    v7p3r_versions = version_data.get("v7p3r_versions", {})
    slowmate_versions = version_data.get("slowmate_versions", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🤖 V7P3R Version History")
        if v7p3r_versions:
            v7p3r_list = []
            for version, stats in v7p3r_versions.items():
                v7p3r_list.append({
                    "Version": version,
                    "Games": stats.get('games', 0),
                    "Wins": stats.get('wins', 0),
                    "Losses": stats.get('losses', 0),
                    "Draws": stats.get('draws', 0),
                    "Score %": f"{stats.get('score_percentage', 0):.1f}%"
                })
            
            if v7p3r_list:
                v7p3r_df = pd.DataFrame(v7p3r_list)
                # Add numeric score column for plotting
                v7p3r_df['Score_Numeric'] = v7p3r_df['Score %'].str.replace('%', '').astype(float)
                st.dataframe(v7p3r_df.drop('Score_Numeric', axis=1), use_container_width=True, hide_index=True)
                
                # Version progression chart
                if len(v7p3r_list) > 1:
                    fig = px.line(
                        v7p3r_df, 
                        x='Version', 
                        y='Score_Numeric',
                        title="V7P3R Score Progression",
                        markers=True,
                        labels={'Score_Numeric': 'Score %'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No V7P3R version data available")
    
    with col2:
        st.subheader("🧠 SlowMate Version History")
        if slowmate_versions:
            slowmate_list = []
            for version, stats in slowmate_versions.items():
                slowmate_list.append({
                    "Version": version,
                    "Games": stats.get('games', 0),
                    "Wins": stats.get('wins', 0),
                    "Losses": stats.get('losses', 0),
                    "Draws": stats.get('draws', 0),
                    "Score %": f"{stats.get('score_percentage', 0):.1f}%"
                })
            
            if slowmate_list:
                slowmate_df = pd.DataFrame(slowmate_list)
                # Add numeric score column for plotting
                slowmate_df['Score_Numeric'] = slowmate_df['Score %'].str.replace('%', '').astype(float)
                st.dataframe(slowmate_df.drop('Score_Numeric', axis=1), use_container_width=True, hide_index=True)
                
                # Version progression chart
                if len(slowmate_list) > 1:
                    fig = px.line(
                        slowmate_df, 
                        x='Version', 
                        y='Score_Numeric',
                        title="SlowMate Score Progression",
                        markers=True,
                        labels={'Score_Numeric': 'Score %'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No SlowMate version data available")
    
    # Latest versions comparison
    if v7p3r_versions and slowmate_versions:
        st.subheader("🆚 Latest Versions Comparison")
        
        # Get latest versions (assuming highest version number or last in dict)
        latest_v7p3r = max(v7p3r_versions.keys()) if v7p3r_versions else "unknown"
        latest_slowmate = max(slowmate_versions.keys()) if slowmate_versions else "unknown"
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🤖 Latest V7P3R", latest_v7p3r)
            if latest_v7p3r in v7p3r_versions:
                stats = v7p3r_versions[latest_v7p3r]
                st.metric("Games", stats.get('games', 0))
                st.metric("Score %", f"{stats.get('score_percentage', 0):.1f}%")
        
        with col2:
            st.markdown("### VS")
        
        with col3:
            st.metric("🧠 Latest SlowMate", latest_slowmate)
            if latest_slowmate in slowmate_versions:
                stats = slowmate_versions[latest_slowmate]
                st.metric("Games", stats.get('games', 0))
                st.metric("Score %", f"{stats.get('score_percentage', 0):.1f}%")

def show_advanced_metrics(data):
    """Show advanced chess-specific metrics"""
    st.header("🎯 Advanced Chess Metrics")
    
    st.info("📝 This section will display advanced metrics as they become available:")
    
    # Placeholder for future advanced metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎲 Opening Repertoire Analysis")
        st.markdown("""
        **Coming Soon:**
        - Opening variety and success rates
        - Favorite openings by engine
        - Opening preparation effectiveness
        - ECO code distribution
        """)
        
        st.subheader("⚔️ Tactical Ability")
        st.markdown("""
        **Coming Soon:**
        - Puzzle solving accuracy
        - Tactical shot finding
        - Combination depth
        - Pattern recognition
        """)
    
    with col2:
        st.subheader("👑 Endgame Performance")
        st.markdown("""
        **Coming Soon:**
        - Endgame conversion rates
        - Theoretical endgame knowledge
        - Pawn endgame technique
        - Material advantage utilization
        """)
        
        st.subheader("🎯 Missed Opportunities")
        st.markdown("""
        **Current Analysis:**
        - Missed wins tracking
        - Blunder detection
        - Evaluation swings
        - Critical position handling
        """)
    
    # Show what data is available
    advanced = data.get("advanced_metrics", {})
    if advanced:
        st.subheader("📊 Available Advanced Data")
        for category, details in advanced.items():
            if isinstance(details, dict):
                analyzed = details.get("analyzed", False)
                if analyzed:
                    st.success(f"✅ {category.replace('_', ' ').title()}: Available")
                else:
                    reason = details.get("reason", "Not implemented")
                    st.warning(f"⏳ {category.replace('_', ' ').title()}: {reason}")

def show_tournament_breakdown(data):
    """Show detailed tournament-by-tournament breakdown"""
    st.header("🏟️ Tournament Breakdown")
    
    tournaments = data.get("tournaments", {})
    if not tournaments:
        st.warning("No tournament data available")
        return
    
    # Tournament selector
    tournament_names = list(tournaments.keys())
    selected_tournament = st.selectbox("Select Tournament:", tournament_names)
    
    if selected_tournament:
        tournament_data = tournaments[selected_tournament]
        
        st.subheader(f"Tournament: {selected_tournament}")
        
        # Basic tournament info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Games", len(tournament_data.get("games", [])))
        with col2:
            st.metric("Head-to-Head Games", len(tournament_data.get("head_to_head", [])))
        with col3:
            st.metric("V7P3R Games", len(tournament_data.get("v7p3r_games", [])))
        
        # Head-to-head results in this tournament
        h2h_games = tournament_data.get("head_to_head", [])
        if h2h_games:
            st.subheader("🥊 Head-to-Head Results")
            
            v7p3r_wins = 0
            slowmate_wins = 0
            draws = 0
            
            for game in h2h_games:
                result = game.get("result", "*")
                white = game.get("white", "")
                
                # Determine winner (assuming V7P3R engine detection works)
                if "V7P3R" in white or "v7p3r" in white:
                    v7p3r_is_white = True
                else:
                    v7p3r_is_white = False
                
                if result == "1-0":
                    if v7p3r_is_white:
                        v7p3r_wins += 1
                    else:
                        slowmate_wins += 1
                elif result == "0-1":
                    if v7p3r_is_white:
                        slowmate_wins += 1
                    else:
                        v7p3r_wins += 1
                elif result == "1/2-1/2":
                    draws += 1
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🤖 V7P3R Wins", v7p3r_wins)
            with col2:
                st.metric("🤝 Draws", draws)
            with col3:
                st.metric("🧠 SlowMate Wins", slowmate_wins)
        
        # Show game details
        if st.checkbox("Show detailed game list"):
            games_data = []
            for i, game in enumerate(h2h_games):
                games_data.append({
                    "Game": i + 1,
                    "White": game.get("white", ""),
                    "Black": game.get("black", ""),
                    "Result": game.get("result", "*"),
                    "Termination": game.get("result_type", ""),
                    "V7P3R Version": game.get("v7p3r_version", "unknown"),
                    "SlowMate Version": game.get("slowmate_version", "unknown")
                })
            
            if games_data:
                games_df = pd.DataFrame(games_data)
                st.dataframe(games_df, use_container_width=True, hide_index=True)

def main():
    st.title("⚔️ Man vs Machine Scoreboard")
    st.markdown("*Competitive dashboard tracking V7P3R vs SlowMate performance*")
    
    # Load data
    data = load_mvm_data()
    if not data:
        st.error("Please run the Man vs Machine analyzer first to generate data.")
        st.code("python man_vs_machine_scoreboard/analyzers/mvm_analyzer.py")
        st.stop()
    
    # Sidebar for navigation
    st.sidebar.title("🏆 Scoreboard Navigation")
    page = st.sidebar.radio("Select View:", [
        "⚔️ Main Scoreboard",
        "📈 Overall Performance",
        "🔄 Version Tracking",
        "🏟️ Tournament Breakdown",
        "🎯 Advanced Metrics"
    ])
    
    # Show data freshness
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Data Info")
    analysis_date = data.get('analysis_date', 'Unknown')
    if analysis_date != 'Unknown':
        try:
            date_obj = datetime.fromisoformat(analysis_date.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
            st.sidebar.info(f"📅 Last Updated: {formatted_date}")
        except:
            st.sidebar.info(f"📅 Last Updated: {analysis_date}")
    
    # Quick stats
    h2h = data.get("head_to_head_summary", {})
    if "error" not in h2h:
        st.sidebar.metric("🥊 H2H Games", h2h.get('total_games', 0))
        
        v7p3r_score = h2h.get('v7p3r_score_percentage', 0)
        slowmate_score = h2h.get('slowmate_score_percentage', 0)
        
        if v7p3r_score > slowmate_score:
            leader = "🤖 V7P3R Leading"
            lead_margin = v7p3r_score - slowmate_score
        elif slowmate_score > v7p3r_score:
            leader = "🧠 SlowMate Leading"
            lead_margin = slowmate_score - v7p3r_score
        else:
            leader = "🤝 Tied"
            lead_margin = 0
        
        st.sidebar.metric(leader, f"+{lead_margin:.1f}%" if lead_margin > 0 else "Tied")
    
    # Show selected page
    if page == "⚔️ Main Scoreboard":
        show_main_scoreboard(data)
    elif page == "📈 Overall Performance":
        show_overall_performance(data)
    elif page == "🔄 Version Tracking":
        show_version_tracking(data)
    elif page == "🏟️ Tournament Breakdown":
        show_tournament_breakdown(data)
    elif page == "🎯 Advanced Metrics":
        show_advanced_metrics(data)
    
    # Footer
    st.markdown("---")
    st.markdown("🚀 **Man vs Machine Scoreboard** - Tracking the eternal battle between human-designed and AI-managed chess engines")

if __name__ == "__main__":
    main()
