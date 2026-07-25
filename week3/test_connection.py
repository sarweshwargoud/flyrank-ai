from app.database import get_connection

try:
    conn = get_connection()
    print("[OK] Connected to SQLite successfully!")
    conn.close()

except Exception as e:
    print("[ERROR] Connection failed!")
    print(e)