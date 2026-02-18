from enum import IntEnum


class ErrCode(IntEnum):
    NOERR = 0
    PARSE_ERR = 1
    VALIDATION_ERR = 2
    ARGS_ERR = 3
    INVALID_PATH = 4


class ParseError(Exception):
    pass
