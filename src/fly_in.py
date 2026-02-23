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
    """
    Program entry point.

    Parse inputs, compute paths, and launch the viewer.

    Returns
    -------
    int
        Exit status code as an ErrCode value.
    """
    ac: int = len(sys.argv)
    win_size: float = 3
    if not (1 < ac < 4):
        logger.error(
            "invalid usage. example :\n"
            "make run ARGS=\"example_map [(float)size]\""
        )
        return ErrCode.ARGS_ERR
    if ac == 3:
        try:
            win_size = float(sys.argv[2])
            if win_size < 1 or win_size > 4:
                logger.error("size must be greather than 0 and less than 5")
                return ErrCode.ARGS_ERR
        except ValueError:
            logger.error(
                "invalid usage. example :\n"
                "make run ARGS=\"example_map [(float)size]\""
            )
            return ErrCode.ARGS_ERR

    # parsing
    try:
        map_specs: dict[str, Any] = parse(sys.argv[1])
    except (ParseError, OSError) as e:
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
    try:
        m.compute_paths()
    except (RuntimeError, AssertionError) as e:
        logger.error(e)
        return ErrCode.INVALID_PATH

    # display
    try:
        height, width = screen_size()
        window: arcade.Window = arcade.Window(
            int(height / win_size), int(width / win_size), "Fly-in"
        )
        view: MapView = MapView(m)
        window.show_view(view)
        arcade.run()
    except Exception as e:
        logger.error(e)
        return ErrCode.DISPLAY_ERR

    return ErrCode.NOERR


if __name__ == "__main__":
    sys.exit(main())
