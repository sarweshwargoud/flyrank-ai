from app.repository import TaskRepository


repo = TaskRepository()

tasks = repo.get_all_tasks()

print("Tasks in database:")
print(tasks)