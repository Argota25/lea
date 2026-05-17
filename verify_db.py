"""Quick read-only check of what's in lea.db."""

import sqlite3

conn = sqlite3.connect('lea.db')
conn.row_factory = sqlite3.Row

print("=== ALBUMS ===")
for row in conn.execute("SELECT * FROM albums"):
    print(dict(row))

print("\n=== TRACKS ===")
for row in conn.execute("SELECT * FROM tracks"):
    print(dict(row))

conn.close()