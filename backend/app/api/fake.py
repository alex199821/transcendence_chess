# STUB: fake data for the API contract. Delete this file once every endpoint is real.
from datetime import UTC, datetime

from app.schemas import UserMe, UserPublic

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