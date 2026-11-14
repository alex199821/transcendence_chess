from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api import fake
from app.api.helpers import get_current_user
from app.schemas import Login, Register, UserMe

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: Register) -> UserMe:
    # STUB: real version saves the user with a hashed password and sets the auth cookie
    return fake.ME.model_copy(update={"email": body.email, "display_name": body.display_name})


@router.post("/login")
async def login(body: Login) -> UserMe:
    # STUB: real version checks the password and sets the auth cookie
    return fake.ME


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout() -> None:
    # STUB: real version deletes the auth cookie
    return None


@router.get("/me")
async def me(user: Annotated[UserMe, Depends(get_current_user)]) -> UserMe:
    return user