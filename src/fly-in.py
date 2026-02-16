import sys
import logging
from typing import Any
from pydantic import ValidationError

from src.parsing import parse
from src.logic import Map
from src.error import ParseError, ErrCode
from src.display import run

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s:%(lineno)d - %(message)s"
)
logger = logging.getLogger(__name__)


def main() -> int:
    if len(sys.argv) != 2:
        logger.error("invalid usage. example :")
        logger.error("make run args=example_map")
        return ErrCode.ARGS_ERR
    try:
        map_specs: dict[str, Any] = parse(sys.argv[1])
    except ParseError as e:
        logger.error(e)
        return ErrCode.PARSE_ERR
    try:
        Map.MapSpecs(**map_specs)
    except ValidationError as e:
        logger.error(e.errors()[0]["msg"])
        return ErrCode.VALIDATION_ERR
    m = Map(**map_specs)
    logger.debug(m.hubs)
    logger.debug(m.connections)
    run(m)
    return ErrCode.NOERR


if __name__ == "__main__":
    sys.exit(main())
