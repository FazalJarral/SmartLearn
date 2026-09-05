from dataclasses import dataclass
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


@dataclass
class ApiError(Exception):
    code: str
    message: str
    status_code: int = 400
    field_errors: dict[str, str] | None = None


def error_envelope(code: str, message: str, request_id: str, field_errors: dict[str, str] | None = None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
            "fields": field_errors or {},
        }
    }


def install_error_handlers(app: FastAPI) -> None:
    @app.middleware("http")
    async def correlation_id(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response

    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        request_id = getattr(request.state, "request_id", str(uuid4()))
        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope(exc.code, exc.message, request_id, exc.field_errors),
            headers={"x-request-id": request_id},
        )
