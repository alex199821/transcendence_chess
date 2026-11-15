import asyncio
import random

import socketio
from starlette.requests import cookie_parser

from app.db import SessionLocal
from app.live_games import (
    RunningGame,
    ending_of,
    game_of,
    legal_move,
    other_player,
    pgn_of,
    queue,
    running_games,
    state_of,
    whose_turn,
)
from app.models import Game, User
from app.security import COOKIE_NAME, read_token
from datetime import UTC, datetime

sio = socketio.AsyncServer(async_mode="asgi")

# user id -> ids of that user's open connections (one per browser tab)
connections: dict[int, set[str]] = {}

# only one "find_game" at a time, so nobody gets paired twice
matchmaking_lock = asyncio.Lock()

# a player who leaves a running game has this long to come back, otherwise they lose
RECONNECT_SECONDS = 60

# user id -> timer that makes this player lose if they don't come back in time
leave_timers: dict[int, asyncio.Task] = {}

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
    if stop_leave_timer(user_id):  # was gone from a game and came back in time
        game = game_of(user_id)
        await sio.emit("opponent_back", {}, room=f"user:{other_player(game, user_id)}")

@sio.event
async def disconnect(sid):
    user_id = (await sio.get_session(sid))["user_id"]
    connections[user_id].discard(sid)
    if not connections[user_id]:
        del connections[user_id]
        if user_id in queue:
            queue.remove(user_id)
        game = game_of(user_id)
        if game is not None:
            leave_timers[user_id] = asyncio.create_task(lose_if_not_back(game, user_id))
            opponent_room = f"user:{other_player(game, user_id)}"
            await sio.emit("opponent_left", {"seconds": RECONNECT_SECONDS}, room=opponent_room)

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
    await sio.emit("live_games_changed", room="lobby")

@sio.event
async def cancel_search(sid):
    user_id = (await sio.get_session(sid))["user_id"]
    if user_id in queue:
        queue.remove(user_id)
        


async def send_to_players(game: RunningGame, event: str, data: dict) -> None:
    """Send to both players and to everyone watching the game."""
    await sio.emit(event, data, room=f"user:{game.white_id}")
    await sio.emit(event, data, room=f"user:{game.black_id}")
    await sio.emit(event, data, room=f"game:{game.id}")


async def reject(sid: str, reason: str) -> None:
    await sio.emit("move_rejected", {"reason": reason}, to=sid)


@sio.event
async def move(sid, uci=None):
    """A player moves, e.g. "e2e4" (from-square + to-square; "e7e8q" = pawn becomes a queen)."""
    user_id = (await sio.get_session(sid))["user_id"]
    game = game_of(user_id)
    if game is None:
        await reject(sid, "You are not in a game")
        return
    if whose_turn(game) != user_id:
        await reject(sid, "Not your turn")
        return
    chess_move = legal_move(game.board, uci)
    if chess_move is None:
        await reject(sid, "Illegal move")
        return

    game.board.push(chess_move)
    ending = ending_of(game.board)
    if ending is None:
        await send_to_players(game, "game_state", state_of(game))
    else:
        await finish_game(game, *ending)


@sio.event
async def resign(sid):
    user_id = (await sio.get_session(sid))["user_id"]
    game = game_of(user_id)
    if game is None:
        return
    result = "0-1" if user_id == game.white_id else "1-0"  # the other player wins
    await finish_game(game, result, "resignation")


async def finish_game(game: RunningGame, result: str, termination: str) -> None:
    """The game is over: free both players, save the result, tell both players."""
    del running_games[game.id]  # first, before any await: from now on nobody can move here
    stop_leave_timer(game.white_id)
    stop_leave_timer(game.black_id)
    
    async with SessionLocal() as session:
        row = await session.get(Game, game.id)
        row.result = result
        row.termination = termination
        row.pgn = pgn_of(game.board, result)
        row.ended_at = datetime.now(UTC)
        await session.commit()

    winner_id = {"1-0": game.white_id, "0-1": game.black_id}.get(result)  # None = draw
    await send_to_players(
        game,
        "game_over",
        {**state_of(game), "result": result, "termination": termination, "winner_id": winner_id},
    )
    await sio.close_room(f"game:{game.id}")  # spectators stop following this game
    await sio.emit("live_games_changed", room="lobby")
    

@sio.event
async def rejoin_game(sid):
    """The browser asks "am I in a game?" after (re)connecting. If yes, send the whole game."""
    user_id = (await sio.get_session(sid))["user_id"]
    game = game_of(user_id)
    if game is None:
        return
    async with SessionLocal() as session:
        white = await session.get(User, game.white_id)
        black = await session.get(User, game.black_id)
    info = {**state_of(game), "white": player_info(white), "black": player_info(black)}
    await sio.emit("game_resumed", info, to=sid)


async def lose_if_not_back(game: RunningGame, user_id: int) -> None:
    """Runs in the background after a player left a game. Cancelled if they come back."""
    await asyncio.sleep(RECONNECT_SECONDS)
    del leave_timers[user_id]  # this timer is done
    result = "0-1" if user_id == game.white_id else "1-0"  # the other player wins
    await finish_game(game, result, "abandoned")


def stop_leave_timer(user_id: int) -> bool:
    """Cancel this player's "come back or lose" timer. True if there was one."""
    timer = leave_timers.pop(user_id, None)
    if timer is None:
        return False
    timer.cancel()
    return True



# ---------- spectators ----------

def spectator_count(game_id: int) -> int:
    return len(list(sio.manager.get_participants("/", f"game:{game_id}")))


@sio.event
async def watch_game(sid, game_id=None):
    """Watch a running game: get the whole game now, then every move and the end."""
    game = running_games.get(game_id) if isinstance(game_id, int) else None
    if game is not None:
        async with SessionLocal() as session:
            white = await session.get(User, game.white_id)
            black = await session.get(User, game.black_id)
    if game is None or game.id not in running_games:  # not running, or ended while we loaded
        await sio.emit("watch_rejected", {"reason": "This game is not being played"}, to=sid)
        return
    await sio.enter_room(sid, f"game:{game.id}")
    info = {**state_of(game), "white": player_info(white), "black": player_info(black)}
    await sio.emit("watching", info, to=sid)


@sio.event
async def stop_watching(sid, game_id=None):
    await sio.leave_room(sid, f"game:{game_id}")


@sio.event
async def join_lobby(sid):
    """The browser shows the list of live games: tell it whenever a game starts or ends."""
    await sio.enter_room(sid, "lobby")


@sio.event
async def leave_lobby(sid):
    await sio.leave_room(sid, "lobby")