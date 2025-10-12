class DomainException(Exception):
    """Base class for all domain-related errors."""

    pass


class InvalidValue(DomainException, ValueError):
    """Invalid value for a value object."""

class EntityNotFound(DomainException):
    """Entity not found in the repository."""