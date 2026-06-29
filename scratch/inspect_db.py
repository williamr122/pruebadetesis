import sqlite3

def inspect():
    conn = sqlite3.connect("yelia.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # List all tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row['name'] for row in cur.fetchall()]
    print("Tables in yelia.db:")
    for t in tables:
        print(f" - {t}")
        cur.execute(f"PRAGMA table_info({t});")
        cols = cur.fetchall()
        col_names = [c['name'] for c in cols]
        print(f"   Columns: {col_names}")
        
        # Check for empty/null values in each column
        null_counts = []
        for col in col_names:
            cur.execute(f"SELECT COUNT(*) as count FROM {t} WHERE {col} IS NULL OR {col} = '';")
            empty_count = cur.fetchone()['count']
            cur.execute(f"SELECT COUNT(*) as count FROM {t};")
            total = cur.fetchone()['count']
            if empty_count > 0:
                null_counts.append(f"{col}: {empty_count}/{total} empty")
        if null_counts:
            print(f"   Empty info: {', '.join(null_counts)}")
            
    print("\n--- Relational integrity checks ---")
    # Check metrics_events records
    if "metrics_events" in tables:
        cur.execute("SELECT * FROM metrics_events LIMIT 5;")
        rows = cur.fetchall()
        print("metrics_events sample:")
        for r in rows:
            print(dict(r))
            
    if "progreso" in tables:
        cur.execute("SELECT * FROM progreso LIMIT 5;")
        rows = cur.fetchall()
        print("progreso sample:")
        for r in rows:
            print(dict(r))

    conn.close()

if __name__ == "__main__":
    inspect()
