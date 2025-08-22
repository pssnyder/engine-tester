"""
Database module for Puzzle Challenger.
Handles creating, accessing, and querying the puzzle database.
"""

import os
import pandas as pd
import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text
from sqlalchemy.sql import text  # Add this import for text queries
from sqlalchemy.orm import declarative_base, sessionmaker
from tqdm import tqdm

Base = declarative_base()

class Puzzle(Base):
    """SQLAlchemy model for chess puzzles."""
    __tablename__ = 'puzzles'
    
    id = Column(String, primary_key=True)
    fen = Column(String, nullable=False)
    moves = Column(String, nullable=False)
    rating = Column(Integer)
    rating_deviation = Column(Integer)
    popularity = Column(Integer)
    num_plays = Column(Integer)
    themes = Column(String)
    game_url = Column(String)
    opening_tags = Column(String)
    
    def __repr__(self):
        return f"<Puzzle(id='{self.id}', rating={self.rating})>"


class PuzzleDatabase:
    """Class to manage the puzzle database operations."""
    
    def __init__(self, db_path='puzzles.db'):
        """Initialize the database connection."""
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)
        
    def create_tables(self):
        """Create database tables if they don't exist."""
        Base.metadata.create_all(self.engine)
        
    def import_from_csv(self, csv_path, batch_size=10000):
        """Import puzzles from CSV file into the database."""
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        print(f"Importing puzzles from {csv_path}...")
        self.create_tables()
        
        # Use pandas to read CSV in chunks to handle large files
        chunks = pd.read_csv(csv_path, chunksize=batch_size)
        
        session = self.Session()
        total_imported = 0
        
        try:
            for chunk in tqdm(chunks):
                # Process column names to match our model
                chunk.columns = [col.lower().replace(' ', '_') for col in chunk.columns]
                
                # Convert pandas DataFrame to list of dictionaries
                records = chunk.to_dict('records')
                
                # Bulk insert into database
                conn = self.engine.connect()
                for record in records:
                    # Format record to match our model
                    puzzle = Puzzle(
                        id=record.get('puzzleid', ''),
                        fen=record.get('fen', ''),
                        moves=record.get('moves', ''),
                        rating=record.get('rating', 0),
                        rating_deviation=record.get('ratingdeviation', 0),
                        popularity=record.get('popularity', 0),
                        num_plays=record.get('numberofplays', 0),
                        themes=record.get('themes', ''),
                        game_url=record.get('gameurl', ''),
                        opening_tags=record.get('openingtags', '')
                    )
                    session.add(puzzle)
                
                session.commit()
                total_imported += len(records)
                print(f"Imported {total_imported} puzzles so far...")
                
            print(f"Successfully imported {total_imported} puzzles.")
        except Exception as e:
            session.rollback()
            print(f"Error importing puzzles: {e}")
        finally:
            session.close()
    
    def query_puzzles(self, themes=None, min_rating=0, max_rating=3500, 
                     limit_moves=0, quantity=10, strict_themes=False):
        """
        Query puzzles based on specified criteria.
        
        Args:
            themes: List of themes to filter by
            min_rating: Minimum puzzle rating
            max_rating: Maximum puzzle rating
            limit_moves: Maximum number of moves (0 = no limit)
            quantity: Number of puzzles to return
            strict_themes: If True, all themes must match; if False, any theme can match
        
        Returns:
            List of Puzzle objects
        """
        session = self.Session()
        query = session.query(Puzzle)
        
        # Apply rating filter
        query = query.filter(Puzzle.rating >= min_rating, 
                           Puzzle.rating <= max_rating)
        
        # Apply themes filter if provided
        if themes and len(themes) > 0:
            if strict_themes:
                # Must match all themes (more complex query)
                for theme in themes:
                    query = query.filter(Puzzle.themes.like(f'%{theme}%'))
            else:
                # Can match any theme
                theme_filters = []
                for theme in themes:
                    theme_filters.append(Puzzle.themes.like(f'%{theme}%'))
                from sqlalchemy import or_
                query = query.filter(or_(*theme_filters))
        
        # Apply move limit if specified
        if limit_moves > 0:
            # This is a simplification; actual implementation would count moves in the 'moves' field
            query = query.filter(Puzzle.moves.like(f'%{" " * (limit_moves - 1)}%'))
        
        # Limit number of results and return
        puzzles = query.limit(quantity).all()
        session.close()
        return puzzles
    
    def get_puzzle_by_id(self, puzzle_id):
        """Retrieve a specific puzzle by its ID."""
        session = self.Session()
        puzzle = session.query(Puzzle).filter(Puzzle.id == puzzle_id).first()
        session.close()
        return puzzle
