# FlyRank Backend Internship – Week 3 Assignment

## Connecting your CRUD to the Database (SQLite)

This project moves the in-memory Task CRUD API from Week 2 to a persistent **SQLite** database. All tasks are saved to a local database file, ensuring data survives application restarts.

The project uses a clean, **modular layered architecture**:
- **`app/database.py`**: SQLite database connection, table creation, indexing, and transactional seeding.
- **`app/repository.py`**: Directly executes parameterized SQL queries against the database.
- **`app/service.py`**: Business logic and input validation (e.g. preventing empty task titles).
- **`app/routes.py`**: FastAPI route handlers defining the REST API endpoints and mapping Pydantic schemas.
- **`app/main.py`**: Application entry point.

---

## Why SQLite?

SQLite was chosen for this stage of the project because:
1. **Serverless & Zero Configuration**: SQLite reads and writes directly to ordinary disk files. There is no need to install, configure, or run a separate database server (like PostgreSQL or MySQL).
2. **Single Disk File**: The entire database (schema, tables, indexes, and data) is stored in a single file (`tasks.db`).
3. **Automatic Creation**: If the database file does not exist, SQLite creates it automatically when the application starts up.
4. **Reliability & Persistence**: It is fully ACID-compliant, ensuring that tasks are written safely to disk and survive server restarts.

---

## Database Details

- **Database File**: `tasks.db` (located in the `week3` root directory).
- **Table Name**: `tasks`
- **Schema**:
  | Column Name | Data Type | Constraints | Description |
  |-------------|-----------|-------------|-------------|
  | `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique ID generated automatically by SQLite |
  | `title` | TEXT | NOT NULL | Title of the task |
  | `done` | INTEGER | DEFAULT 0 | Done status (stored as `0` for False, `1` for True) |
  | `created_at`| TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Task creation timestamp |
  | `updated_at`| TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Task last update timestamp |

- **Indexes**:
  - `idx_tasks_done` on `tasks(done)` for optimized status filtering.
  - `idx_tasks_title` on `tasks(title)` for optimized text searches.

---

## Installation & Setup

1. Move into the `week3` directory:
   ```bash
   cd week3
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the FastAPI application using the Python module:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

---

## API Endpoints & Verification

### Base Endpoints

| Method | Endpoint | Query Params | Description | Expected Status Codes |
|--------|----------|--------------|-------------|-----------------------|
| GET | `/` | None | API Information | 200 OK |
| GET | `/health`| None | Health Check | 200 OK |
| GET | `/tasks` | `search`, `done`, `sort` | Get all tasks (supports search, status filter, and title sorting) | 200 OK |
| GET | `/tasks/{id}` | None | Get a single task by ID | 200 OK / 404 Not Found |
| POST | `/tasks` | None | Create a task | 201 Created / 400 Bad Request |
| PUT | `/tasks/{id}` | None | Update a task | 200 OK / 400 Bad Request / 404 Not Found |
| DELETE| `/tasks/{id}` | None | Delete a task | 204 No Content / 404 Not Found |
| GET | `/stats` | None | Get aggregate statistics (Total, Completed, Pending) | 200 OK |

---

## Example SQL Queries

During Stage 4, SQL queries were executed directly against `tasks.db` using a database inspector:

1. **Select all tasks**:
   ```sql
   SELECT * FROM tasks;
   ```
   *Returned:* All seeded tasks with their IDs, titles, done status (0 or 1), and timestamps.

2. **Select only completed tasks**:
   ```sql
   SELECT * FROM tasks WHERE done = 1;
   ```
   *Returned:* Only tasks where `done` equals 1.

3. **Get count of tasks**:
   ```sql
   SELECT COUNT(*) FROM tasks;
   ```
   *Returned:* The total number of rows (e.g. `3`).

4. **Mark all tasks completed**:
   ```sql
   UPDATE tasks SET done = 1;
   ```
   *Returned:* Updates all tasks to `done = 1`.

---

## DB Browser Screenshot

Below is a visualization of the database structure and tables inside **DB Browser for SQLite**:

```markdown
![DB Browser Schema](db_browser_screenshot.png)
```

*(Note: Run your application first to automatically generate the `tasks.db` file, then open it in DB Browser for SQLite to view the tables and take a screenshot!)*
