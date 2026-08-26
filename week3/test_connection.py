from app.database import get_connection

try:
    conn = get_connection()
    print("[OK] Connected to PostgreSQL successfully!")
    with conn.cursor() as cur:
        cur.execute("SELECT version();")
        ver = cur.fetchone()
        print(f"[OK] Database version: {ver['version']}")
    conn.close()

except Exception as e:
    print("[ERROR] Connection failed!")
    print(e)