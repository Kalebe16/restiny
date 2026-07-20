from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class SQLModelBase(DeclarativeBase):
    pass


class SQLFolder(SQLModelBase):
    __tablename__ = 'folders'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey('folders.id'), nullable=True
    )
    headers: Mapped[str] = mapped_column(nullable=False, default='[]')
    auth_mode: Mapped[str] = mapped_column(nullable=False, default='basic')
    auth: Mapped[str] = mapped_column(
        nullable=False, default='{{"username":"","password":""}}'
    )
    documentation: Mapped[str] = mapped_column(nullable=False, default='')
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
    uuid: Mapped[str] = mapped_column(nullable=False)
    folder_id: Mapped[int] = mapped_column(
        ForeignKey('folders.id'), nullable=True
    )
    name: Mapped[str] = mapped_column(nullable=False)

    method: Mapped[str] = mapped_column(nullable=False, default='GET')
    url: Mapped[str] = mapped_column(nullable=False, default='')
    headers: Mapped[str] = mapped_column(nullable=False, default='[]')
    params: Mapped[str] = mapped_column(nullable=False, default='[]')

    body_enabled: Mapped[bool] = mapped_column(nullable=False, default=False)
    body_mode: Mapped[str] = mapped_column(nullable=False, default='raw')
    body: Mapped[str] = mapped_column(
        nullable=False, default='{{"language":"plaintext","value":""}}'
    )

    auth_enabled: Mapped[bool] = mapped_column(nullable=False, default=False)
    auth_mode: Mapped[str] = mapped_column(nullable=False, default='inherited')
    auth: Mapped[str | None] = mapped_column(nullable=True)

    option_timeout: Mapped[float | None] = mapped_column(
        nullable=True, default=5.5
    )
    option_follow_redirects: Mapped[bool] = mapped_column(
        nullable=False, default=True
    )
    option_verify_ssl: Mapped[bool] = mapped_column(
        nullable=False, default=True
    )
    option_attach_cookies: Mapped[bool] = mapped_column(
        nullable=False, default=True
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


class SQLSettings(SQLModelBase):
    __tablename__ = 'settings'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    theme: Mapped[str] = mapped_column(nullable=False)
    accent_color: Mapped[str] = mapped_column(nullable=False)

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
