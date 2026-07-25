from app.database import init_db
from app.repository import TaskRepository

# Initialize and seed database if empty
init_db()

repo = TaskRepository()
tasks = repo.get_all_tasks()

print("\nTasks in database:")
for task in tasks:
    print(f"ID: {task['id']} | Title: {task['title']} | Done: {task['done']}")