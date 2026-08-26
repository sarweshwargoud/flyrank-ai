import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_get_all_tasks(client):
    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3


def test_get_task_by_id_success(client):
    response = client.get("/tasks/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Learn FastAPI"
    assert "done" in data


def test_get_task_by_id_not_found(client):
    response = client.get("/tasks/9999")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_post_task_valid(client):
    response = client.post("/tasks", json={"title": "Test PostgreSQL Task"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test PostgreSQL Task"
    assert data["done"] is False
    assert "id" in data
    assert "updated_at" in data


def test_post_task_empty_title(client):
    response = client.post("/tasks", json={"title": "   "})
    assert response.status_code == 400
    assert "detail" in response.json()


def test_put_task_success(client):
    # First create a task to update
    create_res = client.post("/tasks", json={"title": "Task to Update"})
    task_id = create_res.json()["id"]

    response = client.put(f"/tasks/{task_id}", json={"title": "Updated Task Title", "done": True})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Updated Task Title"
    assert data["done"] is True


def test_put_task_not_found(client):
    response = client.put("/tasks/9999", json={"title": "Non-existent", "done": True})
    assert response.status_code == 404


def test_put_task_empty_title(client):
    response = client.put("/tasks/1", json={"title": "", "done": True})
    assert response.status_code == 400


def test_delete_task_success(client):
    # Create task to delete
    create_res = client.post("/tasks", json={"title": "Task to Delete"})
    task_id = create_res.json()["id"]

    delete_res = client.delete(f"/tasks/{task_id}")
    assert delete_res.status_code == 204
    assert delete_res.text == ""

    # Verify task is deleted
    get_res = client.get(f"/tasks/{task_id}")
    assert get_res.status_code == 404


def test_delete_task_not_found(client):
    response = client.delete("/tasks/9999")
    assert response.status_code == 404


def test_stats_endpoint(client):
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "completed" in data
    assert "pending" in data
