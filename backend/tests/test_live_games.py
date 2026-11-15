import chess

from app.live_games import RunningGame, legal_move, state_of, whose_turn


def test_white_moves_first_then_black():
    game = RunningGame(1, white_id=10, black_id=20)
    assert whose_turn(game) == 10
    game.board.push_uci("e2e4")
    assert whose_turn(game) == 20


def test_legal_move():
    board = chess.Board()
    assert legal_move(board, "e2e4") == chess.Move.from_uci("e2e4")
    for bad in ["e2e5", "e7e5", "zzz", "", 123, None]:  # e7e5 is black's move, but it's white's turn
        assert legal_move(board, bad) is None


def test_promotion_needs_the_new_piece():
    board = chess.Board("8/4P3/8/8/8/8/8/4K2k w - - 0 1")  # white pawn on e7, about to reach e8
    assert legal_move(board, "e7e8") is None
    assert legal_move(board, "e7e8q") is not None


def test_state_of_a_new_game():
    assert state_of(RunningGame(5, white_id=1, black_id=2)) == {
        "game_id": 5,
        "fen": chess.STARTING_FEN,
        "turn": "white",
        "last_move": None,
    }
