from backend.db.session import db_session

def run():
    with db_session(write=True) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM metrics_feedback WHERE usuario = 'test_user';")
        print("Cleaned up test_user feedback")

if __name__ == '__main__':
    run()
