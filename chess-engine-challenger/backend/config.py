"""
Configuration settings for Chess Engine Challenger
"""

class Config:
    """Application configuration"""
    
    # Time controls in format "base_minutes|increment_seconds"
    TIME_CONTROLS = [
        "30|0",   # 30 minutes, no increment
        "10|5",   # 10 minutes + 5 seconds per move
        "5|5",    # 5 minutes + 5 seconds per move
        "3|2",    # 3 minutes + 2 seconds per move
        "1|1",    # 1 minute + 1 second per move
    ]
    
    # Default engine thinking time in milliseconds
    DEFAULT_ENGINE_TIME = 1000
    
    # Database configuration
    DATABASE_PATH = '../data/games.db'
    
    # Game records directory
    GAME_RECORDS_DIR = '../game_records'
    
    # Starting ELO ratings
    STARTING_ELO = {
        'V7P3R': 1800,  # Estimated starting ELO
        'C0BR4': 1600,
        'SlowMate': 1400,
        'Human': 1500,  # Default human rating
    }
    
    # ELO calculation parameters
    K_FACTOR = 32  # Standard K-factor for ELO calculations
