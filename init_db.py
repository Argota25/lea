"""
Initialize the LEA database.

Runs schema.sql then seed.sql against lea.db.
Re-running this WIPES all existing data (because schema.sql drops tables first).
"""

import sqlite3
import os

DB_PATH = 'lea.db'
SCHEMA_PATH = 'schema.sql'
SEED_PATH = 'seed.sql'


def init_db():
    # Remove old database file to start fresh
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    
    # Apply schema
    with open(SCHEMA_PATH, 'r') as f:
        conn.executescript(f.read())
    print(f"Applied {SCHEMA_PATH}")

    # Apply seed data
    with open(SEED_PATH, 'r') as f:
        conn.executescript(f.read())
    print(f"Applied {SEED_PATH}")

    conn.commit()
    conn.close()
    print(f"Database {DB_PATH} initialized successfully.")


if __name__ == "__main__":
    init_db()