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


def whose_turn(game: RunningGame) -> int:
    """The id of the player who must move now."""
    return game.white_id if game.board.turn == chess.WHITE else game.black_id


def legal_move(board: chess.Board, uci) -> chess.Move | None:
    """The move if it's legal right now, otherwise None. uci looks like "e2e4" or "e7e8q"."""
    if not isinstance(uci, str):
        return None
    try:
        move = chess.Move.from_uci(uci)
    except ValueError:
        return None
    return move if move in board.legal_moves else None


def state_of(game: RunningGame) -> dict:
    """What the browser needs to draw the board."""
    board = game.board
    return {
        "game_id": game.id,
        "fen": board.fen(),
        "turn": "white" if board.turn == chess.WHITE else "black",
        "last_move": board.peek().uci() if board.move_stack else None,
    }


def ending_of(board: chess.Board) -> tuple[str, str] | None:
    """(result, how it ended) if the game is over, e.g. ("0-1", "checkmate"). None if it goes on."""
    outcome = board.outcome()  # checkmate, stalemate, not enough pieces to mate, ...
    if outcome is not None:
        return outcome.result(), outcome.termination.name.lower()
    if board.is_repetition(3):  # same position 3 times
        return "1/2-1/2", "threefold_repetition"
    if board.is_fifty_moves():  # 50 moves each without a capture or pawn move
        return "1/2-1/2", "fifty_moves"
    return None


def pgn_of(board: chess.Board, result: str) -> str:
    """All moves in standard chess notation, e.g. "1. f3 e5 2. g4 Qh4# 0-1"."""
    return f"{chess.Board().variation_san(board.move_stack)} {result}".strip()


def other_player(game: RunningGame, user_id: int) -> int:
    """The opponent of this player."""
    return game.black_id if user_id == game.white_id else game.white_id