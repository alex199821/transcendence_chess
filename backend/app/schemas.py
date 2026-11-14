from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# Reusable field rules (the frontend must use the same ones)
DisplayName = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{3,20}$")]
Password = Annotated[str, Field(min_length=8, max_length=128)]


class RequestBody(BaseModel):
    """Parent for everything the client sends: unknown fields are rejected."""

    model_config = ConfigDict(extra="forbid")


# ---------- what the client sends ----------

class Register(RequestBody):
    email: EmailStr
    display_name: DisplayName
    password: Password

    @field_validator("password")
    @classmethod
    def letter_and_digit(cls, value: str) -> str:
        if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
            raise ValueError("must contain at least one letter and one digit")
        return value


class Login(RequestBody):
    email: EmailStr
    password: str = Field(max_length=128)


class UserUpdate(RequestBody):
    display_name: DisplayName | None = None


# ---------- what the server sends back ----------

class UserPublic(BaseModel):
    """What anyone can see about a user."""

    id: int
    display_name: str
    avatar_url: str
    elo: int
    online: bool


class UserMe(UserPublic):
    """What you see about yourself: the public part plus private fields."""

    email: EmailStr
    totp_enabled: bool
    created_at: datetime
    
# ---------- friends ----------

class NewFriendRequest(RequestBody):
    """What the client sends to ask someone to be friends."""

    user_id: int


class FriendRequest(BaseModel):
    id: int
    from_user: UserPublic
    to_user: UserPublic
    created_at: datetime


class FriendsOverview(BaseModel):
    """Everything the friends page needs, in one response."""

    friends: list[UserPublic]
    incoming: list[FriendRequest]  # people who want to be your friend
    outgoing: list[FriendRequest]  # people you asked, still waiting
    


# ---------- games ----------

class LiveGame(BaseModel):
    """A game being played right now (for the list of games you can watch)."""

    id: int
    white: UserPublic
    black: UserPublic
    started_at: datetime
    move_count: int
    spectators: int  # how many people are watching


class GameSummary(BaseModel):
    """A finished game, as one line in someone's match history."""

    id: int
    white: UserPublic
    black: UserPublic
    result: str  # "1-0" = white won, "0-1" = black won, "1/2-1/2" = draw
    termination: str  # how it ended, e.g. "checkmate", "resignation", "timeout"
    ended_at: datetime


class GameDetail(GameSummary):
    """A finished game with all its moves (for replaying it)."""

    started_at: datetime
    pgn: str  # all the moves, in standard chess notation


# ---------- stats ----------

class RatingPoint(BaseModel):
    """A player's rating after one game (one dot on the progress chart)."""

    date: datetime
    elo: int


class UserStats(BaseModel):
    """A player's numbers for their profile page."""

    wins: int
    losses: int
    draws: int
    elo: int
    rating_history: list[RatingPoint]  # oldest first


class Achievement(BaseModel):
    """A badge a player can unlock."""

    code: str  # short fixed name, e.g. "first_win"
    name: str
    description: str
    unlocked_at: datetime | None  # None = not unlocked yet


class LeaderboardEntry(BaseModel):
    """One line on the leaderboard."""

    rank: int  # 1 = best
    user: UserPublic
    wins: int
    losses: int
    draws: int