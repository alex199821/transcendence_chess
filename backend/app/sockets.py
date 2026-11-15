import asyncio
import random

import socketio
from starlette.requests import cookie_parser

from app.db import SessionLocal
from app.live_games import RunningGame, game_of, queue, running_games
from app.models import Game, User
from app.security import COOKIE_NAME, read_token

sio = socketio.AsyncServer(async_mode="asgi")

# user id -> ids of that user's open connections (one per browser tab)
connections: dict[int, set[str]] = {}

# only one "find_game" at a time, so nobody gets paired twice
matchmaking_lock = asyncio.Lock()


def is_online(user_id: int) -> bool:
    return user_id in connections


def player_info(user: User) -> dict:
    return {"id": user.id, "display_name": user.display_name, "elo": user.elo}


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
        if user_id in queue:
            queue.remove(user_id)


@sio.event
async def find_game(sid):
    """The player pressed "Play": wait for an opponent, or start a game with the one waiting."""
    user_id = (await sio.get_session(sid))["user_id"]
    async with matchmaking_lock:
        if user_id in queue or game_of(user_id) is not None:
            return
        if not queue:
            queue.append(user_id)
            return

        players = [queue.pop(0), user_id]
        random.shuffle(players)
        white_id, black_id = players
        async with SessionLocal() as session:
            game = Game(white_id=white_id, black_id=black_id)
            session.add(game)
            await session.commit()
            white = await session.get(User, white_id)
            black = await session.get(User, black_id)
        running_games[game.id] = RunningGame(game.id, white_id, black_id)

    info = {"game_id": game.id, "white": player_info(white), "black": player_info(black)}
    await sio.emit("game_started", info, room=f"user:{white_id}")
    await sio.emit("game_started", info, room=f"user:{black_id}")


@sio.event
async def cancel_search(sid):
    user_id = (await sio.get_session(sid))["user_id"]
    if user_id in queue:
        queue.remove(user_id)