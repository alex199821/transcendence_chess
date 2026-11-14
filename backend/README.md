# Backend

The server side of our online chess game. It stores users and games in a database and answers the website's requests.

## Run it

From the project root (the folder above this one):

```bash
cp .env.example .env    # only the first time, then put your own password in .env
make                    # builds and starts everything
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
- **SQLAlchemy**: lets us use the database through Python classes instead of writing SQL by hand. The subject gives a point for using an ORM like this.
- **Alembic**: keeps track of changes to the database tables, so everyone's database (and the evaluator's) ends up the same. It runs automatically every time the backend starts.

## Fake endpoints (important)

Most endpoints are **fake for now**. They have the correct URLs and data shapes, but they return made-up data from `app/api/fake.py`, and nothing is saved. This lets the frontend build its pages before the real code exists.

Every fake part is marked with a `# STUB` comment. To make an endpoint real, replace its body with real database code. To see what's still fake:

```bash
grep -rn "STUB" backend/app
```

Nothing marked `STUB` may be left when the project is evaluated.

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

**The website shows "502 Bad Gateway"?** The backend crashed. Run the logs command above: the last line says why, usually a typo or a wrong import.

## What's done and what's next

Done:
- Docker setup, HTTPS through nginx, database connection
- `users` table + automatic database updates (Alembic)
- Fake endpoints for login/register, users, friends

Next:
- Fake endpoints for games and stats
- Fake live game over WebSockets (Socket.IO)
- Real login/register (password hashing, login cookie)
- The real chess game (moves checked on the server, clocks, reconnecting)
