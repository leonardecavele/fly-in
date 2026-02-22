from enum import IntEnum


class ErrCode(IntEnum):
    """
    Error codes used by the application.

    Attributes
    ----------
    NOERR : int
        Attribute description.
    PARSE_ERR : int
        Attribute description.
    VALIDATION_ERR : int
        Attribute description.
    ARGS_ERR : int
        Attribute description.
    INVALID_PATH : int
        Attribute description.
    """
    NOERR = 0
    PARSE_ERR = 1
    VALIDATION_ERR = 2
    ARGS_ERR = 3
    INVALID_PATH = 4


class ParseError(Exception):
    """
    Raised when map parsing fails.
    """
    pass
