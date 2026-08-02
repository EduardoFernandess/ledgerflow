from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    payload = {
        "detail": response.data.get("detail", response.data)
        if isinstance(response.data, dict)
        else response.data,
        "code": getattr(exc, "default_code", getattr(exc, "code", "error")),
        "errors": response.data if isinstance(response.data, dict) else None,
    }
    if isinstance(response.data, dict) and "detail" in response.data and len(response.data) == 1:
        payload["errors"] = None
    response.data = payload
    return response


class ServiceError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "service_error"

    def __init__(self, detail: str, code: str | None = None, status_code: int | None = None):
        super().__init__(detail)
        self.detail = detail
        self.code = code or self.default_code
        if status_code is not None:
            self.status_code = status_code


def error_response(exc: ServiceError) -> Response:
    return Response(
        {"detail": exc.detail, "code": exc.code, "errors": None},
        status=exc.status_code,
    )
