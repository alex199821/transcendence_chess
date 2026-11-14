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