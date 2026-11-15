import chess

from app.live_games import RunningGame, ending_of, legal_move, pgn_of, state_of, whose_turn

FOOLS_MATE = ["f2f3", "e7e5", "g2g4", "d8h4"]  # the fastest checkmate: black wins
KNIGHTS_OUT_AND_BACK = ["g1f3", "g8f6", "f3g1", "f6g8"]  # back to the start position


def play(moves, fen=chess.STARTING_FEN):
    board = chess.Board(fen)
    for uci in moves:
        board.push_uci(uci)
    return board


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


# ---------- game endings ----------

def test_a_new_game_goes_on():
    assert ending_of(chess.Board()) is None


def test_checkmate():
    assert ending_of(play(FOOLS_MATE)) == ("0-1", "checkmate")


def test_stalemate():
    board = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")  # black to move, no legal move, not in check
    assert ending_of(board) == ("1/2-1/2", "stalemate")


def test_not_enough_pieces_to_mate():
    board = chess.Board("8/8/8/4k3/8/8/8/4K3 w - - 0 1")  # only the two kings
    assert ending_of(board) == ("1/2-1/2", "insufficient_material")


def test_threefold_repetition_only_once_it_really_happened():
    moves = KNIGHTS_OUT_AND_BACK * 2
    assert ending_of(play(moves[:-1])) is None  # one move before: not yet
    assert ending_of(play(moves)) == ("1/2-1/2", "threefold_repetition")


def test_fifty_moves_without_capture_or_pawn_move():
    board = chess.Board("8/8/8/4k3/8/8/8/R3K3 w - - 100 80")  # 100 half-moves = 50 each
    assert ending_of(board) == ("1/2-1/2", "fifty_moves")


def test_pgn():
    assert pgn_of(play(FOOLS_MATE), "0-1") == "1. f3 e5 2. g4 Qh4# 0-1"
    assert pgn_of(chess.Board(), "1-0") == "1-0"  # resigned before any move
