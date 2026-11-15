from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    display_name: Mapped[str] = mapped_column(String(20), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    avatar_path: Mapped[str | None] = mapped_column(String(255))
    elo: Mapped[int] = mapped_column(server_default="1200")
    intra_id: Mapped[int | None] = mapped_column(unique=True)
    totp_secret: Mapped[str | None] = mapped_column(String(64))
    totp_enabled: Mapped[bool] = mapped_column(server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    
class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    white_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    black_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    result: Mapped[str | None] = mapped_column(String(7))  # "1-0", "0-1", "1/2-1/2"; None while playing
    termination: Mapped[str | None] = mapped_column(String(30))  # "checkmate", "resignation", ...
    pgn: Mapped[str] = mapped_column(Text, server_default="")  # all the moves
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))