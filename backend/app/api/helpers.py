from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import User
from app.schemas import UserMe
from app.security import COOKIE_NAME, read_token

DEFAULT_AVATAR = "/avatars/default.png"


def to_user_me(user: User) -> UserMe:
    """Turns a database row into what the API sends back."""
    return UserMe(
        id=user.id,
        display_name=user.display_name,
        avatar_url=user.avatar_path or DEFAULT_AVATAR,
        elo=user.elo,
        online=True,
        email=user.email,
        totp_enabled=user.totp_enabled,
        created_at=user.created_at,
    )


async def get_current_user(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> UserMe:
    """Who is making this request? Answers 401 if nobody is logged in."""
    user_id = read_token(request.cookies.get(COOKIE_NAME))
    user = await session.get(User, user_id) if user_id is not None else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not logged in")
    return to_user_me(user)