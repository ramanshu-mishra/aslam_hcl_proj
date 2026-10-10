"""Load student data from CSV files into SQLite database."""
import csv
import argparse
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.connection import get_db


def load_csv(file_path, table_name, conn):
    """Load a CSV file into a database table."""
    with open(file_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        if not rows:
            print(f"Warning: {file_path.name} is empty")
            return 0
        
        # Get column names
        columns = list(rows[0].keys())
        placeholders = ','.join(['?' * len(columns)])
        
        # Build INSERT query
        query = f"""
            INSERT OR REPLACE INTO {table_name} ({','.join(columns)})
            VALUES ({','.join(['?' for _ in columns])})
        """
        
        # Insert all rows
        for row in rows:
            values = [row[col] for col in columns]
            conn.execute(query, values)
        
        return len(rows)


def main():
    """Load all student data files."""
    parser = argparse.ArgumentParser(
        description="Load student data from CSV files into database"
    )
    parser.add_argument(
        '--dir',
        type=Path,
        default=Path('data/test_students'),
        help='Directory containing CSV files'
    )
    
    args = parser.parse_args()
    
    if not args.dir.exists():
        print(f"Error: Directory {args.dir} does not exist")
        return 1
    
    print(f"Loading student data from {args.dir}...\n")
    
    db = get_db()
    
    # Files to load in order (to respect foreign keys)
    files = [
        ('students.csv', 'students'),
        ('courses.csv', 'courses'),
        ('attendance.csv', 'attendance'),
        ('results.csv', 'results'),
    ]
    
    total_loaded = 0
    
    try:
        with db.transaction() as conn:
            for filename, table in files:
                file_path = args.dir / filename
                
                if not file_path.exists():
                    print(f"⚠️  {filename}: Not found, skipping")
                    continue
                
                count = load_csv(file_path, table, conn)
                print(f"✅ {filename}: Loaded {count} records into {table}")
                total_loaded += count
        
        print(f"\n{'='*60}")
        print(f"✅ Successfully loaded {total_loaded} total records")
        return 0
        
    except Exception as e:
        print(f"\n❌ Error loading data: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
