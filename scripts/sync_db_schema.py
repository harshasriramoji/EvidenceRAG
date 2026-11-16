import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import sqlite3
from sqlalchemy.schema import CreateTable
from backend.app.database.session import engine, Base
import backend.app.models.entities

db_path = Path("storage/evidencerag.db")
print(f"Syncing schema for {db_path}...")

# First, ensure all tables are created
Base.metadata.create_all(bind=engine)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Type mapping for SQLite ALTER TABLE
type_map = {
    "INTEGER": "INTEGER",
    "SMALLINT": "INTEGER",
    "BIGINT": "INTEGER",
    "FLOAT": "FLOAT",
    "NUMERIC": "FLOAT",
    "REAL": "FLOAT",
    "BOOLEAN": "BOOLEAN",
    "VARCHAR": "VARCHAR",
    "TEXT": "TEXT",
    "DATETIME": "DATETIME",
    "DATE": "DATE",
}

def get_col_type(column):
    type_str = str(column.type).upper()
    for k, v in type_map.items():
        if k in type_str:
            return v
    return "TEXT"

added_count = 0
for table_name, table in Base.metadata.tables.items():
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_cols = {row[1] for row in cursor.fetchall()}
    
    for col in table.columns:
        if col.name not in existing_cols:
            col_type = get_col_type(col)
            default_val = ""
            if col.default is not None and hasattr(col.default, 'arg'):
                arg = col.default.arg
                if isinstance(arg, (int, float)):
                    default_val = f" DEFAULT {arg}"
                elif isinstance(arg, bool):
                    default_val = f" DEFAULT {1 if arg else 0}"
                elif isinstance(arg, str):
                    default_val = f" DEFAULT '{arg}'"
            
            alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}{default_val}"
            print(f"Executing: {alter_stmt}")
            try:
                cursor.execute(alter_stmt)
                added_count += 1
            except Exception as e:
                print(f"Error adding {table_name}.{col.name}: {e}")

conn.commit()
conn.close()
print(f"Sync complete. {added_count} columns added.")
