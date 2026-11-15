import asyncio
import json
import time

import pytest
from sqlalchemy.exc import IntegrityError

from app import sockets
from app.live_games import queue
from app.models import Game
from app.security import COOKIE_NAME, create_token, read_token
from tests.configuration_tests import TestSession

SOCKET_URL = "/socket.io/?EIO=4&transport=polling"


class Tab:
    """One browser tab connected to Socket.IO.

    It uses Socket.IO's "polling" mode (plain HTTP requests), so our normal test client can do it.
    Messages look like in the browser console: "40" = connected, "44" = refused, '42["event", data]'.
    """

    def __init__(self, client, token):
        self.client = client
        self.user_id = read_token(token)
        self.headers = {"Cookie": f"{COOKIE_NAME}={token}"} if token else {}
        sid = json.loads(client.get(SOCKET_URL, headers=self.headers).text[1:])["sid"]
        self.url = f"{SOCKET_URL}&sid={sid}"
        self.send("40")
        self.answer = self.read()

    def send(self, packet):
        self.client.post(self.url, content=packet, headers=self.headers)

    def read(self):
        """Wait for the next message from the server."""
        return self.client.get(self.url, headers=self.headers).text

    def emit(self, event, *data):
        self.send("42" + json.dumps([event, *data]))

    def receive(self):
        """Wait for the next event. Returns (name, data)."""
        event, data = json.loads(self.read()[2:])
        return event, data

    def close(self):
        self.send("41")


def new_user(client, name):
    """Register a user and return their login token."""
    client.post("/api/auth/register", json={"email": f"{name}@test.com", "display_name": name, "password": "secret123"})
    token = client.cookies.get(COOKIE_NAME)
    client.cookies.clear()  # each Tab sends its own cookie
    return token


def wait_until(check):
    """Socket events run in the background: give the server up to 2 s to finish."""
    deadline = time.time() + 2
    while time.time() < deadline:
        if check():
            return True
        time.sleep(0.01)
    return False


def start_game(client):
    """Pair two new players. Returns (white tab, black tab)."""
    ann, bob = Tab(client, new_user(client, "ann")), Tab(client, new_user(client, "bob"))
    ann.emit("find_game")
    assert wait_until(lambda: queue == [ann.user_id])
    bob.emit("find_game")
    _, game = ann.receive()
    bob.receive()
    return (ann, bob) if game["white"]["id"] == ann.user_id else (bob, ann)


def load_game(game_id):
    async def load():
        async with TestSession() as session:
            return await session.get(Game, game_id)

    return asyncio.run(load())


# ---------- connecting ----------

@pytest.mark.parametrize("token", [None, "garbage", create_token(999)])  # 999 = no such user
def test_connect_needs_login(client, token):
    assert Tab(client, token).answer.startswith("44")


def test_logged_in_user_connects_and_is_online(client):
    tab = Tab(client, new_user(client, "ann"))
    assert tab.answer.startswith("40")
    assert sockets.is_online(tab.user_id)


def test_online_until_the_last_tab_closes(client):
    token = new_user(client, "ann")
    tab1, tab2 = Tab(client, token), Tab(client, token)
    tab1.close()
    assert wait_until(lambda: len(sockets.connections[tab1.user_id]) == 1)
    assert sockets.is_online(tab1.user_id)
    tab2.close()
    assert wait_until(lambda: not sockets.is_online(tab1.user_id))


# ---------- matchmaking ----------

def test_two_players_get_paired(client):
    ann, bob = Tab(client, new_user(client, "ann")), Tab(client, new_user(client, "bob"))
    ann.emit("find_game")
    assert wait_until(lambda: queue == [ann.user_id])
    bob.emit("find_game")

    event, game = ann.receive()
    assert event == "game_started"
    assert bob.receive() == (event, game)
    assert {game["white"]["id"], game["black"]["id"]} == {ann.user_id, bob.user_id}
    assert queue == []

    row = load_game(game["game_id"])  # saved in the database, not finished yet
    assert (row.white_id, row.black_id) == (game["white"]["id"], game["black"]["id"])
    assert row.result is None
    assert row.pgn == ""


def test_pressing_play_twice_is_ignored(client):
    ann = Tab(client, new_user(client, "ann"))
    ann.emit("find_game")
    ann.emit("find_game")
    assert wait_until(lambda: queue == [ann.user_id])
    time.sleep(0.1)
    assert queue == [ann.user_id]


def test_player_in_a_game_cannot_queue(client):
    white, _ = start_game(client)
    white.emit("find_game")
    time.sleep(0.1)
    assert queue == []


def test_cancel_search(client):
    ann = Tab(client, new_user(client, "ann"))
    ann.emit("find_game")
    assert wait_until(lambda: queue == [ann.user_id])
    ann.emit("cancel_search")
    assert wait_until(lambda: queue == [])


def test_leaving_the_site_leaves_the_queue(client):
    ann = Tab(client, new_user(client, "ann"))
    ann.emit("find_game")
    assert wait_until(lambda: queue == [ann.user_id])
    ann.close()
    assert wait_until(lambda: queue == [])


# ---------- moves ----------

def test_move_is_sent_to_both_players(client):
    white, black = start_game(client)
    white.emit("move", "e2e4")
    event, state = white.receive()
    assert event == "game_state"
    assert black.receive() == (event, state)
    assert state["turn"] == "black"
    assert state["last_move"] == "e2e4"
    assert state["fen"].startswith("rnbqkbnr/pppppppp/8/8/4P3/")


def test_not_your_turn(client):
    _, black = start_game(client)
    black.emit("move", "e7e5")
    assert black.receive() == ("move_rejected", {"reason": "Not your turn"})


@pytest.mark.parametrize("bad", ["e2e5", "zzz", 123, None])
def test_illegal_move(client, bad):
    white, _ = start_game(client)
    white.emit("move", bad)
    assert white.receive() == ("move_rejected", {"reason": "Illegal move"})


def test_move_when_not_in_a_game(client):
    cat = Tab(client, new_user(client, "cat"))
    cat.emit("move", "e2e4")
    assert cat.receive() == ("move_rejected", {"reason": "You are not in a game"})


def test_after_checkmate_no_move_is_legal(client):
    white, black = start_game(client)
    for tab, uci in [(white, "f2f3"), (black, "e7e5"), (white, "g2g4"), (black, "d8h4")]:  # Fool's mate
        tab.emit("move", uci)
        white.receive()
        black.receive()
    white.emit("move", "a2a3")
    assert white.receive() == ("move_rejected", {"reason": "Illegal move"})


# ---------- games table ----------

def test_game_needs_real_players(client):
    async def save():
        async with TestSession() as session:
            session.add(Game(white_id=998, black_id=999))  # no such users
            await session.commit()

    with pytest.raises(IntegrityError):
        asyncio.run(save())
