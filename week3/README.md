# FlyRank Week 3 — Containerize the Task API (PostgreSQL + Docker Compose)

## 📌 Project Overview

This project represents the third storage transition in the FlyRank Backend Track:
* **Assignment 1 (A1)**: In-memory dictionary storage (data lost on process restart).
* **Assignment 2 (A2)**: SQLite local database file `tasks.db` on disk.
* **Assignment 3 (A3 - Current)**: Production-grade **PostgreSQL 16** server running in Docker, fully containerized alongside FastAPI with **Docker Compose**, and backed by a persistent named volume.

### The Storage Swap Architecture
Across all three assignments, the **API contract, endpoints, status codes, and JSON schemas remain 100% identical**. All database-specific operations are strictly isolated inside the repository layer (`app/database.py` and `app/repository.py`), proving that storage is an implementation detail that can be replaced without modifying business logic or route contracts.

---

## 🛠️ Technologies

* **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11 / 3.10)
* **Database Engine**: [PostgreSQL 16](https://www.postgresql.org/) running in Docker
* **PostgreSQL Driver**: [psycopg 3](https://www.psycopg.org/psycopg3/) (`psycopg[binary]`)
* **Containerization**: [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)
* **Configuration**: `python-dotenv` reading `DATABASE_URL`
* **Testing**: `pytest`, `httpx`, `curl`

---

## 🚀 Quick Start (One Command Startup)

### 1. Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
* Git.

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:

**On Linux/macOS:**
```bash
cp .env.example .env
```

**On Windows (PowerShell / CMD):**
```powershell
copy .env.example .env
```

The default `.env` contents:
```env
DATABASE_URL=postgresql://postgres:dev@localhost:5432/tasks
```
*(Note: Inside Docker Compose, the API container connects to `postgresql://postgres:dev@db:5432/tasks` via the compose network).*

### 3. Run the Entire Stack
Start both the FastAPI API and the PostgreSQL database with one command:
```bash
docker compose up --build
```
Or run in detached mode:
```bash
docker compose up --build -d
```

The API will be available at: **`http://localhost:8000`**  
Interactive API Docs (Swagger UI): **`http://localhost:8000/docs`**

---

## 🏗️ Docker Compose Architecture

The system consists of two orchestrated services defined in `docker-compose.yml`:

```
┌─────────────────────────────────────────────────────────────┐
│                       Docker Network                        │
│                                                             │
│   ┌─────────────────────┐         ┌─────────────────────┐   │
│   │    api Service      │         │     db Service      │   │
│   │   (FastAPI/Uvicorn) │────────▶│   (PostgreSQL 16)   │   │
│   │     Port: 8000      │         │     Port: 5432      │   │
│   └─────────────────────┘         └──────────┬──────────┘   │
│              ▲                               │              │
└──────────────┼───────────────────────────────┼──────────────┘
               │                               ▼
        Host Port :8000             Volume: taskdata
                               (Persists across container restarts)
```

1. **`db` service**: Runs `postgres:16-alpine`. Uses a healthcheck (`pg_isready -U postgres -d tasks`) and mounts the `taskdata` named volume to `/var/lib/postgresql/data`.
2. **`api` service**: Builds the custom application image from `Dockerfile`, waits for `db` to be healthy, and connects to PostgreSQL using service name `db:5432`.

---

## 💾 Database Persistence & First-Run Seeding

### Named Volume Persistence
The PostgreSQL data is mounted to the named volume `taskdata`. This guarantees that all rows, updates, and schema changes persist across container lifecycles:
* When running `docker compose down`, containers and networks are stopped and removed, but the `taskdata` volume remains intact.
* When running `docker compose up`, the database reattaches to `taskdata` with all previous data preserved.

### First-Run Seed-Once Rule
On startup, `app/database.py` executes `init_db()`:
1. Creates the `tasks` table if it does not exist (`id SERIAL PRIMARY KEY, title TEXT NOT NULL, done BOOLEAN DEFAULT FALSE, created_at TIMESTAMP, updated_at TIMESTAMP`).
2. Checks `SELECT COUNT(*) FROM tasks;`.
3. If and only if the count is `0`, it seeds the 3 example tasks inside a transaction:
   * `"Learn FastAPI"` (done: `false`)
   * `"Build CRUD API"` (done: `false`)
   * `"Submit Assignment"` (done: `true`)
4. On subsequent restarts, existing rows are detected, preventing duplicate seed tasks.

---

## 📋 API Endpoints Specification

| Method | Endpoint | Description | Request Body | Success Status | Error Statuses |
|---|---|---|---|---|---|
| `GET` | `/tasks` | List all tasks (supports `search`, `done`, `sort`) | None | `200 OK` | — |
| `GET` | `/tasks/{id}` | Get single task by ID | None | `200 OK` | `404 Not Found` |
| `POST` | `/tasks` | Create a new task | `{"title": "Task title"}` | `201 Created` | `400 Bad Request` |
| `PUT` | `/tasks/{id}` | Update existing task | `{"title": "Updated", "done": true}` | `200 OK` | `400 Bad Request`, `404 Not Found` |
| `DELETE` | `/tasks/{id}` | Delete task by ID | None | `204 No Content` | `404 Not Found` |
| `GET` | `/health` | Healthcheck endpoint | None | `200 OK` | — |
| `GET` | `/stats` | Task completion statistics | None | `200 OK` | — |

---

## 🔒 Parameterized SQL Queries

All database operations strictly utilize parameterized queries with `%s` placeholders to guarantee security against SQL injection:

```python
# Select single task
cur.execute("SELECT id, title, done, created_at, updated_at FROM tasks WHERE id = %s;", (task_id,))

# Insert new task
cur.execute("INSERT INTO tasks (title, done) VALUES (%s, FALSE) RETURNING id, title, done, created_at, updated_at;", (title,))

# Update task
cur.execute("UPDATE tasks SET title = %s, done = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING id, title, done, created_at, updated_at;", (title, done, task_id))

# Delete task
cur.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
```

---

## 🔬 Example curl Commands & Real Outputs

### 1. `GET /tasks` (List Tasks)
```bash
curl.exe -i http://localhost:8000/tasks
```
**Pasted Output:**
```http
HTTP/1.1 200 OK
date: Wed, 26 Aug 2026 18:35:45 GMT
server: uvicorn
content-length: 559
content-type: application/json

[
  {"id":1,"title":"Learn FastAPI","done":false,"created_at":"2026-08-26 18:34:17.414029","updated_at":"2026-08-26 18:34:17.414029"},
  {"id":2,"title":"Build CRUD API","done":false,"created_at":"2026-08-26 18:34:17.414029","updated_at":"2026-08-26 18:34:17.414029"},
  {"id":3,"title":"Submit Assignment","done":true,"created_at":"2026-08-26 18:34:17.414029","updated_at":"2026-08-26 18:34:17.414029"}
]
```

### 2. `POST /tasks` (Create Task)
```bash
curl.exe -s -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Ship Week 3 Stack"}'
```
**Pasted Output:**
```http
HTTP/1.1 201 Created
date: Wed, 26 Aug 2026 18:36:01 GMT
server: uvicorn
content-length: 133
content-type: application/json

{"id":5,"title":"Ship Week 3 Stack","done":false,"created_at":"2026-08-26 18:36:02.164858","updated_at":"2026-08-26 18:36:02.164858"}
```

### 3. `POST /tasks` with Empty Title (400 Bad Request)
```bash
curl.exe -s -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "   "}'
```
**Pasted Output:**
```http
HTTP/1.1 400 Bad Request
date: Wed, 26 Aug 2026 18:36:09 GMT
server: uvicorn
content-length: 34
content-type: application/json

{"detail":"Title cannot be empty"}
```

### 4. `GET /tasks/999` (404 Not Found)
```bash
curl.exe -s -i http://localhost:8000/tasks/999
```
**Pasted Output:**
```http
HTTP/1.1 404 Not Found
date: Wed, 26 Aug 2026 18:36:05 GMT
server: uvicorn
content-length: 31
content-type: application/json

{"detail":"Task 999 not found"}
```

### 5. `DELETE /tasks/{id}` (204 No Content)
```bash
curl.exe -s -i -X DELETE http://localhost:8000/tasks/5
```
**Pasted Output:**
```http
HTTP/1.1 204 No Content
date: Wed, 26 Aug 2026 18:36:05 GMT
server: uvicorn
```

---

## 🧪 Persistence Verification Record

To empirically verify database persistence across full stack restarts:

1. **Step 1 — Start stack**:
   ```bash
   docker compose up -d
   ```
2. **Step 2 — Add task**:
   Created task `"Docker Compose Persistence Test Task"` (ID: 4).
3. **Step 3 — Stop and tear down containers**:
   ```bash
   docker compose down
   ```
   *(Containers and network removed; volume `taskdata` retained).*
4. **Step 4 — Restart stack**:
   ```bash
   docker compose up -d
   ```
5. **Step 5 — Query `GET /tasks`**:
   Result showed all 4 tasks including task ID 4, confirming that data safely survived container destruction and recreation.

---

## 📸 Database Verification & Screenshot Instructions

To view the database relations and rows directly inside PostgreSQL:

### Terminal Command:
```bash
docker compose exec db psql -U postgres -d tasks
```

### In the `psql` prompt:
```sql
-- Show table schema:
\dt

-- Show all stored task records:
SELECT id, title, done, created_at, updated_at FROM tasks;

-- Exit psql:
\q
```

### Direct CLI One-Liner for Screenshot:
```bash
docker compose exec db psql -U postgres -d tasks -c "\dt" -c "SELECT id, title, done, created_at, updated_at FROM tasks;"
```

**Observed Output:**
```text
         List of relations
 Schema | Name  | Type  |  Owner   
--------+-------+-------+----------
 public | tasks | table | postgres
(1 row)

 id |                      title                       | done |         created_at         |         updated_at         
----+--------------------------------------------------+------+----------------------------+----------------------------
  1 | Learn FastAPI                                    | f    | 2026-08-26 18:34:17.414029 | 2026-08-26 18:34:17.414029
  2 | Build CRUD API                                   | f    | 2026-08-26 18:34:17.414029 | 2026-08-26 18:34:17.414029
  3 | Submit Assignment                                | t    | 2026-08-26 18:34:17.414029 | 2026-08-26 18:34:17.414029
  4 | Docker Compose Persistence Test Task (Completed) | t    | 2026-08-26 18:34:32.701566 | 2026-08-26 18:34:32.758394
(4 rows)
```
