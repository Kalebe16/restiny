import json
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import httpx
from pydantic import BaseModel, field_validator
from pydantic import Field as _Field
from pydantic_core.core_schema import ValidationInfo

from restiny import httpx_auths
from restiny.enums import (
    AuthMode,
    BodyMode,
    BodyRawLanguage,
    ContentType,
    HTTPMethod,
)
from restiny.utils import build_curl_cmd


class Folder(BaseModel):
    id: int | None = None
    name: str
    parent_id: int | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None


class Request(BaseModel):
    class Header(BaseModel):
        enabled: bool
        key: str
        value: str

    class Param(BaseModel):
        enabled: bool
        key: str
        value: str

    class RawBody(BaseModel):
        language: BodyRawLanguage
        value: str

    class FileBody(BaseModel):
        file: Path | None

    class UrlEncodedFormBody(BaseModel):
        class Field(BaseModel):
            enabled: bool
            key: str
            value: str

        fields: list[Field]

    class MultipartFormBody(BaseModel):
        class Field(BaseModel):
            value_kind: Literal['text', 'file']
            enabled: bool
            key: str
            value: str | Path | None

            @field_validator('value', mode='before')
            @classmethod
            def validate_value(cls, value: Any, info: ValidationInfo):
                if value is None:
                    return None

                kind = info.data.get('value_kind')
                if kind == 'file':
                    return Path(value)
                elif kind == 'text':
                    return str(value)

        fields: list[Field]

    class BasicAuth(BaseModel):
        username: str
        password: str

    class BearerAuth(BaseModel):
        token: str

    class ApiKeyAuth(BaseModel):
        key: str
        value: str
        where: Literal['header', 'param']

    class DigestAuth(BaseModel):
        username: str
        password: str

    class Options(BaseModel):
        timeout: float = 5.5
        follow_redirects: bool = True
        verify_ssl: bool = True

    id: int | None = None
    folder_id: int
    name: str

    method: HTTPMethod = HTTPMethod.GET
    url: str = ''
    headers: list[Header] = _Field(default_factory=list)
    params: list[Param] = _Field(default_factory=list)

    body_enabled: bool = False
    body_mode: str = BodyMode.RAW
    body: (
        RawBody | FileBody | UrlEncodedFormBody | MultipartFormBody | None
    ) = None

    auth_enabled: bool = False
    auth_mode: AuthMode = AuthMode.BASIC
    auth: BasicAuth | BearerAuth | ApiKeyAuth | DigestAuth | None = None

    options: Options = _Field(default_factory=Options)

    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_httpx_req(self) -> httpx.Request:
        headers: dict[str, str] = {
            header.key: header.value
            for header in self.headers
            if header.enabled
        }
        params: dict[str, str] = {
            param.key: param.value for param in self.params if param.enabled
        }

        if not self.body_enabled:
            return httpx.Request(
                method=self.method,
                url=self.url,
                headers=headers,
                params=params,
            )

        if self.body_mode == BodyMode.RAW:
            raw_language_to_content_type = {
                BodyRawLanguage.JSON: ContentType.JSON,
                BodyRawLanguage.YAML: ContentType.YAML,
                BodyRawLanguage.HTML: ContentType.HTML,
                BodyRawLanguage.XML: ContentType.XML,
                BodyRawLanguage.PLAIN: ContentType.TEXT,
            }
            headers['content-type'] = raw_language_to_content_type.get(
                self.body.language, ContentType.TEXT
            )

            raw = self.body.value
            if headers['content-type'] == ContentType.JSON:
                try:
                    raw = json.dumps(raw)
                except Exception:
                    pass

            return httpx.Request(
                method=self.method,
                url=self.url,
                headers=headers,
                params=params,
                content=raw,
            )
        elif self.body_mode == BodyMode.FILE:
            file = self.body.file
            if 'content-type' not in headers:
                headers['content-type'] = (
                    mimetypes.guess_type(file.name)[0]
                    or 'application/octet-stream'
                )
            return httpx.Request(
                method=self.method,
                url=self.url,
                headers=headers,
                params=params,
                content=file.read_bytes(),
            )
        elif self.body_mode == BodyMode.FORM_URLENCODED:
            form_urlencoded = {
                form_item.key: form_item.value
                for form_item in self.body.fields
                if form_item.enabled
            }
            return httpx.Request(
                method=self.method,
                url=self.url,
                headers=headers,
                params=params,
                data=form_urlencoded,
            )
        elif self.body_mode == BodyMode.FORM_MULTIPART:
            form_multipart_str = {
                form_item.key: form_item.value
                for form_item in self.body.fields
                if form_item.enabled and isinstance(form_item.value, str)
            }
            form_multipart_files = {
                form_item.key: (
                    form_item.value.name,
                    form_item.value.read_bytes(),
                    mimetypes.guess_type(form_item.value.name)[0]
                    or 'application/octet-stream',
                )
                for form_item in self.body.fields
                if form_item.enabled and isinstance(form_item.value, Path)
            }
            return httpx.Request(
                method=self.method,
                url=self.url,
                headers=headers,
                params=params,
                data=form_multipart_str,
                files=form_multipart_files,
            )

    def to_httpx_auth(self) -> httpx.Auth | None:
        if not self.auth_enabled:
            return

        if self.auth_mode == AuthMode.BASIC:
            return httpx.BasicAuth(
                username=self.auth.username, password=self.auth.password
            )
        elif self.auth_mode == AuthMode.BEARER:
            return httpx_auths.BearerAuth(token=self.auth.token)
        elif self.auth_mode == AuthMode.API_KEY:
            if self.auth.where == 'header':
                return httpx_auths.APIKeyHeaderAuth(
                    key=self.auth.key, value=self.auth.value
                )
            elif self.auth.where == 'param':
                return httpx_auths.APIKeyParamAuth(
                    key=self.auth.key, value=self.auth.value
                )
        elif self.auth_mode == AuthMode.DIGEST:
            return httpx.DigestAuth(
                username=self.auth.username, password=self.auth.password
            )

    def to_curl(self) -> str:
        headers: dict[str, str] = {
            header.key: header.value
            for header in self.headers
            if header.enabled
        }
        params: dict[str, str] = {
            param.key: param.value for param in self.params if param.enabled
        }

        body_raw = None
        body_form_urlencoded = None
        body_form_multipart = None
        body_files = None
        if self.body_enabled:
            if self.body_mode == BodyMode.RAW:
                body_raw = self.body
            elif self.body_mode == BodyMode.FORM_URLENCODED:
                body_form_urlencoded = {
                    form_field.key: form_field.value
                    for form_field in self.body.fields
                    if form_field.enabled
                }
            elif self.body_mode == BodyMode.FORM_MULTIPART:
                body_form_multipart = {
                    form_field.key: form_field.value
                    for form_field in self.body.fields
                    if form_field.enabled
                }
            elif self.body_mode == BodyMode.FILE:
                body_files = [self.body]

        auth_basic = None
        auth_bearer = None
        auth_api_key_header = None
        auth_api_key_param = None
        auth_digest = None
        if self.auth_enabled:
            if self.auth_mode == AuthMode.BASIC:
                auth_basic = (self.auth.username, self.auth.password)
            elif self.auth_mode == AuthMode.BEARER:
                auth_bearer = self.auth.token
            elif self.auth_mode == AuthMode.API_KEY:
                if self.auth.where == 'header':
                    auth_api_key_header = (self.auth.key, self.auth.value)
                elif self.auth.where == 'param':
                    auth_api_key_param = (self.auth.key, self.auth.value)
            elif self.auth_mode == AuthMode.DIGEST:
                auth_digest = (self.auth.username, self.auth.password)

        return build_curl_cmd(
            method=self.method,
            url=self.url,
            headers=headers,
            params=params,
            body_raw=body_raw,
            body_form_urlencoded=body_form_urlencoded,
            body_form_multipart=body_form_multipart,
            body_files=body_files,
            auth_basic=auth_basic,
            auth_bearer=auth_bearer,
            auth_api_key_header=auth_api_key_header,
            auth_api_key_param=auth_api_key_param,
            auth_digest=auth_digest,
        )
