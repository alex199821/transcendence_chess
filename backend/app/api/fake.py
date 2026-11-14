# STUB: fake data for the API contract. Delete this file once every endpoint is real.
from datetime import UTC, datetime

from app.schemas import (
    Achievement,
    FriendRequest,
    GameDetail,
    LeaderboardEntry,
    LiveGame,
    RatingPoint,
    UserMe,
    UserPublic,
    UserStats,
)

DEFAULT_AVATAR = "/avatars/default.png"

ME = UserMe(
    id=1,
    display_name="alex",
    avatar_url=DEFAULT_AVATAR,
    elo=1200,
    online=True,
    email="alex@example.com",
    totp_enabled=False,
    created_at=datetime(2026, 11, 1, tzinfo=UTC),
)

USERS: list[UserPublic] = [
    ME,
    UserPublic(id=2, display_name="magnus", avatar_url=DEFAULT_AVATAR, elo=1450, online=True),
    UserPublic(id=3, display_name="hikaru", avatar_url=DEFAULT_AVATAR, elo=1380, online=False),
]

# magnus is already your friend, hikaru sent you a request
FRIENDS: list[UserPublic] = [USERS[1]]

FRIEND_REQUESTS: list[FriendRequest] = [
    FriendRequest(id=1, from_user=USERS[2], to_user=ME, created_at=datetime(2026, 11, 10, tzinfo=UTC)),
]



# ---------- games ----------

# magnus vs hikaru is being played right now
LIVE_GAMES: list[LiveGame] = [
    LiveGame(
        id=10, white=USERS[1], black=USERS[2],
        started_at=datetime(2026, 11, 14, 18, 0, tzinfo=UTC), move_count=24, spectators=3,
    ),
]

# three finished games you played: one loss, one draw, one win
FINISHED_GAMES: list[GameDetail] = [
    GameDetail(
        id=1, white=ME, black=USERS[1], result="0-1", termination="checkmate",
        started_at=datetime(2026, 11, 11, 20, 0, tzinfo=UTC),
        ended_at=datetime(2026, 11, 11, 20, 2, tzinfo=UTC),
        pgn="1. f3 e5 2. g4 Qh4# 0-1",
    ),
    GameDetail(
        id=2, white=USERS[2], black=ME, result="1/2-1/2", termination="threefold_repetition",
        started_at=datetime(2026, 11, 12, 19, 0, tzinfo=UTC),
        ended_at=datetime(2026, 11, 12, 19, 5, tzinfo=UTC),
        pgn="1. Nf3 Nf6 2. Ng1 Ng8 3. Nf3 Nf6 4. Ng1 Ng8 1/2-1/2",
    ),
    GameDetail(
        id=3, white=ME, black=USERS[2], result="1-0", termination="resignation",
        started_at=datetime(2026, 11, 13, 18, 0, tzinfo=UTC),
        ended_at=datetime(2026, 11, 13, 18, 20, tzinfo=UTC),
        pgn="1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0",
    ),
]

# ---------- stats ----------

# the same made-up numbers are shown for every player
STATS = UserStats(
    wins=1, losses=1, draws=1, elo=1200,
    rating_history=[
        RatingPoint(date=datetime(2026, 11, 11, tzinfo=UTC), elo=1184),
        RatingPoint(date=datetime(2026, 11, 12, tzinfo=UTC), elo=1185),
        RatingPoint(date=datetime(2026, 11, 13, tzinfo=UTC), elo=1200),
    ],
)

ACHIEVEMENTS: list[Achievement] = [
    Achievement(code="first_game", name="First game", description="Finish your first game",
                unlocked_at=datetime(2026, 11, 11, tzinfo=UTC)),
    Achievement(code="first_win", name="First win", description="Win a game",
                unlocked_at=datetime(2026, 11, 13, tzinfo=UTC)),
    Achievement(code="checkmate", name="Checkmate!", description="Win a game by checkmate",
                unlocked_at=None),
    Achievement(code="ten_games", name="Regular", description="Finish 10 games",
                unlocked_at=None),
]

LEADERBOARD: list[LeaderboardEntry] = [
    LeaderboardEntry(rank=1, user=USERS[1], wins=12, losses=3, draws=1),
    LeaderboardEntry(rank=2, user=USERS[2], wins=9, losses=5, draws=2),
    LeaderboardEntry(rank=3, user=ME, wins=1, losses=1, draws=1),
]