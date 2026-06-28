from app import create_app
import json

def run():
    app = create_app()
    client = app.test_client()
    
    # 1. Test invalid rating
    print("Testing invalid rating...")
    res = client.post("/api/feedback", json={
        "rating": "invalid",
        "note": "some note"
    })
    print(f"Status: {res.status_code}")
    print(res.get_json())
    
    # 2. Test valid feedback
    print("\nTesting valid feedback 'up'...")
    res = client.post("/api/feedback", json={
        "rating": "up",
        "note": "very clear explanation",
        "conversation_id": 123
    })
    print(f"Status: {res.status_code}")
    print(res.get_json())

    # 3. Verify database
    print("\nVerifying database row...")
    from backend.db.session import db_session
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM metrics_feedback ORDER BY id DESC LIMIT 1;")
        row = cur.fetchone()
        if row:
            print(dict(row))
        else:
            print("No rows found!")

        # clean up
        cur.execute("DELETE FROM metrics_feedback WHERE usuario LIKE 'Anon-%';")
        print("Cleaned up Anon-% feedback entries")

if __name__ == '__main__':
    run()
