from app.common.exceptions.domain import DomainException


class AuthException(DomainException):
    pass


class InvalidCredentials(AuthException):
    status_code = 401
    error_code = "INVALID_CREDENTIALS"
    message = "Incorrect username or password"


class InactiveUser(AuthException):
    status_code = 401
    error_code = "USER_INACTIVE"
    message = "User is inactive"


class InvalidToken(AuthException):
    status_code = 401
    error_code = "INVALID_TOKEN"
    message = "Invalid or expired token"


class InvalidAuthPayload(AuthException):
    status_code = 401
    error_code = "INVALID_AUTH_PAYLOAD"
    message = "Invalid authentication payload"


class PermissionDenied(AuthException):
    status_code = 403
    error_code = "PERMISSION_DENIED"
    message = "Permission denied"


class PolicyDenied(AuthException):
    status_code = 403
    error_code = "POLICY_DENIED"
    message = "Policy denied"