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
def get_available_tournaments(results_dir='results'):
    """Find available tournament folders and their analysis files"""
    import os
    import glob
    
    tournaments = []
    
    # Look for tournament folders matching 'Engine Battle *' pattern
    tournament_dirs = glob.glob(os.path.join(results_dir, 'Engine Battle *'))
    tournament_dirs += glob.glob(os.path.join(results_dir, 'SlowMate Tournament *'))
    
    for dir_path in tournament_dirs:
        folder_name = os.path.basename(dir_path)
        
        # Look for tournament analysis files in this directory
        analysis_files = glob.glob(os.path.join(dir_path, 'tournament_analysis_*.json'))
        
        if analysis_files:
            # Extract date from folder name
            date_match = re.search(r'(\d{8})', folder_name)
            date_str = date_match.group(1) if date_match else "Unknown"
            
            # Format date for display
            if date_str != "Unknown":
                display_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            else:
                display_date = "Unknown Date"
                
            tournaments.append({
                'folder': folder_name,
                'path': dir_path,
                'analysis_file': analysis_files[0],  # Use first analysis file
                'date': date_str,
                'display_date': display_date
            })
    
    # Sort by date (newest first)
    return sorted(tournaments, key=lambda t: t['date'], reverse=True)

@st.cache_data
def load_data(tournament_folder=None):
    """Load all analysis data files"""
    try:
        results_dir = 'results'
        
        # Get available tournaments
        available_tournaments = get_available_tournaments(results_dir)
        
        if not available_tournaments:
            st.error("No tournament data found in the results directory")
            return None, None, None, []
        
        # Use specified tournament or default to most recent
        selected_tournament = None
        if tournament_folder:
            for tournament in available_tournaments:
                if tournament['folder'] == tournament_folder:
                    selected_tournament = tournament
                    break
        
        # If no match found or none specified, use the first (most recent)
        if not selected_tournament:
            selected_tournament = available_tournaments[0]
            
        # Load tournament data
        with open(selected_tournament['analysis_file'], 'r') as f:
            tournament_data = json.load(f)
        
        # Find most recent engine test report
        test_reports = sorted(glob.glob(os.path.join(results_dir, 'engine_test_report_*.json')), reverse=True)
        if test_reports:
            with open(test_reports[0], 'r') as f:
                engine_test_data = json.load(f)
        else:
            engine_test_data = []
            
        # Load appendix data (persistent across tournaments)
        appendix_path = os.path.join(results_dir, 'results_appendix.json')
        if os.path.exists(appendix_path):
            with open(appendix_path, 'r') as f:
                appendix_data = json.load(f)
        else:
            appendix_data = {"engine_insights": {}}
            
        return tournament_data, engine_test_data, appendix_data, available_tournaments
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None, []

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

def create_tournament_overview(tournament_data):
    """Create tournament performance overview"""
    st.header("🏆 Tournament Performance Overview")
    
    # Tournament date display
    if 'date' in tournament_data:
        st.subheader(f"Tournament Date: {tournament_data['date']}")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Games", tournament_data.get('total_games', 0))
    with col2:
        st.metric("Total Engines", len(tournament_data.get('all_engines', {})))
    with col3:
        # Top performer
        if 'rankings_by_points' in tournament_data and tournament_data['rankings_by_points']:
            top_engine = tournament_data['rankings_by_points'][0]
            st.metric("Top Performer", top_engine['name'].replace('_', ' '))
        else:
            st.metric("Top Performer", "N/A")
    with col4:
        if 'rankings_by_win_rate' in tournament_data and tournament_data['rankings_by_win_rate']:
            st.metric("Top Win Rate", f"{tournament_data['rankings_by_win_rate'][0]['win_rate']:.1f}%")
        else:
            st.metric("Top Win Rate", "N/A")
    
    # Tournament points ranking chart
    st.subheader("Tournament Points Rankings")
    
    df_points = pd.DataFrame(tournament_data['rankings_by_points'][:15])  # Top 15
    df_points['engine_display'] = df_points['name'].str.replace('_', ' ')
    df_points['family'] = df_points['name'].apply(parse_engine_family)
    
    fig_points = px.bar(
        df_points, 
        x='points', 
        y='engine_display',
        color='family',
        orientation='h',
        title="Tournament Points by Engine",
        labels={'points': 'Tournament Points', 'engine_display': 'Engine'},
        color_discrete_map={'SlowMate': '#1f77b4', 'Cece': '#ff7f0e', 'Cecilia': '#2ca02c'}
    )
    fig_points.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_points, use_container_width=True)

