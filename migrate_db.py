
import sqlite3
from pathlib import Path

# Path to database
DB_PATH = Path("data/liquor_analytics.db")

def migrate():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(flavor_analysis)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'analysis_type' not in columns:
            print("Adding 'analysis_type' column to flavor_analysis table...")
            cursor.execute("ALTER TABLE flavor_analysis ADD COLUMN analysis_type VARCHAR(50) DEFAULT 'detailed'")
            conn.commit()
            print("Migration successful: Added 'analysis_type' column.")
        else:
            print("Migration skipped: 'analysis_type' column already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
