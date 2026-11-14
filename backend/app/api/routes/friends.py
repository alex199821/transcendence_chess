from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api import fake
from app.api.helpers import get_current_user
from app.schemas import FriendRequest, FriendsOverview, NewFriendRequest, UserMe, UserPublic

router = APIRouter(prefix="/api/friends", tags=["friends"])

# STUB note: the fake lists never change, so accepting or removing has no lasting effect yet.


@router.get("")
async def get_friends(me: Annotated[UserMe, Depends(get_current_user)]) -> FriendsOverview:
    # STUB: real version loads friends and pending requests from the database
    return FriendsOverview(
        friends=fake.FRIENDS,
        incoming=[r for r in fake.FRIEND_REQUESTS if r.to_user.id == me.id],
        outgoing=[r for r in fake.FRIEND_REQUESTS if r.from_user.id == me.id],
    )


@router.post("/requests", status_code=status.HTTP_201_CREATED)
async def send_friend_request(
    body: NewFriendRequest, me: Annotated[UserMe, Depends(get_current_user)]
) -> FriendRequest:
    if body.user_id == me.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't add yourself")
    target = next((u for u in fake.USERS if u.id == body.user_id), None)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    # STUB: real version also rejects duplicates and users who are already friends
    return FriendRequest(id=99, from_user=me, to_user=target, created_at=datetime.now(UTC))


@router.post("/requests/{request_id}/accept")
async def accept_friend_request(
    request_id: int, me: Annotated[UserMe, Depends(get_current_user)]
) -> UserPublic:
    """Accept a request someone sent you. Returns your new friend."""
    for r in fake.FRIEND_REQUESTS:
        if r.id == request_id and r.to_user.id == me.id:
            return r.from_user  # STUB: real version saves the friendship
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Friend request not found")


@router.delete("/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_friend_request(
    request_id: int, me: Annotated[UserMe, Depends(get_current_user)]
) -> None:
    """Decline a request you got, or cancel one you sent."""
    for r in fake.FRIEND_REQUESTS:
        if r.id == request_id and me.id in (r.from_user.id, r.to_user.id):
            return None  # STUB: real version deletes the request
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Friend request not found")


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_friend(user_id: int, me: Annotated[UserMe, Depends(get_current_user)]) -> None:
    if any(f.id == user_id for f in fake.FRIENDS):
        return None  # STUB: real version deletes the friendship
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Not your friend")