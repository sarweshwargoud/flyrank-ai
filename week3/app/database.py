import os
from typing import Optional
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:dev@localhost:5432/tasks")


def get_connection():
    """
    Creates and returns a connection to the PostgreSQL database.
    Uses dict_row row factory to allow dict-like column access.
    """
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db() -> None:
    """
    Initializes the PostgreSQL database by creating the tasks table and indexes,
    and seeding three default tasks if the table is empty.
    All operations are committed in a safe transaction.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Create tasks table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Create indexes for filtering and searching
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks(done);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_title ON tasks(title);")

            # Check if seeding is required (seed-once rule)
            cur.execute("SELECT COUNT(*) AS count FROM tasks;")
            row = cur.fetchone()
            count = row["count"] if row else 0

            if count == 0:
                # Seed default tasks
                seed_tasks = [
                    ("Learn FastAPI", False),
                    ("Build CRUD API", False),
                    ("Submit Assignment", True),
                ]
                cur.executemany(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s);",
                    seed_tasks,
                )
                conn.commit()
                print("[OK] PostgreSQL database initialized and seeded successfully.")
            else:
                conn.commit()
                print(f"[OK] Database already initialized with {count} tasks.")

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to initialize database: {e}")
        raise e
    finally:
        conn.close()