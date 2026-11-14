from fastapi import APIRouter, HTTPException, status

from app.api import fake
from app.schemas import GameDetail, LiveGame

router = APIRouter(prefix="/api/games", tags=["games"])


# List the games being played right now (for the "watch a game" page).
@router.get("/live")
async def live_games() -> list[LiveGame]:
    # STUB: real version asks the game manager which games are running
    return fake.LIVE_GAMES


# One finished game with all its moves. 404 if there's no game with this id.
@router.get("/{game_id}")
async def get_game(game_id: int) -> GameDetail:
    # STUB: real version loads the game from the database
    for game in fake.FINISHED_GAMES:
        if game.id == game_id:
            return game
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Game not found")