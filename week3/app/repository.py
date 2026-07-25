import sqlite3
from typing import List, Optional, Dict, Any
from app.database import get_connection


class TaskRepository:
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Converts a SQLite Row to a Python dictionary, converting 'done' integer to boolean."""
        d = dict(row)
        d["done"] = bool(d["done"])
        # Format timestamps as strings if they exist
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
        """Retrieves all tasks, with optional search, filtering, and sorting."""
        conn = get_connection()
        try:
            query = "SELECT id, title, done, created_at, updated_at FROM tasks"
            conditions = []
            params = []

            if search is not None:
                conditions.append("title LIKE ?")
                params.append(f"%{search}%")

            if done is not None:
                conditions.append("done = ?")
                params.append(1 if done else 0)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            if sort_by == "title":
                query += " ORDER BY title ASC"
            else:
                query += " ORDER BY id ASC"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
        finally:
            conn.close()

    def get_task_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Fetches a single task by its ID."""
        conn = get_connection()
        try:
            cursor = conn.execute(
                "SELECT id, title, done, created_at, updated_at FROM tasks WHERE id = ?;",
                (task_id,),
            )
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None
        finally:
            conn.close()

    def create_task(self, title: str) -> Dict[str, Any]:
        """Creates a new task with done status set to False."""
        conn = get_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO tasks (title, done) VALUES (?, 0);",
                (title,),
            )
            conn.commit()
            new_id = cursor.lastrowid
            
            # Fetch the newly created task to return it
            cursor = conn.execute(
                "SELECT id, title, done, created_at, updated_at FROM tasks WHERE id = ?;",
                (new_id,),
            )
            row = cursor.fetchone()
            return self._row_to_dict(row)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def update_task(self, task_id: int, title: str, done: bool) -> Optional[Dict[str, Any]]:
        """Updates the title and done status of a task."""
        conn = get_connection()
        try:
            cursor = conn.execute(
                "UPDATE tasks SET title = ?, done = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (title, 1 if done else 0, task_id),
            )
            conn.commit()
            
            if cursor.rowcount == 0:
                return None
                
            # Fetch and return the updated task
            cursor = conn.execute(
                "SELECT id, title, done, created_at, updated_at FROM tasks WHERE id = ?;",
                (task_id,),
            )
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def delete_task(self, task_id: int) -> bool:
        """Deletes a task by ID. Returns True if deleted, False if task wasn't found."""
        conn = get_connection()
        try:
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?;", (task_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, int]:
        """Calculates task completion statistics."""
        conn = get_connection()
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM tasks;")
            total = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM tasks WHERE done = 1;")
            completed = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM tasks WHERE done = 0;")
            pending = cursor.fetchone()[0]

            return {
                "total": total,
                "completed": completed,
                "pending": pending
            }
        finally:
            conn.close()