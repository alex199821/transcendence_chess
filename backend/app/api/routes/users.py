from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api import fake
from app.api.helpers import get_current_user
from app.schemas import UserMe, UserPublic, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
async def search_users(search: Annotated[str, Query(max_length=20)] = "") -> list[UserPublic]:
    # STUB: real version searches the database
    return [u for u in fake.USERS if search.lower() in u.display_name.lower()]


@router.patch("/me")
async def update_me(
    body: UserUpdate, user: Annotated[UserMe, Depends(get_current_user)]
) -> UserMe:
    # STUB: real version saves the change (and rejects a display name that is taken)
    return user.model_copy(update=body.model_dump(exclude_none=True))


@router.get("/{user_id}")
async def get_user(user_id: int) -> UserPublic:
    # STUB: real version loads the user from the database
    for user in fake.USERS:
        if user.id == user_id:
            return user
    raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")