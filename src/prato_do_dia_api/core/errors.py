from __future__ import annotations

from typing import Literal

from fastapi import Request
from fastapi.responses import JSONResponse

from prato_do_dia_api.schemas.v1 import ApiErrorBody, ApiErrorResponse

ApiErrorCode = Literal[
    "invalid_image",
    "unsupported_media_type",
    "file_too_large",
    "model_unavailable",
    "inference_failed",
    "database_error",
    "contract_error",
]


class ApiError(Exception):
    def __init__(self, status_code: int, code: ApiErrorCode, message: str, details: object = None) -> None:
        self.status_code = status_code
        self.code: ApiErrorCode = code
        self.message = message
        self.details = details


async def api_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ApiError):
        raise exc
    response = ApiErrorResponse(error=ApiErrorBody(code=exc.code, message=exc.message, details=exc.details))
    return JSONResponse(status_code=exc.status_code, content=response.model_dump())
