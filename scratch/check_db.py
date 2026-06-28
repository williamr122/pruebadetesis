import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from backend.db.session import is_postgres, db_session

print("Database Engine PostgreSQL?", is_postgres())

with db_session(write=False) as conn:
    cur = conn.cursor()
    
    # Check if table exists
    if is_postgres():
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    else:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cur.fetchall()]
    print("Tables:", tables)

    # Let's count rows in metrics_feedback if it exists
    if "metrics_feedback" in tables:
        cur.execute("SELECT COUNT(*) FROM metrics_feedback;")
        count = cur.fetchone()[0]
        print("metrics_feedback count:", count)
        
        # Let's fetch some rows
        cur.execute("SELECT * FROM metrics_feedback LIMIT 5;")
        rows = cur.fetchall()
        print("metrics_feedback rows:")
        for r in rows:
            print(dict(r) if hasattr(r, 'keys') else r)
    else:
        print("metrics_feedback table does not exist!")
