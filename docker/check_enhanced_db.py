#!/usr/bin/env python3
import sqlite3
import os

# Try multiple possible database paths
db_paths = [
    '/app/data/afp_realtime_analysis.db',
    '/app/data/comparisons.db',
    '/tmp/comparisons.db'
]

conn = None
for path in db_paths:
    if os.path.exists(path):
        print(f"Found database at: {path}")
        conn = sqlite3.connect(path)
        break

if not conn:
    print("ERROR: Database not found!")
    exit(1)

cursor = conn.cursor()
cursor.execute('SELECT id, source_type, similarity_score, ai_explanation FROM comparisons ORDER BY id DESC LIMIT 3')

for row in cursor.fetchall():
    print("\n" + "="*100)
    print(f"ID {row[0]} [{row[1]}] - Similarity: {row[2]:.1%}")
    print("="*100)
    analysis = row[3]
    # Show full analysis to verify it's the new format
    if "COMPREHENSIVE COMPARISON ANALYSIS" in analysis:
        print(analysis[:1200] + "\n\n[... showing first 1200 chars ...]")
    else:
        print(analysis)
    print(f"\n[Full analysis length: {len(analysis)} characters]")

conn.close()
