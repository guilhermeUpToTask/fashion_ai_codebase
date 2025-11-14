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


class InvalidImageDimension(InvalidValue):
    """
    Raised when an image's width or height exceeds the maximum or the minimum allowed pixel dimensions.
    """


class InvalidImageType(InvalidValue):
    """
    Raised when the image type is not supported.
    """


class InvalidBoundingBox(InvalidValue):
    """
    Raised when the bounding box of a cloth item is invalid.
    """


class InvalidImageAnalysisStatusType(InvalidValue):
    """
    Raised when trying to set a invalid image analysis status type.
    """


class InvalidURI(InvalidValue):
    """
    Raised when trying to set a invalid image URI
    """
