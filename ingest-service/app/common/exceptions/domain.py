class DomainException(Exception):
    status_code: int = 400
    error_code: str = "DOMAIN_ERROR"
    message: str = "Domain error"

    def __init__(self, message: str | None = None):
        super().__init__(message or self.message)
