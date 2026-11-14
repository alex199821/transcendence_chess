from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes import auth, friends, games, stats, users
from app.db import get_session

app = FastAPI(
    title="Chess API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(friends.router)
app.include_router(games.router)
app.include_router(stats.router)

@app.get("/api/health")
async def health(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, str]:
    result = await session.execute(text("SELECT version()"))
    version = result.scalar_one()
    return {"status": "ok", "database": "ok", "postgres": version}