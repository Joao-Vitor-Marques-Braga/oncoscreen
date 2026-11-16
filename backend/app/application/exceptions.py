"""Application-level exceptions."""


class ApplicationError(Exception):
    """Base exception for application use cases."""


class AuthenticationError(ApplicationError):
    """Raised when login credentials are invalid."""


class AuthorizationError(ApplicationError):
    """Raised when a user lacks permission for a resource."""


class NotFoundError(ApplicationError):
    """Raised when a requested entity does not exist."""


class ValidationError(ApplicationError):
    """Raised when input data violates business rules."""

