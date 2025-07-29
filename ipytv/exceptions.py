"""All ipytv-specific exceptions.

This module defines custom exception classes for the ipytv library,
providing specific error types for different failure scenarios when
working with IPTV playlists and channels.

Classes:
    IPyTVException: Base exception class for all ipytv errors
    MalformedExtinfException: Raised when EXTINF rows cannot be parsed
    MalformedPlaylistException: Raised when playlist structure is invalid
    URLException: Raised when URL operations fail
    WrongTypeException: Raised when incorrect types are provided
    IndexOutOfBoundsException: Raised when accessing invalid indices
    AttributeAlreadyPresentException: Raised when duplicate attributes are added
    AttributeNotFoundException: Raised when required attributes are missing
"""


class IPyTVException(Exception):
    """Base exception class for all ipytv-specific errors.

    All other exceptions in this module inherit from this class,
    allowing for catch-all exception handling of ipytv-related errors.

    Example:
        >>> try:
        ...     # ipytv operations
        ... except IPyTVException as e:
        ...     # Handle any ipytv-specific error
    """
    def __init__(self, message: str = "An unexpected error occurred") -> None:
        """Initialize the exception with an optional message.

        Args:
            message: The error message to display.
        """
        super().__init__(message)


class MalformedExtinfException(IPyTVException):
    """Raised when an EXTINF row in an M3U playlist cannot be parsed.

    This exception is thrown when the parser encounters EXTINF rows
    with invalid syntax, malformed attributes, or unexpected formatting
    that prevents proper channel information extraction.

    Example:
        >>> # Raised for: #EXTINF:-1 tvg-id="unclosed quote,Channel
        >>> raise MalformedExtinfException("Invalid EXTINF syntax")
    """
    def __init__(self, message: str = "Malformed EXTINF row cannot be parsed") -> None:
        """Initialize the exception with an optional message.

        Args:
            message: The error message describing the EXTINF parsing issue.
        """
        super().__init__(message)


class MalformedPlaylistException(IPyTVException):
    """Raised when the overall playlist structure is invalid.

    This exception indicates issues with the playlist's structure,
    such as missing headers, invalid file format, or corrupted
    playlist data that prevents proper parsing.

    Example:
        >>> # Raised when M3U file lacks #EXTM3U header
        >>> raise MalformedPlaylistException("Missing M3U header")
    """
    def __init__(self, message: str = "Playlist structure is invalid") -> None:
        """Initialize the exception with an optional message.

        Args:
            message: The error message describing the playlist structure issue.
        """
        super().__init__(message)


class URLException(IPyTVException):
    """Raised when URL-related operations fail.

    This exception covers various URL-related errors such as
    invalid URL formats, network connectivity issues, or
    problems accessing remote playlist resources.

    Example:
        >>> # Raised for invalid URLs or network failures
        >>> raise URLException("Cannot access playlist URL")
    """
    def __init__(self, message: str = "URL operation failed") -> None:
        """Initialize the exception with an optional message.

        Args:
            message: The error message describing the URL-related issue.
        """
        super().__init__(message)


class WrongTypeException(IPyTVException):
    """Raised when operations receive arguments of incorrect types.

    This exception is thrown when functions or methods receive
    parameters that don't match the expected type requirements,
    helping to enforce proper type usage throughout the library.

    Example:
        >>> # Raised when string expected but integer provided
        >>> raise WrongTypeException("Expected string, got int")
    """
    def __init__(self, message: str = "Incorrect type provided") -> None:
        """Initialize the exception with an optional message.

        Args:
            message: The error message describing the type mismatch.
        """
        super().__init__(message)


class IndexOutOfBoundsException(IPyTVException):
    """Raised when attempting to access invalid playlist indices.

    This exception occurs when trying to access channels or other
    playlist elements using indices that are outside the valid
    range of available items.

    Example:
        >>> # Raised when accessing playlist[100] on 10-item playlist
        >>> raise IndexOutOfBoundsException("Index 100 out of range")
    """
    def __init__(self, message: str = "Index out of bounds") -> None:
        """Initialize the exception with an optional message.

        Args:
            message: The error message describing the index boundary violation.
        """
        super().__init__(message)


class AttributeAlreadyPresentException(IPyTVException):
    """Raised when attempting to add duplicate attributes.

    This exception is thrown when trying to add an attribute
    that already exists in contexts where duplicates are not
    allowed, such as playlist headers or channel attributes.

    Example:
        >>> # Raised when adding "tvg-id" twice to same channel
        >>> raise AttributeAlreadyPresentException("tvg-id already exists")
    """
    def __init__(self, message: str = "Attribute already exists") -> None:
        """Initialize the exception with an optional message.

        Args:
            message: The error message describing the duplicate attribute issue.
        """
        super().__init__(message)


class AttributeNotFoundException(IPyTVException):
    """Raised when attempting to access non-existent attributes.

    This exception occurs when trying to retrieve, modify, or
    delete attributes that don't exist in the target playlist
    or channel object.

    Example:
        >>> # Raised when accessing missing "group-title" attribute
        >>> raise AttributeNotFoundException("group-title not found")
    """
    def __init__(self, message: str = "Attribute not found") -> None:
        """Initialize the exception with an optional message.

        Args:
            message: The error message describing the missing attribute.
        """
        super().__init__(message)


if __name__ == "__main__":
    pass
