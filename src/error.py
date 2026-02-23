from enum import IntEnum


class ErrCode(IntEnum):
    """
    Error codes used by the application.

    Attributes
    ----------
    NOERR : int
        No error occurred.
    PARSE_ERR : int
        Failed to parse the input (invalid syntax/format).
    VALIDATION_ERR : int
        Input parsed but failed validation (invalid values/rules).
    ARGS_ERR : int
        Invalid command-line arguments (missing/unknown options).
    INVALID_PATH : int
        A provided path is invalid or cannot be accessed.
    DISPLAY_ERR : int
        Failed to display or render the output.
    """
    NOERR = 0
    PARSE_ERR = 1
    VALIDATION_ERR = 2
    ARGS_ERR = 3
    INVALID_PATH = 4
    DISPLAY_ERR = 5


class ParseError(Exception):
    """
    Raised when map parsing fails.
    """
    pass
