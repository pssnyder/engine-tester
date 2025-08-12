#!/usr/bin/env python3
"""
Generate a decision flow diagram for the Copycat Chess Engine.
This script creates a visual flowchart showing how the engine makes decisions.
"""

import os
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
from matplotlib.patches import FancyArrowPatch, Rectangle, Ellipse

def create_decision_flow_diagram(output_path):
    """
    Create and save a decision flow diagram for the engine.
    
    Args:
        output_path: Path to save the diagram
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 16))
    
    # Define node positions - make sure all coordinates are floats
    nodes = {
        'start': (5.0, 15.0),
        'phase': (5.0, 13.0),
        'opening': (2.0, 11.0),
        'middlegame': (5.0, 11.0),
        'endgame': (8.0, 11.0),
        'open_detect': (2.0, 9.0),
        'open_score': (2.0, 7.0),
        'mid_score': (5.0, 9.0),
        'end_score': (8.0, 9.0),
        'piece_pref': (5.0, 7.0),
        'square_pref': (5.0, 5.0),
        'style': (5.0, 3.0),
        'final': (5.0, 1.0)
    }
    
    # Define node styles
    node_styles = {
        'start': {'shape': 'ellipse', 'color': '#3498db', 'label': 'Start\nPosition Analysis'},
        'phase': {'shape': 'diamond', 'color': '#9b59b6', 'label': 'Detect Game Phase'},
        'opening': {'shape': 'rect', 'color': '#2ecc71', 'label': 'Opening Phase'},
        'middlegame': {'shape': 'rect', 'color': '#f39c12', 'label': 'Middlegame Phase'},
        'endgame': {'shape': 'rect', 'color': '#e74c3c', 'label': 'Endgame Phase'},
        'open_detect': {'shape': 'rect', 'color': '#2ecc71', 'label': 'Detect Opening Pattern'},
        'open_score': {'shape': 'rect', 'color': '#2ecc71', 'label': 'Opening Move Scoring\n- Pattern matching\n- Win rate for opening\n- Focus opening weight'},
        'mid_score': {'shape': 'rect', 'color': '#f39c12', 'label': 'Middlegame Scoring\n- Decisiveness factor\n- Position evaluation\n- Tactical patterns'},
        'end_score': {'shape': 'rect', 'color': '#e74c3c', 'label': 'Endgame Scoring\n- Material balance\n- King safety\n- Piece coordination'},
        'piece_pref': {'shape': 'rect', 'color': '#3498db', 'label': 'Piece Preference Scoring\n- Phase-specific usage\n- Attack/Defense ratio\n- Capture tendency'},
        'square_pref': {'shape': 'rect', 'color': '#3498db', 'label': 'Square Preference Scoring\n- Heatmap data\n- Phase-specific positions\n- Attack paths'},
        'style': {'shape': 'diamond', 'color': '#9b59b6', 'label': 'Style Consistency Check'},
        'final': {'shape': 'ellipse', 'color': '#2c3e50', 'label': 'Final Move Selection\nWeighted Random from Top 3'}
    }
    
    # Draw nodes
    for node, (x, y) in nodes.items():
        style = node_styles[node]
        if style['shape'] == 'rect':
            rect = Rectangle((x-1.5, y-0.5), 3, 1, facecolor=style['color'], alpha=0.7, edgecolor='black')
            ax.add_patch(rect)
        elif style['shape'] == 'diamond':
            diamond_pts = np.array([[x, y+0.7], [x+1.5, y], [x, y-0.7], [x-1.5, y]])
            ax.fill(diamond_pts[:, 0], diamond_pts[:, 1], color=style['color'], alpha=0.7, edgecolor='black')
        elif style['shape'] == 'ellipse':
            ellipse = Ellipse((x, y), 3, 1.2, facecolor=style['color'], alpha=0.7, edgecolor='black')
            ax.add_patch(ellipse)
        
        # Add label
        ax.text(x, y, style['label'], ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Define arrows
    arrows = [
        ('start', 'phase'),
        ('phase', 'opening', 'Opening'),
        ('phase', 'middlegame', 'Middlegame'),
        ('phase', 'endgame', 'Endgame'),
        ('opening', 'open_detect'),
        ('open_detect', 'open_score'),
        ('middlegame', 'mid_score'),
        ('endgame', 'end_score'),
        ('open_score', 'piece_pref', '40%'),
        ('mid_score', 'piece_pref', '40%'),
        ('end_score', 'piece_pref', '50%'),
        ('piece_pref', 'square_pref'),
        ('square_pref', 'style'),
        ('style', 'final')
    ]
    
    # Draw arrows
    for arrow in arrows:
        if len(arrow) == 2:
            src, dst = arrow
            label = None
        else:
            src, dst, label = arrow
            
        src_x, src_y = nodes[src]
        dst_x, dst_y = nodes[dst]
        
            # Calculate control points for curved arrows if needed
        if src == 'phase' and dst in ['opening', 'middlegame', 'endgame']:
            # Create curved arrows from phase detection
            if dst == 'opening':
                control_pts = [(3.5, 12.0)]  # Make sure all values are float
            elif dst == 'middlegame':
                control_pts = []  # straight line
            else:  # endgame
                control_pts = [(6.5, 12.0)]  # Make sure all values are float            # Draw curved arrow
            if control_pts:
                arrow_path = [(src_x, src_y-0.7)]  # Start from bottom of diamond
                for pt in control_pts:
                    arrow_path.append(pt)
                arrow_path.append((dst_x, dst_y+0.5))  # End at top of rectangle
                
                # Draw path segments
                for i in range(len(arrow_path)-1):
                    x1, y1 = arrow_path[i]
                    x2, y2 = arrow_path[i+1]
                    ax.arrow(x1, y1, x2-x1, y2-y1, head_width=0.2, head_length=0.2, fc='black', ec='black', length_includes_head=True)
            else:
                # Straight line
                ax.arrow(src_x, src_y-0.7, dst_x-src_x, dst_y-src_y+0.5, head_width=0.2, head_length=0.2, fc='black', ec='black', length_includes_head=True)
        elif dst == 'piece_pref':
            # Arrows from scoring to piece preference
            ax.arrow(src_x, src_y-0.5, dst_x-src_x, dst_y-src_y+0.5, head_width=0.2, head_length=0.2, fc='black', ec='black', length_includes_head=True)
        else:
            # Standard vertical arrows
            if src_y > dst_y:
                ax.arrow(src_x, src_y-0.5, 0, dst_y-src_y+1, head_width=0.2, head_length=0.2, fc='black', ec='black', length_includes_head=True)
        
        # Add arrow label if specified
        if label:
            mid_x = (src_x + dst_x) / 2
            mid_y = (src_y + dst_y) / 2
            
            # Adjust label position for phase arrows
            if src == 'phase':
                if dst == 'opening':
                    mid_x -= 0.5
                elif dst == 'endgame':
                    mid_x += 0.5
                mid_y += 0.3
            
            # Adjust for weight percentage labels
            if dst == 'piece_pref':
                mid_y += 0.5
                if src == 'open_score':
                    mid_x -= 0.5
                elif src == 'end_score':
                    mid_x += 0.5
            
            ax.text(mid_x, mid_y, label, ha='center', va='center', fontsize=8, bbox=dict(facecolor='white', alpha=0.7))
    
    # Add decision weights table
    table_data = [
        ['Game Phase', 'Opening', 'Middlegame', 'Endgame'],
        ['Opening Book', '40%', '0%', '0%'],
        ['Piece Preference', '30%', '40%', '50%'],
        ['Square Preference', '30%', '40%', '50%'],
        ['Decisiveness', '0%', '20%', '0%']
    ]
    
    table_pos = (10, 11)
    cell_height = 0.6
    cell_width = 1.5
    
    for i, row in enumerate(table_data):
        for j, cell in enumerate(row):
            # Header row
            if i == 0 or j == 0:
                color = '#34495e'
                text_color = 'white'
            else:
                color = '#ecf0f1'
                text_color = 'black'
            
            # Draw cell
            rect = Rectangle((table_pos[0]+j*cell_width, table_pos[1]-i*cell_height), 
                             cell_width, cell_height, facecolor=color, edgecolor='black')
            ax.add_patch(rect)
            
            # Add text
            ax.text(table_pos[0]+j*cell_width+cell_width/2, table_pos[1]-i*cell_height+cell_height/2, 
                    cell, ha='center', va='center', color=text_color, fontsize=8)
    
    # Add legend for node types
    legend_x = 10
    legend_y = 6
    legend_items = [
        ('Start/End', '#3498db'),
        ('Decision', '#9b59b6'),
        ('Opening Phase', '#2ecc71'),
        ('Middlegame Phase', '#f39c12'),
        ('Endgame Phase', '#e74c3c'),
        ('Processing Step', '#3498db')
    ]
    
    for i, (label, color) in enumerate(legend_items):
        y_pos = legend_y - i * 0.7
        if i < 2:  # Start/End and Decision get special shapes
            if i == 0:  # Start/End - ellipse
                shape = Ellipse((legend_x, y_pos), 1, 0.4, facecolor=color, alpha=0.7, edgecolor='black')
            else:  # Decision - diamond
                diamond_pts = np.array([[legend_x, y_pos+0.2], [legend_x+0.2, y_pos], 
                                       [legend_x, y_pos-0.2], [legend_x-0.2, y_pos]])
                ax.fill(diamond_pts[:, 0], diamond_pts[:, 1], color=color, alpha=0.7, edgecolor='black')
                shape = None
        else:  # Rectangle for other items
            shape = Rectangle((legend_x-0.3, y_pos-0.2), 0.6, 0.4, facecolor=color, alpha=0.7, edgecolor='black')
        
        if shape:
            ax.add_patch(shape)
        
        ax.text(legend_x+0.7, y_pos, label, ha='left', va='center', fontsize=8)
    
    # Add title and metadata
    ax.text(5, 16.5, 'Copycat Chess Engine Decision Flow', ha='center', fontsize=16, fontweight='bold')
    ax.text(5, 16, 'Data Analytics Based Move Selection', ha='center', fontsize=12, fontstyle='italic')
    
    # Add explanation text
    explanation = [
        "Engine Logic:",
        "1. Analyze position to determine game phase",
        "2. Score candidate moves based on phase-specific criteria",
        "3. Apply piece and square preferences from player's style",
        "4. Ensure moves match overall style consistency",
        "5. Select final move with weighted randomness from top candidates"
    ]
    
    for i, line in enumerate(explanation):
        ax.text(10, 3-i*0.5, line, ha='left', fontsize=8)
    
    # Set axis properties
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 17)
    ax.axis('off')
    
    # Save the diagram
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Decision flow diagram saved to {output_path}")

if __name__ == "__main__":
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    create_decision_flow_diagram(os.path.join(results_dir, "engine_decision_flow.png"))
