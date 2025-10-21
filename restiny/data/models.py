from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class SQLModelBase(DeclarativeBase):
    pass


class SQLFolder(SQLModelBase):
    __tablename__ = 'folders'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column()
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey('folders.id'), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )


class SQLRequest(SQLModelBase):
    __tablename__ = 'requests'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    folder_id: Mapped[int] = mapped_column(
        ForeignKey('folders.id'), nullable=False
    )
    name: Mapped[str] = mapped_column()

    method: Mapped[str] = mapped_column()
    url: Mapped[str | None] = mapped_column()
    headers: Mapped[str | None] = mapped_column()
    params: Mapped[str | None] = mapped_column()

    body_enabled: Mapped[bool] = mapped_column()
    body_mode: Mapped[str] = mapped_column()
    body: Mapped[str | None] = mapped_column()

    auth_enabled: Mapped[bool] = mapped_column()
    auth_mode: Mapped[str] = mapped_column()
    auth: Mapped[str | None] = mapped_column()

    option_timeout: Mapped[float | None] = mapped_column()
    option_follow_redirects: Mapped[bool] = mapped_column()
    option_verify_ssl: Mapped[bool] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )
