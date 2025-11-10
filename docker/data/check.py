import sqlite3
import json

conn = sqlite3.connect('/app/data/afp_realtime_analysis.db')
cursor = conn.cursor()
cursor.execute('SELECT source_type, source_id FROM comparisons LIMIT 3')
for row in cursor.fetchall():
    print(f"\nType: {row[0]}")
    print(f"Length: {len(row[1])}")
    data = json.loads(row[1])
    print(f"Title: {data.get('title', 'N/A')[:80]}")
    content = data.get('content', 'N/A')
    print(f"Content length: {len(content)}")
    print(f"Preview: {content[:150]}")
    print("-" * 80)
conn.close()
