import sys
import logging
from typing import Any

from pydantic import ValidationError
import arcade

from src.parsing import parse
from src.logic import Map
from src.error import ParseError, ErrCode
from src.display import MapView, screen_size

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s:%(lineno)d - %(message)s"
)
logger = logging.getLogger(__name__)


def main() -> int:
    if len(sys.argv) != 2:
        logger.error("invalid usage. example :")
        logger.error("make run ARGS=example_map")
        return ErrCode.ARGS_ERR

    # parsing
    try:
        map_specs: dict[str, Any] = parse(sys.argv[1])
    except ParseError as e:
        logger.error(e)
        return ErrCode.PARSE_ERR
    try:
        Map.Validate(**map_specs)
    except ValidationError as e:
        logger.error(e.errors()[0]["msg"])
        return ErrCode.VALIDATION_ERR
    m = Map(**map_specs)
    logger.debug(m.hubs)
    logger.debug(m.connections)

    # logic
    m.solve()

    # display
    height, width = screen_size()
    window: arcade.Window = arcade.Window(height // 4, width // 4, "Fly-in")
    view: MapView = MapView(m)
    window.show_view(view)
    arcade.run()

    return ErrCode.NOERR


if __name__ == "__main__":
    sys.exit(main())
