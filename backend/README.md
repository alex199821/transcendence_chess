# Backend

The server side of our online chess game. It stores users and games in a database and answers the website's requests.

## Run it

From the project root (the folder above this one):

```bash
cp .env.example .env    # only the first time
make                    # builds and starts everything
```

In `.env`, set your own `POSTGRES_PASSWORD` and a `JWT_SECRET`, the key that signs login tokens. Make the key with `openssl rand -hex 32`; under 32 characters, the backend won't start. Already have a `.env`? Add the key like this:

```bash
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env
```

Then open:
- https://localhost:8443/api/health: should say `"status":"ok"`
- https://localhost:8443/api/docs: a list of every endpoint, where you can click "Try it out" to test them

Chrome will warn about the certificate. That's normal: we make our own certificate for localhost. Click "Advanced", then "Proceed".

## How a request travels

```
Browser ──HTTPS──▶ nginx ──▶ uvicorn ──▶ FastAPI (our code) ──▶ PostgreSQL
```

- **nginx** is the only door from outside. It handles HTTPS and passes `/api/...` requests to the backend.
- **uvicorn** is the program that runs our Python app and listens for requests.
- **FastAPI** is our code: it checks the request and sends an answer.
- **PostgreSQL** is the database.

Each one runs in its own Docker container. The backend and the database can't be reached directly from outside, only through nginx.

## Where things are

```
backend/
  Dockerfile           how the backend container is built
  entrypoint.sh        what runs when the container starts: update the database, then start the server
  requirements.txt     Python packages (exact versions)
  alembic/versions/    database change history (one file per change)
  app/
    main.py            creates the app and plugs in all the routes
    config.py          reads settings (like the database address) from environment variables
    db.py              connection to the database
    models.py          database tables, written as Python classes
    schemas.py         the shape of data going in and out (and the rules, e.g. password length)
    api/
      helpers.py       get_current_user(): "who is logged in?"
      fake.py          made-up test data (see "Fake endpoints" below)
      routes/          the endpoints, one file per topic: auth, users, friends
```

## Why we did it this way

- **FastAPI**: the subject gives points for using a backend framework. FastAPI also checks all input for us and builds the `/api/docs` page automatically.
- **async (`async def` and `await`)**: the whole backend is one program. While one request waits for the database, it handles other requests. Never put slow blocking code (like `time.sleep`) in an `async def`, because it freezes everyone.
- **Only one worker (one process)**: live chess games will be kept in memory. Two processes would each have their own separate copy of the games.
- **SQLAlchemy and Alembic**: see the next section.

## SQLAlchemy and Alembic (how we use the database)

Our data (users, games, friends) lives in **PostgreSQL**. PostgreSQL only understands SQL. These two tools let us work with it from Python, and keep everyone's database the same.

In one sentence each:
- **SQLAlchemy** is how our code **reads and writes data** (add a user, find a user, ...).
- **Alembic** is how the **tables themselves** get created and changed (new table, new column, ...).

Both read the same Python classes in `app/models.py`.

### SQLAlchemy

SQLAlchemy is an **ORM**: it connects database tables to Python classes.

- One table = one class in `app/models.py`, and each field in the class is a column.
- One row in the table = one object of that class.

So instead of writing SQL text, we work with objects:

```python
# Without SQLAlchemy: SQL written as text
await conn.execute("INSERT INTO users (email, display_name) VALUES ($1, $2)", email, name)

# With SQLAlchemy: plain Python objects
session.add(User(email=email, display_name=name))
await session.commit()
```

Why we use it:
- The subject gives **1 point** for using an ORM.
- Your editor catches typos: `User.emial` is an error right away. Inside an SQL string, the same typo only fails when the code runs.
- Values are always passed in safely, so SQL injection is hard to do by accident.
- We can still write plain SQL when that's easier: `text("SELECT ...")`, like `/api/health` in `main.py` does.

Files: `app/db.py` (the connection to the database) and `app/models.py` (the tables).

### Alembic

