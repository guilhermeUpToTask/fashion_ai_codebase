from src.domain.shared.errors import DomainException, InvalidValue


class CorruptedAggregateError(DomainException):
    pass


class InvalidTransitionException(DomainException):
    """
    Raised when a transition call comes from a unexpected state
    """


class MissingItemException(DomainException):
    """
    Raised when a item is missing
    """


class InvariantViolationException(DomainException):
    """
    Raised when a invariant is broken
    """


class InvalidLabel(InvalidValue):
    """
    Raised when a label is empty
    """


class InvalidBoundingBox(InvalidValue):
    """
    Raised when the bounding box of a cloth item is invalid.
    """


class InvalidImageAnalysisStatusType(InvalidValue):
    """
    Raised when trying to set a invalid image analysis status type.
    """


class ImageAnalysisRepositoryException(Exception):
    """Base exception for repository operations"""
    pass


class AggregateNotFoundException(ImageAnalysisRepositoryException):
    """Raised when attempting to operate on non-existent aggregate"""
    pass


class DuplicateAggregateException(ImageAnalysisRepositoryException):
    """Raised when attempting to add an aggregate that already exists"""
    pass