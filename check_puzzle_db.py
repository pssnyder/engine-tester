import sqlite3

conn = sqlite3.connect('databases/puzzles.db')
c = conn.cursor()

# Get total count
result = c.execute('SELECT COUNT(*) FROM puzzles').fetchone()
print(f'Total puzzles in database: {result[0]:,}')

# Get rating stats
stats = c.execute('SELECT MIN(rating), MAX(rating), AVG(rating) FROM puzzles').fetchone()
print(f'Rating range: {stats[0]} - {stats[1]}')
print(f'Average rating: {stats[2]:.0f}')

# Get sample themes
themes = c.execute("SELECT DISTINCT themes FROM puzzles LIMIT 5").fetchall()
print(f'\nSample puzzle themes:')
for theme in themes:
    print(f'  {theme[0][:80]}')

# Get puzzle count by rating ranges
print(f'\nPuzzle count by rating:')
ranges = [
    (0, 1000),
    (1000, 1500),
    (1500, 2000),
    (2000, 2500),
    (2500, 3000),
    (3000, 9999)
]
for min_r, max_r in ranges:
    count = c.execute(f'SELECT COUNT(*) FROM puzzles WHERE rating >= {min_r} AND rating < {max_r}').fetchone()[0]
    print(f'  {min_r}-{max_r}: {count:,} puzzles')

conn.close()
