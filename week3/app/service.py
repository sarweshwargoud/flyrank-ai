from typing import List, Optional, Dict, Any
from app.repository import TaskRepository


class TaskService:
    def __init__(self):
        self.repository = TaskRepository()

    def get_all_tasks(
        self,
        search: Optional[str] = None,
        done: Optional[bool] = None,
        sort_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return self.repository.get_all_tasks(search=search, done=done, sort_by=sort_by)

    def get_task_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        return self.repository.get_task_by_id(task_id)

    def create_task(self, title: str) -> Dict[str, Any]:
        if not title or title.strip() == "":
            raise ValueError("Title cannot be empty")
        return self.repository.create_task(title.strip())

    def update_task(self, task_id: int, title: str, done: bool) -> Optional[Dict[str, Any]]:
        if not title or title.strip() == "":
            raise ValueError("Title cannot be empty")
        return self.repository.update_task(task_id, title.strip(), done)

    def delete_task(self, task_id: int) -> bool:
        return self.repository.delete_task(task_id)

    def get_stats(self) -> Dict[str, int]:
        return self.repository.get_stats()
