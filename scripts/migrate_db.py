import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import sqlite3
from backend.app.database.session import engine, Base
import backend.app.models.entities # ensures all models are loaded

db_path = Path("storage/evidencerag.db")
print(f"Connecting to {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def add_col_if_missing(table, col, col_type):
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cursor.fetchall()]
    if col not in cols:
        print(f"Adding column {col} {col_type} to table {table}...")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")

# Check verification_results
add_col_if_missing("verification_results", "readiness_score", "INTEGER DEFAULT 100")

# Check issues
add_col_if_missing("issues", "bbox_x", "FLOAT")
add_col_if_missing("issues", "bbox_y", "FLOAT")
add_col_if_missing("issues", "bbox_width", "FLOAT")
add_col_if_missing("issues", "bbox_height", "FLOAT")

conn.commit()
conn.close()

# Also create all new tables if any are missing
Base.metadata.create_all(bind=engine)
print("Database schema migration complete.")
