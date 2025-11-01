import json
import sys
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from functools import wraps
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, InterfaceError, OperationalError

from restiny.data.db import DBManager
from restiny.data.models import SQLFolder, SQLRequest
from restiny.entities import Folder, Request


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


@dataclass
class RepoResp:
    status: RepoStatus = RepoStatus.OK
    data: Any = None

    @property
    def ok(self) -> bool:
        return self.status == RepoStatus.OK


class SQLRepoBase(ABC):
    def __init__(self, db_manager: DBManager):
        self.db_manager = db_manager

    @property
    @abstractmethod
    def _updatable_sql_fields(self) -> list[str]:
        pass


class FoldersSQLRepo(SQLRepoBase):
    @property
    def _updatable_sql_fields(self) -> list[str]:
        return [SQLFolder.parent_id.key, SQLFolder.name.key]

    @safe_repo
    def list_by_parent_id(self, parent_id: int) -> RepoResp:
        with self.db_manager.session_scope() as session:
            db_folders = session.scalars(
                select(SQLFolder)
                .where(SQLFolder.parent_id == parent_id)
                .order_by(SQLFolder.name.asc())
            ).all()
            folders = [
                self._folder_from_sql(db_folder) for db_folder in db_folders
            ]
            return RepoResp(data=folders)

    @safe_repo
    def list_roots(self) -> RepoResp:
        with self.db_manager.session_scope() as session:
            db_folders = session.scalars(
                select(SQLFolder)
                .where(SQLFolder.parent_id.is_(None))
                .order_by(SQLFolder.name.asc())
            ).all()
            folders = [
                self._folder_from_sql(db_folder) for db_folder in db_folders
            ]
            return RepoResp(data=folders)

    @safe_repo
    def get_by_id(self, id: int) -> RepoResp:
        with self.db_manager.session_scope() as session:
            db_folder = session.get(SQLFolder, id)
            if not db_folder:
                return RepoResp(status=RepoStatus.NOT_FOUND)

            folder = self._folder_from_sql(db_folder)
            return RepoResp(data=folder)

    @safe_repo
    def create(self, folder: Folder) -> RepoResp:
        with self.db_manager.session_scope() as session:
            db_folder = self._folder_to_sql(folder)
            session.add(db_folder)
            session.flush()
            new_folder = self._folder_from_sql(db_folder)
            return RepoResp(data=new_folder)

    @safe_repo
    def update(self, folder: Folder) -> RepoResp:
        with self.db_manager.session_scope() as session:
            db_folder = session.get(SQLFolder, folder.id)
            if not db_folder:
                return RepoResp(status=RepoStatus.NOT_FOUND)

            new_data = self._folder_to_sql(folder)
            for field in self._updatable_sql_fields:
                setattr(db_folder, field, getattr(new_data, field))

            session.flush()

            new_folder = self._folder_from_sql(db_folder)
            return RepoResp(data=new_folder)

    @safe_repo
    def delete_by_id(self, id: int) -> RepoResp:
        with self.db_manager.session_scope() as session:
            db_folder = session.get(SQLFolder, id)
            if not db_folder:
                return RepoResp(status=RepoStatus.NOT_FOUND)

            session.delete(db_folder)
            return RepoResp()

    def _folder_from_sql(self, sql_folder: SQLFolder) -> Folder:
        return Folder(
            id=sql_folder.id,
            parent_id=sql_folder.parent_id,
            name=sql_folder.name,
            created_at=sql_folder.created_at,
            updated_at=sql_folder.updated_at,
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
    def list_by_folder_id(self, folder_id: int) -> RepoResp:
        with self.db_manager.session_scope() as session:
            db_requests = session.scalars(
                select(SQLRequest)
                .where(SQLRequest.folder_id == folder_id)
                .order_by(SQLRequest.name.asc())
            ).all()
            requests = [
                self._request_from_sql(db_folder) for db_folder in db_requests
            ]
            return RepoResp(data=requests)

    @safe_repo
    def get_by_id(self, id: int) -> RepoResp:
        with self.db_manager.session_scope() as session:
            db_request = session.get(SQLRequest, id)

            if not db_request:
                return RepoResp(status=RepoStatus.NOT_FOUND)

            request = self._request_from_sql(db_request)
            return RepoResp(data=request)

    @safe_repo
    def create(self, request: Request) -> RepoResp:
        with self.db_manager.session_scope() as session:
            db_request = self._request_to_sql(request)
            session.add(db_request)
            session.flush()
            new_request = self._request_from_sql(db_request)
            return RepoResp(data=new_request)

    @safe_repo
    def update(self, request: Request) -> RepoResp:
        with self.db_manager.session_scope() as session:
            db_request = session.get(SQLRequest, request.id)
            if not db_request:
                return RepoResp(status=RepoStatus.NOT_FOUND)

            new_data = self._request_to_sql(request)
            for field in self._updatable_sql_fields:
                setattr(db_request, field, getattr(new_data, field))

            session.flush()

            new_request = self._request_from_sql(db_request)
            return RepoResp(data=new_request)

    @safe_repo
    def delete_by_id(self, id: int) -> RepoResp:
        with self.db_manager.session_scope() as session:
            db_request = session.get(SQLRequest, id)
            if not db_request:
                return RepoResp(status=RepoStatus.NOT_FOUND)

            session.delete(db_request)
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

    def _request_from_sql(self, sql_request: SQLRequest) -> Request:
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
            created_at=sql_request.created_at,
            updated_at=sql_request.updated_at,
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
