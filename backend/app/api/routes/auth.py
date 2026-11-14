from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.helpers import get_current_user, to_user_me
from app.db import get_session
from app.models import User
from app.schemas import Login, Register, UserMe
from app.security import COOKIE_NAME, TOKEN_LIFETIME, create_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def set_login_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        COOKIE_NAME,
        create_token(user_id),
        max_age=int(TOKEN_LIFETIME.total_seconds()),
        httponly=True,
        secure=True,
        samesite="lax",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: Register, response: Response, session: Annotated[AsyncSession, Depends(get_session)]
) -> UserMe:
    email = body.email.lower()
    taken = await session.scalar(
        select(User).where(or_(User.email == email, User.display_name == body.display_name))
    )
    if taken is not None:
        field = "Email" if taken.email == email else "Display name"
        raise HTTPException(status.HTTP_409_CONFLICT, f"{field} is already taken")

    user = User(email=email, display_name=body.display_name, password_hash=hash_password(body.password))
    session.add(user)
    await session.commit()
    set_login_cookie(response, user.id)
    return to_user_me(user)


@router.post("/login")
async def login(
    body: Login, response: Response, session: Annotated[AsyncSession, Depends(get_session)]
) -> UserMe:
    user = await session.scalar(select(User).where(User.email == body.email.lower()))
    if (
        user is None
        or user.password_hash is None  # accounts made with "Log in with 42" have no password
        or not verify_password(body.password, user.password_hash)
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong email or password")
    set_login_cookie(response, user.id)
    return to_user_me(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, httponly=True, secure=True, samesite="lax")


@router.get("/me")
async def me(user: Annotated[UserMe, Depends(get_current_user)]) -> UserMe:
    return user