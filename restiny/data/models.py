from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class SQLModelBase(DeclarativeBase):
    pass


class SQLFolder(SQLModelBase):
    __tablename__ = 'folders'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey('folders.id'), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(),
        default=func.current_timestamp(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(),
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )


class SQLRequest(SQLModelBase):
    __tablename__ = 'requests'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    folder_id: Mapped[int] = mapped_column(
        ForeignKey('folders.id'), nullable=False
    )
    name: Mapped[str] = mapped_column(nullable=False)

    method: Mapped[str] = mapped_column(nullable=False)
    url: Mapped[str | None] = mapped_column(nullable=True)
    headers: Mapped[str | None] = mapped_column(nullable=True)
    params: Mapped[str | None] = mapped_column(nullable=True)

    body_enabled: Mapped[bool] = mapped_column(nullable=False)
    body_mode: Mapped[str] = mapped_column(nullable=False)
    body: Mapped[str | None] = mapped_column(nullable=True)

    auth_enabled: Mapped[bool] = mapped_column(nullable=False)
    auth_mode: Mapped[str] = mapped_column(nullable=False)
    auth: Mapped[str | None] = mapped_column(nullable=True)

    option_timeout: Mapped[float | None] = mapped_column(nullable=True)
    option_follow_redirects: Mapped[bool] = mapped_column(nullable=False)
    option_verify_ssl: Mapped[bool] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(),
        default=func.current_timestamp(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(),
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )


class SQLSettings(SQLModelBase):
    __tablename__ = 'settings'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    theme: Mapped[str] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(),
        default=func.current_timestamp(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(),
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )


class SQLEnvironment(SQLModelBase):
    __tablename__ = 'environments'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    variables: Mapped[str] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(),
        default=func.current_timestamp(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(),
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )
