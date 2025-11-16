import json
import sys
import traceback
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from datetime import UTC
from enum import StrEnum
from functools import wraps
from typing import Generic, TypeVar

from sqlalchemy import case, select
from sqlalchemy.exc import IntegrityError, InterfaceError, OperationalError
from sqlalchemy.orm import Session

from restiny.data.db import DBManager
from restiny.data.models import (
    SQLEnvironment,
    SQLFolder,
    SQLRequest,
    SQLSettings,
)
from restiny.entities import Environment, Folder, Request, Settings


def safe_repo(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except (
            InterfaceError,
            OperationalError,
        ):
            traceback.print_exc(file=sys.stderr)
            return RepoResp(status=RepoStatus.DB_ERROR)

        except IntegrityError as error:
            error_msg = str(error)
            if 'UNIQUE' in str(error_msg):
                return RepoResp(status=RepoStatus.DUPLICATED)

            traceback.print_exc(file=sys.stderr)
            return RepoResp(status=RepoStatus.DB_ERROR)

    return wrapper


class RepoStatus(StrEnum):
    OK = 'ok'
    NOT_FOUND = 'not_found'
    DUPLICATED = 'duplicated'
    DB_ERROR = 'db_error'


T = TypeVar('T')


@dataclass
class RepoResp(Generic[T]):
    status: RepoStatus = RepoStatus.OK
    data: T | None = None

    @property
    def ok(self) -> bool:
        return self.status == RepoStatus.OK


class SQLRepoBase(ABC):
    def __init__(self, db_manager: DBManager):
        self.db_manager = db_manager

    @contextmanager
    def _ensure_session(
        self, existing_session: Session | None
    ) -> Iterator[Session]:
        if existing_session:
            with nullcontext(existing_session) as session:
                yield session
        else:
            with self.db_manager.session_scope() as session:
                yield session

    @property
    @abstractmethod
    def _updatable_sql_fields(self) -> list[str]:
        pass


class FoldersSQLRepo(SQLRepoBase):
    @property
    def _updatable_sql_fields(self) -> list[str]:
        return [SQLFolder.parent_id.key, SQLFolder.name.key]

    @safe_repo
    def get_by_parent_id(
        self, parent_id: int, session: Session | None = None
    ) -> RepoResp[list[Folder]]:
        with self._ensure_session(session) as session:
            sql_folders = session.scalars(
                select(SQLFolder)
                .where(SQLFolder.parent_id == parent_id)
                .order_by(SQLFolder.name.asc())
            ).all()
            folders = [
                self._sql_to_folder(sql_folder) for sql_folder in sql_folders
            ]
            return RepoResp(data=folders)

    @safe_repo
    def get_roots(
        self, session: Session | None = None
    ) -> RepoResp[list[Folder]]:
        with self._ensure_session(session) as session:
            sql_folders = session.scalars(
                select(SQLFolder)
                .where(SQLFolder.parent_id.is_(None))
                .order_by(SQLFolder.name.asc())
            ).all()
            folders = [
                self._sql_to_folder(sql_folder) for sql_folder in sql_folders
            ]
            return RepoResp(data=folders)

    @safe_repo
    def get_by_id(
        self, id: int, session: Session | None = None
    ) -> RepoResp[Folder]:
        with self._ensure_session(session) as session:
            sql_folder = session.get(SQLFolder, id)
            if not sql_folder:
                return RepoResp(status=RepoStatus.NOT_FOUND)

            folder = self._sql_to_folder(sql_folder)
            return RepoResp(data=folder)

    @safe_repo
    def create(
        self, folder: Folder, session: Session | None = None
    ) -> RepoResp[Folder]:
        with self._ensure_session(session) as session:
            sql_folder = self._folder_to_sql(folder)
            session.add(sql_folder)
            session.flush()
            new_folder = self._sql_to_folder(sql_folder)
            return RepoResp(data=new_folder)

    @safe_repo
    def update(
        self, folder: Folder, session: Session | None = None
    ) -> RepoResp[Folder]:
        with self._ensure_session(session) as session:
            sql_folder = session.get(SQLFolder, folder.id)
            if not sql_folder:
                return RepoResp(status=RepoStatus.NOT_FOUND)

            new_data = self._folder_to_sql(folder)
            for field in self._updatable_sql_fields:
                setattr(sql_folder, field, getattr(new_data, field))

            session.flush()

            new_folder = self._sql_to_folder(sql_folder)
            return RepoResp(data=new_folder)

    @safe_repo
    def delete_by_id(
        self, id: int, session: Session | None = None
    ) -> RepoResp[None]:
        with self._ensure_session(session) as session:
            sql_folder = session.get(SQLFolder, id)
            if not sql_folder:
                return RepoResp(status=RepoStatus.NOT_FOUND)

            session.delete(sql_folder)
            return RepoResp()

    def _sql_to_folder(self, sql_folder: SQLFolder) -> Folder:
        return Folder(
            id=sql_folder.id,
            parent_id=sql_folder.parent_id,
            name=sql_folder.name,
            created_at=sql_folder.created_at.replace(tzinfo=UTC),
            updated_at=sql_folder.updated_at.replace(tzinfo=UTC),
        )

    def _folder_to_sql(self, folder: Folder) -> SQLFolder:
        return SQLFolder(
            id=folder.id,
            parent_id=folder.parent_id,
            name=folder.name,
            created_at=folder.created_at,
            updated_at=folder.updated_at,
        )


class RequestsSQLRepo(SQLRepoBase):
    @safe_repo
    def get_by_folder_id(
        self, folder_id: int, session: Session | None = None
    ) -> RepoResp[list[Request]]:
        with self._ensure_session(session) as session:
            sql_requests = session.scalars(
                select(SQLRequest)
                .where(SQLRequest.folder_id == folder_id)
                .order_by(SQLRequest.name.asc())
            ).all()
            requests = [
                self._sql_to_request(sql_folder) for sql_folder in sql_requests
            ]
            return RepoResp(data=requests)

    @safe_repo
    def get_by_id(
        self, id: int, session: Session | None = None
    ) -> RepoResp[Request]:
        with self._ensure_session(session) as session:
            sql_request = session.get(SQLRequest, id)

            if not sql_request:
                return RepoResp(status=RepoStatus.NOT_FOUND)

            request = self._sql_to_request(sql_request)
            return RepoResp(data=request)

    @safe_repo
    def create(
        self, request: Request, session: Session | None = None
    ) -> RepoResp[Request]:
        with self._ensure_session(session) as session:
            sql_request = self._request_to_sql(request)
            session.add(sql_request)
            session.flush()
            new_request = self._sql_to_request(sql_request)
            return RepoResp(data=new_request)

    @safe_repo
    def update(
        self, request: Request, session: Session | None = None
    ) -> RepoResp[Request]:
        with self._ensure_session(session) as session:
            sql_request = session.get(SQLRequest, request.id)
            if not sql_request:
                return RepoResp(status=RepoStatus.NOT_FOUND)

            new_data = self._request_to_sql(request)
            for field in self._updatable_sql_fields:
                setattr(sql_request, field, getattr(new_data, field))

            session.flush()

            new_request = self._sql_to_request(sql_request)
            return RepoResp(data=new_request)

    @safe_repo
    def delete_by_id(
        self, id: int, session: Session | None = None
    ) -> RepoResp[None]:
        with self._ensure_session(session) as session:
            sql_request = session.get(SQLRequest, id)
            if not sql_request:
                return RepoResp(status=RepoStatus.NOT_FOUND)

            session.delete(sql_request)
            return RepoResp()

    @property
    def _updatable_sql_fields(self) -> list[str]:
        return [
            SQLRequest.folder_id.key,
            SQLRequest.name.key,
            SQLRequest.method.key,
            SQLRequest.url.key,
            SQLRequest.headers.key,
            SQLRequest.params.key,
            SQLRequest.body_enabled.key,
            SQLRequest.body_mode.key,
            SQLRequest.body.key,
            SQLRequest.auth_enabled.key,
            SQLRequest.auth_mode.key,
            SQLRequest.auth.key,
            SQLRequest.option_timeout.key,
            SQLRequest.option_follow_redirects.key,
            SQLRequest.option_verify_ssl.key,
        ]

    def _sql_to_request(self, sql_request: SQLRequest) -> Request:
        return Request(
            id=sql_request.id,
            folder_id=sql_request.folder_id,
            name=sql_request.name,
            method=sql_request.method,
            url=sql_request.url,
            headers=json.loads(sql_request.headers),
            params=json.loads(sql_request.params),
            body_enabled=sql_request.body_enabled,
            body_mode=sql_request.body_mode,
            body=json.loads(sql_request.body) if sql_request.body else None,
            auth_enabled=sql_request.auth_enabled,
            auth_mode=sql_request.auth_mode,
            auth=json.loads(sql_request.auth) if sql_request.auth else None,
            options=Request.Options(
                timeout=sql_request.option_timeout,
                follow_redirects=sql_request.option_follow_redirects,
                verify_ssl=sql_request.option_verify_ssl,
            ),
            created_at=sql_request.created_at.replace(tzinfo=UTC),
            updated_at=sql_request.updated_at.replace(tzinfo=UTC),
        )

    def _request_to_sql(self, request: Request) -> SQLRequest:
        return SQLRequest(
            id=request.id,
            folder_id=request.folder_id,
            name=request.name,
            method=request.method,
            url=request.url,
            headers=json.dumps(
                [header.model_dump() for header in request.headers]
            ),
            params=json.dumps(
                [param.model_dump() for param in request.params]
            ),
            body_enabled=request.body_enabled,
            body_mode=request.body_mode,
            body=json.dumps(request.body.model_dump(), default=str)
            if request.body
            else None,
            auth_enabled=request.auth_enabled,
            auth_mode=request.auth_mode,
            auth=json.dumps(request.auth.model_dump(), default=str)
            if request.auth
            else None,
            option_timeout=request.options.timeout,
            option_follow_redirects=request.options.follow_redirects,
            option_verify_ssl=request.options.verify_ssl,
            created_at=request.created_at,
            updated_at=request.updated_at,
        )


class SettingsSQLRepo(SQLRepoBase):
    @safe_repo
    def get(self, session: Session | None = None) -> RepoResp[Settings]:
        with self._ensure_session(session) as session:
            sql_settings = session.scalar(select(SQLSettings).limit(1))

            if not sql_settings:
                return RepoResp(data=Settings())

            settings = self._sql_to_settings(sql_settings)
            return RepoResp(data=settings)

    @safe_repo
    def set(
        self, settings: Settings, session: Session | None = None
    ) -> RepoResp[Settings]:
        with self._ensure_session(session) as session:
            sql_settings = session.scalar(select(SQLSettings).limit(1))

            if not sql_settings:
                # create
                sql_settings = self._settings_to_sql(settings=settings)
                session.add(sql_settings)
                session.flush()
                new_settings = self._sql_to_settings(sql_settings=sql_settings)
                return RepoResp(data=new_settings)
            else:
                # update
                new_data = self._settings_to_sql(settings=settings)
                for field in self._updatable_sql_fields:
                    setattr(sql_settings, field, getattr(new_data, field))
                session.flush()
                new_settings = self._sql_to_settings(sql_settings=sql_settings)
                return RepoResp(data=new_settings)

    @property
    def _updatable_sql_fields(self) -> list[str]:
        return [SQLSettings.theme.key]

    def _sql_to_settings(self, sql_settings: SQLSettings) -> Settings:
        return Settings(
            id=sql_settings.id,
            theme=sql_settings.theme,
            created_at=sql_settings.created_at.replace(tzinfo=UTC),
            updated_at=sql_settings.updated_at.replace(tzinfo=UTC),
        )

    def _settings_to_sql(self, settings: Settings) -> SQLSettings:
        return SQLSettings(
            id=settings.id,
            theme=settings.theme,
            created_at=settings.created_at,
            updated_at=settings.updated_at,
        )


class EnvironmentsSQLRepo(SQLRepoBase):
    @safe_repo
    def get_by_id(
        self, id: int, session: Session | None = None
    ) -> RepoResp[Environment]:
        with self._ensure_session(session) as session:
            sql_environment = session.get(SQLEnvironment, id)

            if not sql_environment:
                return RepoResp(status=RepoStatus.NOT_FOUND)

            environment = self._sql_to_environment(sql_environment)
            return RepoResp(data=environment)

    @safe_repo
    def get_by_name(
        self, name: str, session: Session | None = None
    ) -> RepoResp[Environment]:
        with self._ensure_session(session) as session:
            sql_environment = session.scalar(
                select(SQLEnvironment).where(SQLEnvironment.name == name)
            )

            if not sql_environment:
                return RepoResp(status=RepoStatus.NOT_FOUND)

            environment = self._sql_to_environment(sql_environment)
            return RepoResp(data=environment)

    @safe_repo
    def get_all(
        self, session: Session | None = None
    ) -> RepoResp[list[Environment]]:
        with self._ensure_session(session) as session:
            sql_envs = session.scalars(
                select(SQLEnvironment).order_by(
                    case((SQLEnvironment.name == 'global', 0), else_=1),
                    SQLEnvironment.name.asc(),
                )
            )
            envs = [self._sql_to_environment(sql_env) for sql_env in sql_envs]
            return RepoResp(data=envs)

    @safe_repo
    def create(
        self, environment: Environment, session: Session | None = None
    ) -> RepoResp[Environment]:
        with self._ensure_session(session) as session:
            sql_env = self._environment_to_sql(environment)
            session.add(sql_env)
            session.flush()
            new_env = self._sql_to_environment(sql_env)
            return RepoResp(data=new_env)

    @safe_repo
    def update(
        self, environment: Environment, session: Session | None = None
    ) -> RepoResp[Environment]:
        with self._ensure_session(session) as session:
            sql_environment = session.get(SQLEnvironment, environment.id)
            if not sql_environment:
                return RepoResp(status=RepoStatus.NOT_FOUND)

            new_data = self._environment_to_sql(environment)
            for field in self._updatable_sql_fields:
                setattr(sql_environment, field, getattr(new_data, field))

            session.flush()

            new_environment = self._sql_to_environment(sql_environment)
            return RepoResp(data=new_environment)

    @safe_repo
    def delete_by_id(
        self, id: int, session: Session | None = None
    ) -> RepoResp[None]:
        with self._ensure_session(session) as session:
            sql_environment = session.get(SQLEnvironment, id)
            if not sql_environment:
                return RepoResp(status=RepoStatus.NOT_FOUND)

            session.delete(sql_environment)
            return RepoResp()

    @property
    def _updatable_sql_fields(self) -> list[str]:
        return [SQLEnvironment.name.key, SQLEnvironment.variables.key]

    def _sql_to_environment(
        self, sql_environment: SQLEnvironment
    ) -> Environment:
        return Environment(
            id=sql_environment.id,
            name=sql_environment.name,
            variables=json.loads(sql_environment.variables),
            created_at=sql_environment.created_at.replace(tzinfo=UTC),
            updated_at=sql_environment.updated_at.replace(tzinfo=UTC),
        )

    def _environment_to_sql(self, environment: Environment) -> SQLEnvironment:
        return SQLEnvironment(
            id=environment.id,
            name=environment.name,
            variables=json.dumps(
                [variable.model_dump() for variable in environment.variables]
            ),
            created_at=environment.created_at,
            updated_at=environment.updated_at,
        )
