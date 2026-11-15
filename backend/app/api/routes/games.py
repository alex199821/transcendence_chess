from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import fake
from app.api.helpers import to_user_public
from app.db import get_session
from app.live_games import running_games
from app.models import Game, User
from app.schemas import GameDetail, LiveGame
from app.sockets import spectator_count

router = APIRouter(prefix="/api/games", tags=["games"])


# List the games being played right now (for the "watch a game" page).
@router.get("/live")
async def live_games(session: Annotated[AsyncSession, Depends(get_session)]) -> list[LiveGame]:
    running = dict(running_games)  # a copy: games may end while we wait for the database
    rows = (await session.scalars(select(Game).where(Game.id.in_(list(running))).order_by(Game.started_at))).all()
    player_ids = [row.white_id for row in rows] + [row.black_id for row in rows]
    users = {user.id: user for user in await session.scalars(select(User).where(User.id.in_(player_ids)))}
    return [
        LiveGame(
            id=row.id,
            white=to_user_public(users[row.white_id]),
            black=to_user_public(users[row.black_id]),
            started_at=row.started_at,
            move_count=len(running[row.id].board.move_stack),
            spectators=spectator_count(row.id),
        )
        for row in rows
    ]


# One finished game with all its moves. 404 if there's no game with this id.
@router.get("/{game_id}")
async def get_game(game_id: int) -> GameDetail:
    # STUB: real version loads the game from the database
    for game in fake.FINISHED_GAMES:
        if game.id == game_id:
            return game
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Game not found")