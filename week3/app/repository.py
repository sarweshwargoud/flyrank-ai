from app.database import get_connection


class TaskRepository:
    def get_all_tasks(self):
        # Connect to PostgreSQL
        conn = get_connection()

        # Create a cursor to execute SQL
        cur = conn.cursor()

        # Execute SQL query
        cur.execute("""
            SELECT id, title, done
            FROM tasks
            ORDER BY id;
        """)

        # Fetch all rows
        rows = cur.fetchall()

        # Close cursor and connection
        cur.close()
        conn.close()

        # Return data
        return rowsre