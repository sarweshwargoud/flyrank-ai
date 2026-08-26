from typing import List, Optional, Dict, Any
from app.database import get_connection


class TaskRepository:
    def _row_to_dict(self, row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Converts a database row dictionary to the standardized task schema."""
        if not row:
            return None
        d = dict(row)
        d["done"] = bool(d["done"])
        if "created_at" in d and d["created_at"]:
            d["created_at"] = str(d["created_at"])
        if "updated_at" in d and d["updated_at"]:
            d["updated_at"] = str(d["updated_at"])
        return d

    def get_all_tasks(
        self,
        search: Optional[str] = None,
        done: Optional[bool] = None,
        sort_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves all tasks with optional search, filtering, and sorting using PostgreSQL."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                query = "SELECT id, title, done, created_at, updated_at FROM tasks"
                conditions = []
                params = []

                if search is not None:
                    conditions.append("title ILIKE %s")
                    params.append(f"%{search}%")

                if done is not None:
                    conditions.append("done = %s")
                    params.append(done)

                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

                if sort_by == "title":
                    query += " ORDER BY title ASC;"
                else:
                    query += " ORDER BY id ASC;"

                cur.execute(query, params)
                rows = cur.fetchall()
                return [self._row_to_dict(row) for row in rows]
        finally:
            conn.close()

    def get_task_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Fetches a single task by its ID using parameterized query."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, title, done, created_at, updated_at FROM tasks WHERE id = %s;",
                    (task_id,),
                )
                row = cur.fetchone()
                return self._row_to_dict(row)
        finally:
            conn.close()

    def create_task(self, title: str) -> Dict[str, Any]:
        """Creates a new task with done status set to False."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tasks (title, done)
                    VALUES (%s, FALSE)
                    RETURNING id, title, done, created_at, updated_at;
                    """,
                    (title,),
                )
                task = cur.fetchone()
                conn.commit()
                return self._row_to_dict(task)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def update_task(self, task_id: int, title: str, done: bool) -> Optional[Dict[str, Any]]:
        """Updates the title and done status of a task."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE tasks
                    SET title = %s, done = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING id, title, done, created_at, updated_at;
                    """,
                    (title, done, task_id),
                )
                task = cur.fetchone()
                conn.commit()
                return self._row_to_dict(task)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def delete_task(self, task_id: int) -> bool:
        """Deletes a task by ID. Returns True if deleted, False if task wasn't found."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM tasks WHERE id = %s;",
                    (task_id,),
                )
                deleted = cur.rowcount > 0
                conn.commit()
                return deleted
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, int]:
        """Calculates task completion statistics."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE done = TRUE) AS completed,
                        COUNT(*) FILTER (WHERE done = FALSE) AS pending
                    FROM tasks;
                """)
                row = cur.fetchone()
                return {
                    "total": row["total"] if row else 0,
                    "completed": row["completed"] if row else 0,
                    "pending": row["pending"] if row else 0,
                }
        finally:
            conn.close()