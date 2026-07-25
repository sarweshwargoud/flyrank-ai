import os
import sqlite3

# Define database file path inside week3 directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "tasks.db")


def get_connection() -> sqlite3.Connection:
    """
    Creates and returns a connection to the SQLite database.
    Sets row_factory to sqlite3.Row to allow column access by name.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Initializes the database by creating the tasks table and index,
    and seeding three default tasks if the table is empty.
    All seeding is wrapped in a transaction.
    """
    conn = get_connection()
    try:
        # Enable write-ahead logging (WAL) for better concurrent performance
        conn.execute("PRAGMA journal_mode=WAL;")

        # Create tasks table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Add index for search/filtering optimization (Stretch Goal)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks(done);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_title ON tasks(title);")

        # Check if seeding is required
        cursor = conn.execute("SELECT COUNT(*) FROM tasks;")
        count = cursor.fetchone()[0]

        if count == 0:
            # Seed default tasks inside a transaction (Stretch Goal)
            conn.execute("BEGIN TRANSACTION;")
            conn.execute(
                "INSERT INTO tasks (title, done) VALUES (?, ?);",
                ("Learn FastAPI", 0),
            )
            conn.execute(
                "INSERT INTO tasks (title, done) VALUES (?, ?);",
                ("Build CRUD API", 0),
            )
            conn.execute(
                "INSERT INTO tasks (title, done) VALUES (?, ?);",
                ("Submit Assignment", 1),
            )
            conn.commit()
            print("[OK] Database initialized and seeded successfully.")
        else:
            print("[OK] Database already initialized.")

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to initialize database: {e}")
        raise e
    finally:
        conn.close()