Our tables will change many times while we build the project: a new table for games, a new column, and so on. Alembic saves each change as a small file in `alembic/versions/`, called a **migration**. It's like a git commit, but for the table structure.

How it works:
- Each migration file has `upgrade()` (make the change) and `downgrade()` (undo it).
- Each migration points to the one before it, so together they form a chain: 1st → 2nd → 3rd...
- The database stores the ID of the last migration it ran, in a tiny table called `alembic_version`.
- `alembic upgrade head` runs every migration the database doesn't have yet. Our backend does this **automatically every time it starts** (see `entrypoint.sh`).

Why we use it:
- Everyone's database ends up with exactly the same tables, just by running `make`: yours, your teammates', and the evaluator's fresh copy.
- Existing data is kept. A migration changes the table instead of deleting it and making a new one.
- We don't write migration files by hand. Alembic compares `app/models.py` with the real database and writes the file for us. We only read it to check it.

Files: `alembic/env.py` (tells Alembic where the database is and where our table classes are) and `alembic/versions/` (the migrations).

To change a table, follow "Changing the database tables" below.

## Fake endpoints (important)

Most endpoints are **fake for now**. They have the correct URLs and data shapes, but they return made-up data from `app/api/fake.py`, and nothing is saved. This lets the frontend build its pages before the real code exists.

Every fake part is marked with a `# STUB` comment. To make an endpoint real, replace its body with real database code. To see what's still fake:

```bash
grep -rn "STUB" backend/app
```

Nothing marked `STUB` may be left when the project is evaluated.

Login is already real. Register or log in first; otherwise endpoints that need a user answer 401.

## Changing the database tables

1. Edit the classes in `app/models.py`.
2. Run `make` so the container gets your new code.
3. Create a change file (a "migration") inside the container:
   ```bash
   docker compose exec backend alembic revision --autogenerate -m "describe your change"
   ```
4. Copy the new file from the container into your folder:
   ```bash
   docker compose cp backend:/app/alembic/versions/. backend/alembic/versions/
   ```
5. Open the new file in `alembic/versions/` and check that it does what you expect.
6. Run `make` again. The backend applies the change automatically when it starts.
7. Commit the new file together with your `models.py` change.

## Useful commands

| What | Command |
|---|---|
| Start / rebuild everything (run it after every code change) | `make` |
| Stop everything | `make down` |
| Delete everything, including the database data | `make clean` |
| Restart only the backend (doesn't load code changes, use `make` for that) | `docker compose restart backend` |
| See backend errors | `docker compose logs backend --tail 20` |
| Look inside the database | `docker compose exec db psql -U chess` (use the user from `.env`) |
| Run the tests | `docker compose exec backend pytest -v` |

**The website shows "502 Bad Gateway"?** The backend crashed. Run the logs command above: the last line says why, usually a typo or a wrong import.

## What's done and what's next

Done:
- Docker setup, HTTPS through nginx, database connection
- `users` table + automatic database updates (Alembic)
- Fake endpoints for users, friends, games, stats
- Real register/login/logout (hashed passwords, login cookie) + automatic tests

Next:
- Fake live game over WebSockets (Socket.IO)
- The real chess game (moves checked on the server, reconnecting)

## Tests

The automatic tests are in `tests/`:
- Each `test_*.py` file checks one part. For example, `test_auth.py` covers register, login, logout and bad tokens.
- `configuration_tests.py` is the shared setup: the test database and the `client` fake browser. `pytest.ini` tells pytest to load it.

Run them while the app is running. Run `make` first so the tests use your latest code:

```bash
docker compose exec backend pytest -v
```

Every test should say `PASSED`.

- Tests use their own database, `chess_test`. It's created automatically and emptied before each test, so your real data is never touched.
- Run one file: `docker compose exec backend pytest -v tests/test_auth.py`
- Run one test by name: `docker compose exec backend pytest -v -k test_logout`
- To add a test, write a function whose name starts with `test_` in a `test_*.py` file. Give it a `client` parameter to get a fake browser that keeps cookies like a real one.