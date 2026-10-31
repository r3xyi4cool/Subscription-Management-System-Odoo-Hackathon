from flask import jsonify


class APIError(Exception):
    def __init__(self, message, status_code=400, code="BAD_REQUEST", details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}

    def to_dict(self):
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class BadRequestError(APIError):
    def __init__(self, message="Bad Request", details=None):
        super().__init__(message, status_code=400, code="BAD_REQUEST", details=details)


class UnauthorizedError(APIError):
    def __init__(self, message="Unauthorized", details=None):
        super().__init__(message, status_code=401, code="UNAUTHORIZED", details=details)


class ForbiddenError(APIError):
    def __init__(self, message="Forbidden", details=None):
        super().__init__(message, status_code=403, code="FORBIDDEN", details=details)


class NotFoundError(APIError):
    def __init__(self, message="Resource not found", details=None):
        super().__init__(message, status_code=404, code="NOT_FOUND", details=details)


class ConflictError(APIError):
    def __init__(self, message="Conflict", details=None):
        super().__init__(message, status_code=409, code="CONFLICT", details=details)


class ValidationError(APIError):
    def __init__(self, message="Validation error", details=None):
        super().__init__(message, status_code=422, code="UNPROCESSABLE_ENTITY", details=details)


def error_response(message, status_code=400, code="BAD_REQUEST", details=None):
    return (
        jsonify({
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        }),
        status_code,
    )


def success_response(data=None, status_code=200, message=None):
    payload = {}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
        if isinstance(data, dict):
            for k, v in data.items():
                if k not in payload:
                    payload[k] = v
    return jsonify(payload), status_code

