class DomainException(Exception):
    """Base class for all domain-related errors."""

    pass


class InvalidValue(DomainException, ValueError):
    """Invalid value for a value object."""

class EntityNotFound(DomainException):
    """Entity not found in the repository."""
    
    
class InvalidURI(InvalidValue):
    """
    Raised when trying to set a invalid image URI
    """
class InvalidImageDimension(InvalidValue):
    """
    Raised when an image's width or height exceeds the maximum or the minimum allowed pixel dimensions.
    """


class InvalidImageType(InvalidValue):
    """
    Raised when the image type is not supported.
    """