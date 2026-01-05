from app.common.exceptions.domain import DomainException

class UserException(DomainException):
    pass


class UserNotFoundError(UserException):
    status_code = 404
    error_code = "USER_NOT_FOUND"
    message = "User not found"

class InvalidUserDataError(UserException):
    status_code = 400
    error_code = "INVALID_USER_DATA"
    message = "Invalid user data"

class UserPermissionDenied(UserException):
    status_code = 403
    error_code = "USER_PERMISSION_DENIED"
