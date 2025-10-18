from src.domain.shared.errors import DomainException, InvalidValue


class ClothNotFoundException(DomainException):
    """
    Raised when not finding any cloth pieces in a input image.
    """
    pass

class InvalidImageDimension(InvalidValue):
    """
    Raised when an image's width or height exceeds the maximum or the minimum allowed pixel dimensions.
    """

class InvalidImageType(InvalidValue):
    """
    Raised when the image type is not supported.
    """

class InvalidImageBlobSize(InvalidValue):
    """
    Raised when the image blob size exceeds the max size or is empty.
    """
    
class InvalidBoundingBox(InvalidValue):
    """
    Raised when the bounding box of a cloth item is invalid.
    """

class InvalidImageAnalysisStatusType(InvalidValue):
    """
    Raised when trying to set a invalid image analysis status type.
    """