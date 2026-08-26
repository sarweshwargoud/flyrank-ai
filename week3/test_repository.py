from app.database import init_db
from app.repository import TaskRepository

# Initialize and seed database if empty
init_db()

repo = TaskRepository()
tasks = repo.get_all_tasks()

print("\nTasks in PostgreSQL database:")
for task in tasks:
    print(f"ID: {task['id']} | Title: {task['title']} | Done: {task['done']} | Created: {task['created_at']}")

task_1 = repo.get_task_by_id(1)
print(f"\nTask ID 1: {task_1}")

task_999 = repo.get_task_by_id(999)
print(f"Task ID 999 (should be None): {task_999}")