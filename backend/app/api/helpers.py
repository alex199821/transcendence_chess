from app.api import fake
from app.schemas import UserMe


async def get_current_user() -> UserMe:
    """Who is making this request?"""
    # STUB: always the same fake user. The real version reads the auth cookie.
    return fake.ME