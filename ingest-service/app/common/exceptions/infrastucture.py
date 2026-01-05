class InfrastructureException(Exception):
    """
    Base exception for infrastructure failures.

    These indicate SYSTEM problems and should result in 5xx.
    """
    pass


class StorageError(InfrastructureException):
    pass


class DatabaseError(InfrastructureException):
    pass


class QueueError(InfrastructureException):
    pass
