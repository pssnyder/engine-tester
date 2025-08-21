#!/usr/bin/env python3
"""
Comprehensive Engine Testing Workflow
Integrates ELO rating, blunder analysis, and engine validation for pre-tournament testing
"""

import os
import sys
import asyncio
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# Add the elo_testing directory to the path for imports
sys.path.append(str(Path(__file__).parent / "elo_testing"))
from elo_rating_system import EloRatingSystem, EloRating

@dataclass
class EngineTestResult:
    """Comprehensive test result for an engine"""
    engine_name: str
    version: str
    executable_path: str
    
    # ELO Rating Information
    elo_rating: Optional[float] = None
    elo_confidence: Optional[Tuple[float, float]] = None
    games_played: int = 0
    win_rate: float = 0.0
    
    # Blunder Analysis
    total_blunders: int = 0
    blunder_rate: float = 0.0  # blunders per game
    avg_blunder_magnitude: float = 0.0  # average centipawn loss
    critical_blunders: int = 0  # blunders > 300cp
    
    # Performance Metrics
    avg_depth: float = 0.0
    avg_time_per_move: float = 0.0
    time_pressure_performance: float = 0.0  # performance under time pressure
    
    # Validation Status
    is_tournament_ready: bool = False
    validation_notes: Optional[List[str]] = None
    last_tested: str = ""
    
    def __post_init__(self):
        if self.validation_notes is None:
            self.validation_notes = []
        if not self.last_tested:
            self.last_tested = datetime.now().isoformat()

