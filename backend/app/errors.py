from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from .timeutils import iso_z, utcnow


class ApiError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def _error_response(
    status_code: int, code: str, message: str
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {"code": code, "message": message},
            "serverTime": iso_z(utcnow()),
        },
    )


async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
    return _error_response(exc.status_code, exc.code, exc.message)


async def validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    message = "Invalid request payload"
    if errors:
        location = ".".join(str(part) for part in errors[0].get("loc", ())[1:])
        detail = str(errors[0].get("msg", "is invalid"))
        message = f"{location}: {detail}" if location else detail
    return _error_response(422, "VALIDATION_ERROR", message)


async def integrity_error_handler(_request: Request, exc: IntegrityError) -> JSONResponse:
    return _error_response(
        409, "CONFLICT", "The request conflicts with an existing record."
    )
