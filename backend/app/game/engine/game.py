 -import chess

class ChessGame:
    def __init__(self) -> None:
        self.board = chess.Board()

    def legal_moves_from(self, square: str) -> list[str]:
        sq = chess.parse_square(square)
        return [
            chess.square_name(m.to_square)
            for m in self.board.legal_moves
            if m.from_square == sq
        ]

    def apply_move(self, from_sq: str, to_sq: str) -> bool:
        move = chess.Move(
            chess.parse_square(from_sq),
            chess.parse_square(to_sq),
        )
        # handle promotion later; for now reject if not legal
        if move not in self.board.legal_moves:
            return False
        self.board.push(move)
        return True

    def fen(self) -> str:
        return self.board.fen()

    def status(self) -> str:
        if self.board.is_checkmate():
            return "checkmate"
        if self.board.is_stalemate():
            return "stalemate"
        if self.board.is_check():
            return "check"
        return "ok"

    def turn(self) -> str:
        return "white" if self.board.turn == chess.WHITE else "black"