def create_performance_analysis(tournament_data):
    """Create detailed performance analysis"""
    st.header("📊 Performance Analysis")
    
    # Win rate vs decisive win rate scatter
    st.subheader("Win Rate vs Decisive Win Rate")
    
    df_all = pd.DataFrame(list(tournament_data['all_engines'].values()))
    df_all['family'] = df_all['name'].apply(parse_engine_family)
    df_all['version'] = df_all['name'].apply(parse_version_number)
    df_all['engine_display'] = df_all['name'].str.replace('_', ' ')
    
    fig_scatter = px.scatter(
        df_all,
        x='win_rate',
        y='decisive_win_rate', 
        color='family',
        size='games',
        hover_data=['name', 'points', 'wins', 'losses', 'draws'],
        title="Win Rate vs Decisive Win Rate",
        labels={
            'win_rate': 'Win Rate (%)',
            'decisive_win_rate': 'Decisive Win Rate (%)',
            'games': 'Games Played'
        }
    )
    fig_scatter.update_layout(height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Performance by engine family
    st.subheader("Performance by Engine Family")
    
    col1, col2 = st.columns(2)
    
    with col1:
        family_stats = df_all.groupby('family').agg({
            'win_rate': 'mean',
            'decisive_win_rate': 'mean', 
            'points': 'mean',
            'games': 'sum'
        }).round(1)
        
        fig_family = px.bar(
            family_stats.reset_index(),
            x='family',
            y='win_rate', 
            title="Average Win Rate by Family",
            color='family'
        )
        st.plotly_chart(fig_family, use_container_width=True)
    
    with col2:
        fig_decisive = px.bar(
            family_stats.reset_index(),
            x='family',
            y='decisive_win_rate',
            title="Average Decisive Win Rate by Family", 
            color='family'
        )
        st.plotly_chart(fig_decisive, use_container_width=True)

def create_version_progression(tournament_data):
    """Show version progression analysis"""
    st.header("📈 Version Progression Analysis")
    
    # Filter SlowMate engines for version analysis
    df_all = pd.DataFrame(list(tournament_data['all_engines'].values()))
    slowmate_engines = df_all[df_all['name'].str.contains('SlowMate')].copy()
    slowmate_engines['version'] = slowmate_engines['name'].apply(parse_version_number)
    slowmate_engines['version_sort'] = slowmate_engines['version'].apply(
        lambda x: tuple(map(int, x.split('.')))
    )
    slowmate_engines = slowmate_engines.sort_values('version_sort')
    
    st.subheader("SlowMate Version Performance Progression")
    
    fig_progression = go.Figure()
    
    # Win rate line
    fig_progression.add_trace(go.Scatter(
        x=slowmate_engines['version'],
        y=slowmate_engines['win_rate'],
        mode='lines+markers',
        name='Win Rate (%)',
        line=dict(color='blue'),
        yaxis='y'
    ))
    
    # Decisive win rate line  
    fig_progression.add_trace(go.Scatter(
        x=slowmate_engines['version'],
        y=slowmate_engines['decisive_win_rate'],
        mode='lines+markers', 
        name='Decisive Win Rate (%)',
        line=dict(color='red'),
        yaxis='y'
    ))
    
    fig_progression.update_layout(
        title="Performance Trends Across SlowMate Versions",
        xaxis_title="Version",
        yaxis_title="Percentage (%)",
        height=500,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_progression, use_container_width=True)
    
    # Regression detection
    st.subheader("🚨 Version Regressions Detected")
    regressions = []
    for i in range(1, len(slowmate_engines)):
        prev = slowmate_engines.iloc[i-1]
        curr = slowmate_engines.iloc[i]
        win_rate_drop = prev['win_rate'] - curr['win_rate']
        if win_rate_drop > 15:  # Significant regression
            regressions.append({
                'From': prev['name'],
                'To': curr['name'], 
                'Win Rate Drop': f"{win_rate_drop:.1f}%",
                'Points Drop': f"{prev['points'] - curr['points']:.1f}"
            })
    
    if regressions:
        st.dataframe(pd.DataFrame(regressions), use_container_width=True)
    else:
        st.info("No significant regressions detected in version progression.")

def create_uci_compliance_analysis(engine_test_data, tournament_data):
    """Analyze UCI compliance vs tournament performance"""
    st.header("🔧 UCI Compliance Analysis")
    
    # Create UCI compliance lookup
    uci_lookup = {}
    for engine in engine_test_data:
        # Remove .exe extension for matching with tournament data
        engine_name = engine['engine'].replace('.exe', '')
        uci_lookup[engine_name] = {
            'critical_pass': engine['critical_pass'],
            'total_duration': engine['total_duration'],
            'stages': {stage['name']: stage['ok'] for stage in engine['stages']}
        }
    
    # Merge with tournament data
    compliance_data = []
    matched_engines = 0
    for engine_name, tournament_stats in tournament_data['all_engines'].items():
        if engine_name in uci_lookup:
            matched_engines += 1
            uci_data = uci_lookup[engine_name]
            compliance_data.append({
                'Engine': engine_name.replace('_', ' '),
                'UCI Status': 'PASS' if uci_data['critical_pass'] else 'FAIL',
                'Win Rate': tournament_stats['win_rate'],
                'Tournament Points': tournament_stats['points'],
                'Test Duration': uci_data['total_duration'],
                'Family': parse_engine_family(engine_name)
            })
    
    st.write(f"Debug: Successfully matched {matched_engines} engines between UCI and tournament data")
    
    df_compliance = pd.DataFrame(compliance_data)
    
    # Check if we have any compliance data
    if df_compliance.empty:
        st.warning("No UCI compliance data available for correlation analysis.")
        st.info("Make sure engine test results are available and engine names match between datasets.")
        return
    
    # UCI status overview
    col1, col2 = st.columns(2)
    
    with col1:
        uci_counts = df_compliance['UCI Status'].value_counts()
        fig_uci_pie = px.pie(
            values=uci_counts.values,
            names=uci_counts.index,
            title="UCI Compliance Status"
        )
        st.plotly_chart(fig_uci_pie, use_container_width=True)
    
    with col2:
        fig_compliance_scatter = px.scatter(
            df_compliance,
            x='Win Rate',
            y='Tournament Points',
            color='UCI Status',
            hover_data=['Engine'],
            title="Tournament Performance vs UCI Compliance"
        )
        st.plotly_chart(fig_compliance_scatter, use_container_width=True)
    
    # Detailed compliance table
    st.subheader("Detailed UCI Compliance Results")
    st.dataframe(
        df_compliance.sort_values('Tournament Points', ascending=False),
        use_container_width=True
    )

def create_anomaly_insights(appendix_data):
    """Display data anomalies and insights"""
    st.header("🔍 Data Insights & Anomalies")
    
    # Manual insights
    st.subheader("Engine Behavior Insights")
    
    for engine_name, insight in appendix_data['engine_insights'].items():
        with st.expander(f"🔍 {engine_name.replace('_', ' ')}"):
            st.write(f"**Expected Behavior:** {insight['expected_behavior']}")
            st.write(f"**Actual Performance:** {insight['actual_performance']}")
            st.write(f"**Analysis:** {insight['anomaly_explanation']}")
            st.write(f"**Context:** {insight['context']}")
            st.write(f"**Tags:** {', '.join(insight['tags'])}")
    
    # Automated analysis results
    if 'automated_analysis' in appendix_data:
        auto_analysis = appendix_data['automated_analysis']
        
        st.subheader("🤖 Automated Anomaly Detection")
        
        # Version regressions
        if auto_analysis['version_regressions']:
            st.write("**Version Regressions Found:**")
            for regression in auto_analysis['version_regressions']:
                severity_color = "🔴" if regression['severity'] == 'high' else "🟡"
                st.write(f"{severity_color} {regression['previous_version']} → {regression['current_version']}: "
                        f"{regression['win_rate_drop']:.1f}% win rate drop")
        
        # Feature mismatches
        if auto_analysis['feature_mismatches']:
            st.write("**Feature Implementation Issues:**")
            for mismatch in auto_analysis['feature_mismatches']:
                st.write(f"⚠️ {mismatch['engine']}: {mismatch['claimed_feature']} feature underperforming")
        
        # Data quality issues
        if auto_analysis['data_quality_issues']:
            st.write("**Data Quality Concerns:**")
            for issue in auto_analysis['data_quality_issues']:
                st.write(f"📊 {issue['engine']}: {issue['analysis']}")

def main():
    st.title("♞ Chess Engine Analysis Dashboard")
    st.markdown("Comprehensive analysis of chess engine performance and UCI compliance")
    
    # Load data
    tournament_data, engine_test_data, appendix_data, available_tournaments = load_data()
    
    if not all([tournament_data, engine_test_data, appendix_data]):
        st.error("Failed to load required data files. Please ensure all JSON files are present in the results/ directory.")
        return
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # Tournament selection
    st.sidebar.subheader("Tournament Selection")
    
    # Format tournament options for the selectbox
    tournament_options = [f"{t['folder']} ({t['display_date']})" for t in available_tournaments]
    selected_tournament_idx = st.sidebar.selectbox(
        "Select Tournament",
        range(len(tournament_options)),
        format_func=lambda i: tournament_options[i]
    )
    
    selected_tournament = available_tournaments[selected_tournament_idx]
    
    # If tournament selection changed, reload data
    if "current_tournament" not in st.session_state or st.session_state.current_tournament != selected_tournament['folder']:
        st.session_state.current_tournament = selected_tournament['folder']
        tournament_data, engine_test_data, appendix_data, _ = load_data(selected_tournament['folder'])
        
        if not all([tournament_data, engine_test_data, appendix_data]):
            st.error(f"Failed to load data for tournament {selected_tournament['folder']}.")
            return
    
    # Display selected tournament info
    st.sidebar.info(f"📅 Tournament Date: {selected_tournament['display_date']}")
    
    # Page selection
    page = st.sidebar.selectbox(
        "Choose Analysis View",
        [
            "Tournament Overview",
            "Performance Analysis", 
            "Version Progression",
            "UCI Compliance",
            "Data Insights & Anomalies"
        ]
    )
    
    # Filter options
    st.sidebar.subheader("Filters")
    
    if tournament_data and 'all_engines' in tournament_data:
        # Engine family filter
        all_engines = list(tournament_data['all_engines'].keys())
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
            max_value=100,
            value=5,
            help="Filter engines with fewer than this many games"
        )
    else:
        st.sidebar.warning("No tournament data available for filtering.")
    
    # Display selected page
    if page == "Tournament Overview":
        create_tournament_overview(tournament_data)
    elif page == "Performance Analysis":
        create_performance_analysis(tournament_data)
    elif page == "Version Progression":
        create_version_progression(tournament_data)
    elif page == "UCI Compliance":
        create_uci_compliance_analysis(engine_test_data, tournament_data)
    elif page == "Data Insights & Anomalies":
        create_anomaly_insights(appendix_data)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Data Sources:**")
    st.sidebar.markdown(f"- Tournament: {selected_tournament['folder']}")
    if engine_test_data:
        st.sidebar.markdown("- UCI Engine Tests")
    if appendix_data:
        st.sidebar.markdown("- Results Appendix") 
    st.sidebar.markdown(f"- Analysis Date: {datetime.datetime.now().strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    main()
