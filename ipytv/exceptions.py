"""All ipytv-specific exceptions

Classes:
    IPyTVException
    MalformedExtinfException
    MalformedPlaylistException
    URLException
    WrongTypeException
    IndexOutOfBoundsException
    AttributeAlreadyPresentException
    AttributeNotFoundException
"""
class IPyTVException(Exception):
    pass


class MalformedExtinfException(IPyTVException):
    pass


class MalformedPlaylistException(IPyTVException):
    pass


class URLException(IPyTVException):
    pass


class WrongTypeException(IPyTVException):
    pass


class IndexOutOfBoundsException(IPyTVException):
    pass


class AttributeAlreadyPresentException(IPyTVException):
    pass


class AttributeNotFoundException(IPyTVException):
    pass
