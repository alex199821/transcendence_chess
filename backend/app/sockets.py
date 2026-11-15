import socketio
from starlette.requests import cookie_parser

from app.db import SessionLocal
from app.models import User
from app.security import COOKIE_NAME, read_token

sio = socketio.AsyncServer(async_mode="asgi")

# user id -> ids of that user's open connections (one per browser tab)
connections: dict[int, set[str]] = {}


def is_online(user_id: int) -> bool:
    return user_id in connections


@sio.event
async def connect(sid, environ, auth):
    cookies = cookie_parser(environ.get("HTTP_COOKIE", ""))
    user_id = read_token(cookies.get(COOKIE_NAME))
    if user_id is not None:
        async with SessionLocal() as session:
            if await session.get(User, user_id) is None:
                user_id = None
    if user_id is None:
        raise socketio.exceptions.ConnectionRefusedError("Not logged in")

    await sio.save_session(sid, {"user_id": user_id})
    await sio.enter_room(sid, f"user:{user_id}")
    connections.setdefault(user_id, set()).add(sid)


@sio.event
async def disconnect(sid):
    user_id = (await sio.get_session(sid))["user_id"]
    connections[user_id].discard(sid)
    if not connections[user_id]:
        del connections[user_id]