class ComprehensiveEngineTester:
    """Comprehensive engine testing system"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.engines_dir = self.base_dir / "engines"
        self.results_dir = self.base_dir / "results"
        self.testing_dir = self.base_dir / "engine_testing"
        self.testing_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize sub-systems
        self.elo_system = EloRatingSystem(self.base_dir)
        self.stockfish_path = self.base_dir / "engines" / "Stockfish" / "stockfish-windows-x86-64-avx2.exe"
        
        # Tournament readiness thresholds
        self.min_games_for_rating = 20
        self.min_elo_for_tournament = 1200
        self.max_blunder_rate = 0.5  # blunders per game
        self.max_critical_blunder_rate = 0.1  # critical blunders per game
        
        # Test results storage
        self.test_results: Dict[str, EngineTestResult] = {}
        
    def _ensure_validation_notes(self, result: EngineTestResult):
        """Ensure validation_notes list is initialized"""
        if result.validation_notes is None:
            result.validation_notes = []
            
    def discover_engines(self) -> List[Tuple[str, str, Path]]:
        """Discover all available engines"""
        engines = []
        
        if not self.engines_dir.exists():
            print(f"Warning: Engines directory not found: {self.engines_dir}")
            return engines
            
        for engine_dir in self.engines_dir.iterdir():
            if engine_dir.is_dir():
                # Look for executable files
                for file in engine_dir.rglob("*.exe"):
                    if file.is_file():
                        # Extract version information from filename or directory
                        version = self._extract_version(file.name, engine_dir.name)
                        engines.append((engine_dir.name, version, file))
                        
        return engines
        
    def _extract_version(self, filename: str, dirname: str) -> str:
        """Extract version information from filename or directory"""
        # Try to find version in filename first
        name_lower = filename.lower()
        if '_v' in name_lower:
            try:
                version_part = name_lower.split('_v')[1].split('.exe')[0]
                return f"v{version_part}"
            except:
                pass
                
        # Try directory name
        if '_v' in dirname.lower():
            try:
                version_part = dirname.lower().split('_v')[1]
                return f"v{version_part}"
            except:
                pass
                
        # Default to filename without extension
        return filename.replace('.exe', '')
        
    async def test_engine_comprehensive(self, engine_name: str, version: str, 
                                      executable_path: Path) -> EngineTestResult:
        """Perform comprehensive testing of a single engine"""
        print(f"\n{'='*60}")
        print(f"COMPREHENSIVE ENGINE TEST: {engine_name} {version}")
        print(f"{'='*60}")
        
        result = EngineTestResult(
            engine_name=engine_name,
            version=version,
            executable_path=str(executable_path)
        )
        
        # Step 1: Basic validation
        print("Step 1: Basic Engine Validation")
        if not executable_path.exists():
            if result.validation_notes is None:
                result.validation_notes = []
            result.validation_notes.append(f"ERROR: Executable not found: {executable_path}")
            return result
            
        # Step 2: Load ELO rating from existing tournament data
        print("Step 2: ELO Rating Analysis")
        await self._analyze_elo_rating(result)
        
        # Step 3: Blunder analysis on existing games
        print("Step 3: Blunder Analysis")
        await self._analyze_blunders(result)
        
        # Step 4: Performance metrics
        print("Step 4: Performance Metrics")
        await self._analyze_performance(result)
        
        # Step 5: Tournament readiness assessment
        print("Step 5: Tournament Readiness Assessment")
        self._assess_tournament_readiness(result)
        
        self.test_results[f"{engine_name}_{version}"] = result
        return result
        
    async def _analyze_elo_rating(self, result: EngineTestResult):
        """Analyze ELO rating from existing tournament data"""
        # Load all tournament data
        self.elo_system.load_games_from_pgn_files(str(self.results_dir))
        
        if len(self.elo_system.games) > 0:
            # Calculate ratings
            ratings = self.elo_system.calculate_elo_internal()
            
            # Find this engine's rating
            engine_variants = [
                result.engine_name,
                f"{result.engine_name}_{result.version}",
                f"{result.engine_name} {result.version}",
                result.version
            ]
            
            for variant in engine_variants:
                if variant in ratings:
                    rating = ratings[variant]
                    result.elo_rating = rating.elo
                    result.elo_confidence = rating.confidence_interval
                    result.games_played = rating.games_played
                    result.win_rate = (rating.wins + rating.draws * 0.5) / max(rating.games_played, 1) * 100
                    
                    print(f"  Found ELO rating: {result.elo_rating:.0f} ± {(rating.confidence_interval[1] - rating.confidence_interval[0])/2:.0f}")
                    print(f"  Games played: {result.games_played}")
                    print(f"  Win rate: {result.win_rate:.1f}%")
                    return
                    
        self._ensure_validation_notes(result)
        result.validation_notes.append("No ELO rating data found - needs tournament games")
        print("  No ELO rating data found")
        
    async def _analyze_blunders(self, result: EngineTestResult):
        """Analyze blunder patterns from existing games"""
        try:
            # Import enhanced blunder analyzer
            sys.path.append(str(self.base_dir))
            from enhanced_blunder_analyzer import EnhancedBlunderAnalyzer
            
            if not self.stockfish_path.exists():
                self._ensure_validation_notes(result)
                result.validation_notes.append(f"WARNING: Stockfish not found at {self.stockfish_path}")
                print(f"  WARNING: Stockfish not found, skipping blunder analysis")
                return
                
            analyzer = EnhancedBlunderAnalyzer(str(self.stockfish_path))
            
            # Find games where this engine played
            engine_games = []
            for pgn_file in self.results_dir.rglob("*.pgn"):
                try:
                    # Try multiple encodings to handle character issues
                    content = None
                    for encoding in ['utf-8', 'latin-1', 'cp1252', 'utf-8-sig']:
                        try:
                            with open(pgn_file, 'r', encoding=encoding, errors='ignore') as f:
                                content = f.read()
                                break
                        except UnicodeDecodeError:
                            continue
                    
                    if content and (result.engine_name in content or result.version in content):
                        engine_games.append(pgn_file)
                except Exception as e:
                    print(f"    Error reading {pgn_file}: {e}")
                    continue
                    
            if not engine_games:
                self._ensure_validation_notes(result)
                result.validation_notes.append("No games found for blunder analysis")
                print("  No games found for blunder analysis")
                return
                
            print(f"  Analyzing {len(engine_games)} game files...")
            
            total_blunders = 0
            total_games = 0
            total_magnitude = 0
            critical_blunders = 0
            
            # Analyze a sample of games (limit for performance)
            sample_games = engine_games[:5]  # Analyze first 5 files
            
            for pgn_file in sample_games:
                try:
                    game_analysis = await analyzer.analyze_games_in_file(str(pgn_file))
                    
                    for game_id, analysis in game_analysis.items():
                        # Check if this engine was involved
                        if (result.engine_name in analysis.get('white_engine', '') or 
                            result.engine_name in analysis.get('black_engine', '') or
                            result.version in analysis.get('white_engine', '') or 
                            result.version in analysis.get('black_engine', '')):
                            
                            total_games += 1
                            game_blunders = len(analysis.get('blunders', []))
                            total_blunders += game_blunders
                            
                            for blunder in analysis.get('blunders', []):
                                magnitude = abs(blunder.get('eval_change', 0))
                                total_magnitude += magnitude
                                if magnitude > 300:  # Critical blunder threshold
                                    critical_blunders += 1
                                    
                except Exception as e:
                    print(f"    Error analyzing {pgn_file}: {e}")
                    continue
                    
            if total_games > 0:
                result.total_blunders = total_blunders
                result.blunder_rate = total_blunders / total_games
                result.avg_blunder_magnitude = total_magnitude / max(total_blunders, 1)
                result.critical_blunders = critical_blunders
                
                print(f"  Blunder analysis complete:")
                print(f"    Games analyzed: {total_games}")
                print(f"    Total blunders: {total_blunders}")
                print(f"    Blunder rate: {result.blunder_rate:.2f} per game")
                print(f"    Avg magnitude: {result.avg_blunder_magnitude:.0f} centipawns")
                print(f"    Critical blunders: {critical_blunders}")
            else:
                self._ensure_validation_notes(result)
                result.validation_notes.append("No games found with this engine for blunder analysis")
                print("  No games found with this engine")
                
        except ImportError:
            self._ensure_validation_notes(result)
            result.validation_notes.append("Enhanced blunder analyzer not available")
            print("  Enhanced blunder analyzer not available")
        except Exception as e:
            self._ensure_validation_notes(result)
            result.validation_notes.append(f"Blunder analysis error: {e}")
            print(f"  Blunder analysis error: {e}")
            
    async def _analyze_performance(self, result: EngineTestResult):
        """Analyze performance metrics"""
        # TODO: Implement performance analysis
        # For now, use placeholder values
        result.avg_depth = 12.0  # Placeholder
        result.avg_time_per_move = 1.5  # Placeholder
        result.time_pressure_performance = 0.85  # Placeholder
        print("  Performance analysis: Not yet implemented")
        
    def _assess_tournament_readiness(self, result: EngineTestResult):
        """Assess if engine is ready for tournament play"""
        checks = []
        
        # Check 1: Minimum games played
        if result.games_played >= self.min_games_for_rating:
            checks.append("✓ Sufficient games played for reliable rating")
        else:
            checks.append(f"✗ Needs more games ({result.games_played}/{self.min_games_for_rating})")
            
        # Check 2: Minimum ELO rating
        if result.elo_rating and result.elo_rating >= self.min_elo_for_tournament:
            checks.append(f"✓ ELO rating acceptable ({result.elo_rating:.0f})")
        else:
            checks.append(f"✗ ELO rating too low or unknown")
            
        # Check 3: Blunder rate
        if result.blunder_rate <= self.max_blunder_rate:
            checks.append(f"✓ Blunder rate acceptable ({result.blunder_rate:.2f})")
        else:
            checks.append(f"✗ Blunder rate too high ({result.blunder_rate:.2f})")
            
        # Check 4: Critical blunder rate
        critical_rate = result.critical_blunders / max(result.games_played, 1)
        if critical_rate <= self.max_critical_blunder_rate:
            checks.append(f"✓ Critical blunder rate acceptable ({critical_rate:.2f})")
        else:
            checks.append(f"✗ Critical blunder rate too high ({critical_rate:.2f})")
            
        # Check 5: Executable exists
        if Path(result.executable_path).exists():
            checks.append("✓ Executable found and accessible")
        else:
            checks.append("✗ Executable not found")
            
        # Determine readiness
        passed_checks = sum(1 for check in checks if check.startswith("✓"))
        result.is_tournament_ready = passed_checks >= 4  # Need at least 4/5 checks
        
        print("  Tournament Readiness Assessment:")
        for check in checks:
            print(f"    {check}")
        print(f"  Overall: {'READY' if result.is_tournament_ready else 'NOT READY'}")
        
    async def batch_test_engines(self, engine_families: Optional[List[str]] = None) -> Dict[str, EngineTestResult]:
        """Test multiple engines in batch"""
        engines = self.discover_engines()
        
        if engine_families:
            # Filter to only requested families
            engines = [
                (name, version, path) for name, version, path in engines
                if any(family.lower() in name.lower() for family in engine_families)
            ]
            
        print(f"Found {len(engines)} engines to test")
        
        results = {}
        for engine_name, version, executable_path in engines:
            try:
                result = await self.test_engine_comprehensive(engine_name, version, executable_path)
                results[f"{engine_name}_{version}"] = result
            except Exception as e:
                print(f"Error testing {engine_name} {version}: {e}")
                
        return results
        
    def generate_comprehensive_report(self, output_file: str = "comprehensive_engine_report.json"):
        """Generate comprehensive testing report"""
        if not self.test_results:
            print("No test results available")
            return
            
        output_path = self.testing_dir / output_file
        
        # Prepare report data
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_engines_tested": len(self.test_results),
            "tournament_ready_engines": sum(1 for r in self.test_results.values() if r.is_tournament_ready),
            "testing_criteria": {
                "min_games_for_rating": self.min_games_for_rating,
                "min_elo_for_tournament": self.min_elo_for_tournament,
                "max_blunder_rate": self.max_blunder_rate,
                "max_critical_blunder_rate": self.max_critical_blunder_rate
            },
            "engines": [asdict(result) for result in self.test_results.values()]
        }
        
        # Save JSON report
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"Comprehensive report saved to {output_path}")
        
        # Generate summary
        self._print_summary_report()
        
    def _print_summary_report(self):
        """Print summary to console"""
        print("\n" + "="*80)
        print("COMPREHENSIVE ENGINE TESTING SUMMARY")
        print("="*80)
        
        # Sort by tournament readiness, then by ELO
        sorted_results = sorted(
            self.test_results.values(),
            key=lambda x: (x.is_tournament_ready, x.elo_rating or 0),
            reverse=True
        )
        
        print(f"{'Engine':<25} {'Version':<15} {'ELO':<6} {'Games':<6} {'Blunders':<8} {'Ready':<6}")
        print("-" * 80)
        
        for result in sorted_results:
            elo_str = f"{result.elo_rating:.0f}" if result.elo_rating else "N/A"
            blunder_str = f"{result.blunder_rate:.2f}" if result.blunder_rate > 0 else "N/A"
            ready_str = "YES" if result.is_tournament_ready else "NO"
            
            print(f"{result.engine_name[:24]:<25} {result.version[:14]:<15} {elo_str:<6} "
                  f"{result.games_played:<6} {blunder_str:<8} {ready_str:<6}")
            
        # Summary statistics
        ready_count = sum(1 for r in self.test_results.values() if r.is_tournament_ready)
        print(f"\nSummary: {ready_count}/{len(self.test_results)} engines are tournament ready")
        
        # Recommendations
        print("\nRecommendations:")
        for result in sorted_results:
            if not result.is_tournament_ready and result.validation_notes:
                print(f"  {result.engine_name} {result.version}:")
                for note in result.validation_notes[:3]:  # Show first 3 notes
                    print(f"    - {note}")

async def main():
    """Main testing workflow"""
    tester = ComprehensiveEngineTester()
    
    # Test specific engine families
    engine_families = ["SlowMate", "Cece", "V7P3R", "C0BR4"]
    
    print("Starting comprehensive engine testing...")
    results = await tester.batch_test_engines(engine_families)
    
    # Generate report
    tester.generate_comprehensive_report()
    
    # Show tournament ready engines
    ready_engines = [r for r in results.values() if r.is_tournament_ready]
    if ready_engines:
        print(f"\n🏆 TOURNAMENT READY ENGINES ({len(ready_engines)}):")
        for engine in ready_engines:
            print(f"  - {engine.engine_name} {engine.version} (ELO: {engine.elo_rating:.0f})")
    else:
        print("\n⚠️  No engines currently meet tournament readiness criteria")

if __name__ == "__main__":
    asyncio.run(main())
