from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api import fake
from app.schemas import Achievement, GameSummary, LeaderboardEntry, UserStats

router = APIRouter(prefix="/api", tags=["stats"])


# Stop with 404 if there's no user with this id (used by the endpoints below).
def check_user_exists(user_id: int) -> None:
    if not any(u.id == user_id for u in fake.USERS):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")


# A player's finished games, newest first, 20 per page: /api/users/1/games?page=2
@router.get("/users/{user_id}/games")
async def match_history(
    user_id: int, page: Annotated[int, Query(ge=1)] = 1
) -> list[GameSummary]:
    check_user_exists(user_id)
    # STUB: real version loads this player's games from the database
    games = [g for g in fake.FINISHED_GAMES if user_id in (g.white.id, g.black.id)]
    games.sort(key=lambda g: g.ended_at, reverse=True)  # newest first
    start = (page - 1) * 20
    return games[start : start + 20]


# A player's wins, losses, draws, rating and rating history.
@router.get("/users/{user_id}/stats")
async def user_stats(user_id: int) -> UserStats:
    check_user_exists(user_id)
    # STUB: real version counts this player's games in the database
    return fake.STATS


# All achievements, with the date each one was unlocked (None = still locked).
@router.get("/users/{user_id}/achievements")
async def user_achievements(user_id: int) -> list[Achievement]:
    check_user_exists(user_id)
    # STUB: real version loads this player's unlocked achievements from the database
    return fake.ACHIEVEMENTS


# The best players, highest rating first.
@router.get("/leaderboard")
async def leaderboard() -> list[LeaderboardEntry]:
    # STUB: real version sorts all players by rating
    return fake.LEADERBOARD