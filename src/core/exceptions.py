class SpectraError(Exception):
    def __init__(self, message: str = "An error occurred", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(SpectraError):
    def __init__(self, resource: str = "Resource", id: str | None = None):
        detail = f"{resource} not found" if not id else f"{resource} {id} not found"
        super().__init__(message=detail, status_code=404)


class AuthError(SpectraError):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, status_code=401)


class ForbiddenError(SpectraError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message=message, status_code=403)


class ConflictError(SpectraError):
    def __init__(self, message: str = "Conflict"):
        super().__init__(message=message, status_code=409)


class ValidationError(SpectraError):
    def __init__(self, message: str = "Validation error"):
        super().__init__(message=message, status_code=422)
