"""
Visualization utilities for Puzzle Challenger.
Generate charts and reports from puzzle solving results.
"""

import matplotlib.pyplot as plt
import pandas as pd
import json
import os

def create_performance_charts(results, output_dir="."):
    """
    Create performance charts from puzzle solving results.
    
    Args:
        results: Dictionary with solver results
        output_dir: Directory to save the charts
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Overall performance chart
    fig, ax = plt.subplots(figsize=(8, 6))
    labels = ['Solved', 'Failed']
    sizes = [results['solved'], results['failed']]
    colors = ['#4CAF50', '#F44336']
    
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    plt.title('Overall Puzzle Performance')
    plt.savefig(os.path.join(output_dir, 'overall_performance.png'), dpi=300)
    plt.close()
    
    # Performance by theme
    if results['by_theme']:
        theme_data = []
        for theme, stats in results['by_theme'].items():
            if stats['total'] > 0:
                success_rate = (stats['solved'] / stats['total']) * 100
                theme_data.append({
                    'theme': theme,
                    'success_rate': success_rate,
                    'total': stats['total']
                })
        
        # Sort by success rate
        theme_df = pd.DataFrame(theme_data).sort_values(by='success_rate', ascending=False)
        
        # Filter to top 10 themes with at least 3 puzzles
        theme_df = theme_df[theme_df['total'] >= 3].head(10)
        
        if not theme_df.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.barh(theme_df['theme'], theme_df['success_rate'], color='#2196F3')
            ax.set_xlabel('Success Rate (%)')
            ax.set_xlim(0, 100)
            ax.grid(axis='x', linestyle='--', alpha=0.7)
            
            # Add value labels
            for i, v in enumerate(theme_df['success_rate']):
                ax.text(v + 1, i, f"{v:.1f}%", va='center')
                
            plt.title('Performance by Theme')
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'theme_performance.png'), dpi=300)
            plt.close()
    
    # Performance by rating range
    if results['by_rating']:
        rating_data = []
        for rating_range, stats in results['by_rating'].items():
            if stats['total'] > 0:
                success_rate = (stats['solved'] / stats['total']) * 100
                # Extract the lower bound of the range for sorting
                lower_bound = int(rating_range.split('-')[0])
                rating_data.append({
                    'rating_range': rating_range,
                    'success_rate': success_rate,
                    'total': stats['total'],
                    'lower_bound': lower_bound
                })
        
        # Sort by rating
        rating_df = pd.DataFrame(rating_data).sort_values(by='lower_bound')
        
        if not rating_df.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(rating_df['rating_range'], rating_df['success_rate'], color='#FF9800')
            ax.set_xlabel('Rating Range')
            ax.set_ylabel('Success Rate (%)')
            ax.set_ylim(0, 100)
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f"{height:.1f}%", ha='center', va='bottom', rotation=0)
            
            plt.title('Performance by Rating Range')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'rating_performance.png'), dpi=300)
            plt.close()
    
    # Create HTML report
    html_report = create_html_report(results, output_dir)
    with open(os.path.join(output_dir, 'performance_report.html'), 'w') as f:
        f.write(html_report)
    
    print(f"Charts and report saved to {output_dir}")

def create_html_report(results, output_dir):
    """Create an HTML report from the results."""
    total = results['total']
    solved = results['solved']
    success_rate = (solved / total * 100) if total > 0 else 0
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chess Engine Performance Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 1000px; margin: 0 auto; padding: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            .summary {{ display: flex; justify-content: space-around; margin: 20px 0; background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
            .stat {{ text-align: center; }}
            .stat-value {{ font-size: 2em; font-weight: bold; margin: 10px 0; }}
            .stat-label {{ font-size: 0.9em; color: #666; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
            tr:hover {{ background-color: #f5f5f5; }}
            .progress-bar {{ height: 20px; background-color: #e0e0e0; border-radius: 10px; overflow: hidden; }}
            .progress {{ height: 100%; background-color: #4CAF50; }}
            .images {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; margin: 20px 0; }}
            .image-container {{ text-align: center; }}
            img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>Chess Engine Performance Report</h1>
        
        <div class="summary">
            <div class="stat">
                <div class="stat-value">{total}</div>
                <div class="stat-label">Total Puzzles</div>
            </div>
            <div class="stat">
                <div class="stat-value">{solved}</div>
                <div class="stat-label">Solved Puzzles</div>
            </div>
            <div class="stat">
                <div class="stat-value">{success_rate:.1f}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
            <div class="stat">
                <div class="stat-value">{results['time_taken']:.1f}s</div>
                <div class="stat-label">Total Time</div>
            </div>
        </div>
        
        <h2>Performance by Theme</h2>
        <table>
            <tr>
                <th>Theme</th>
                <th>Success Rate</th>
                <th>Solved / Total</th>
            </tr>
    """
    
    # Add theme data
    sorted_themes = sorted(
        results['by_theme'].items(),
        key=lambda x: (x[1]['solved'] / x[1]['total']) if x[1]['total'] > 0 else 0,
        reverse=True
    )
    
    for theme, stats in sorted_themes:
        if stats['total'] > 0:
            theme_success = (stats['solved'] / stats['total'] * 100)
            html += f"""
            <tr>
                <td>{theme}</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress" style="width: {theme_success}%;"></div>
                    </div>
                    {theme_success:.1f}%
                </td>
                <td>{stats['solved']}/{stats['total']}</td>
            </tr>
            """
    
    html += """
        </table>
        
        <h2>Performance by Rating Range</h2>
        <table>
            <tr>
                <th>Rating Range</th>
                <th>Success Rate</th>
                <th>Solved / Total</th>
            </tr>
    """
    
    # Add rating data
    rating_data = []
    for rating_range, stats in results['by_rating'].items():
        if stats['total'] > 0:
            # Extract the lower bound of the range for sorting
            lower_bound = int(rating_range.split('-')[0])
            rating_data.append((rating_range, stats, lower_bound))
    
    # Sort by rating
    sorted_ratings = sorted(rating_data, key=lambda x: x[2])
    
    for rating_range, stats, _ in sorted_ratings:
        rating_success = (stats['solved'] / stats['total'] * 100)
        html += f"""
        <tr>
            <td>{rating_range}</td>
            <td>
                <div class="progress-bar">
                    <div class="progress" style="width: {rating_success}%;"></div>
                </div>
                {rating_success:.1f}%
            </td>
            <td>{stats['solved']}/{stats['total']}</td>
        </tr>
        """
    
    html += """
        </table>
        
        <h2>Charts</h2>
        <div class="images">
            <div class="image-container">
                <img src="overall_performance.png" alt="Overall Performance">
                <p>Overall Performance</p>
            </div>
    """
    
    # Add other charts if they exist
    if os.path.exists(os.path.join(output_dir, 'theme_performance.png')):
        html += """
            <div class="image-container">
                <img src="theme_performance.png" alt="Theme Performance">
                <p>Performance by Theme</p>
            </div>
        """
    
    if os.path.exists(os.path.join(output_dir, 'rating_performance.png')):
        html += """
            <div class="image-container">
                <img src="rating_performance.png" alt="Rating Performance">
                <p>Performance by Rating Range</p>
            </div>
        """
    
    html += """
        </div>
        
        <footer>
            <p>Generated by Puzzle Challenger</p>
        </footer>
    </body>
    </html>
    """
    
    return html

def save_results_to_json(results, output_path):
    """Save results to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {output_path}")

def load_results_from_json(input_path):
    """Load results from a JSON file."""
    with open(input_path, 'r') as f:
        results = json.load(f)
    
    return results

if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate visualizations from puzzle results')
    parser.add_argument('--results', type=str, required=True, 
                        help='Path to the JSON results file')
    parser.add_argument('--output', type=str, default='reports',
                        help='Directory to save the charts and reports')
    
    args = parser.parse_args()
    
    results = load_results_from_json(args.results)
    create_performance_charts(results, args.output)
