class M3YouException(Exception):
    pass


class MalformedExtinfException(M3YouException):
    pass


class MalformedPlaylistException(M3YouException):
    pass


class URLException(M3YouException):
    pass


class WrongTypeException(M3YouException):
    pass


class IndexOutOfBoundsException(M3YouException):
    pass


class AttributeAlreadyPresentException(M3YouException):
    pass


class AttributeNotFoundException(M3YouException):
    pass
