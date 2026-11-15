from dataclasses import dataclass, field

import chess


@dataclass
class RunningGame:
    id: int
    white_id: int
    black_id: int
    board: chess.Board = field(default_factory=chess.Board)


# game id -> a game being played right now
running_games: dict[int, RunningGame] = {}

# players who pressed "Play" and wait for an opponent
queue: list[int] = []


def game_of(user_id: int) -> RunningGame | None:
    """The game this user is playing right now, or None."""
    for game in running_games.values():
        if user_id in (game.white_id, game.black_id):
            return game
    return None