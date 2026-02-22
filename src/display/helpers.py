import math

import pyglet
import arcade


def screen_size() -> tuple[int, int]:
    """
    Get the primary screen size.

    Return the width and height of the default display.

    Returns
    -------
    tuple[int, int]
        Screen width and height in pixels.
    """
    screen = pyglet.display.get_display().get_default_screen()
    return screen.width, screen.height


def parse_color(name: str) -> arcade.types.Color:
    """
    Parse a color name.

    Map a string to an Arcade color constant.

    Parameters
    ----------
    name
        Color name to parse.

    Returns
    -------
    arcade.types.Color
        Resolved Arcade color value.
    """
    key = name.strip().upper().replace(" ", "_").replace("-", "_")
    return getattr(arcade.color, key, arcade.color.SNOW)


def triangle_points(
    cx: float, cy: float, size: float
) -> list[tuple[float, float]]:
    """
    Compute triangle vertices.

    Return points for an upright triangle centered at (cx, cy).

    Parameters
    ----------
    cx
        Triangle center x coordinate.
    cy
        Triangle center y coordinate.
    size
        Triangle size in pixels.

    Returns
    -------
    list[tuple[float, float]]
        Triangle vertex points.
    """
    h = size * 0.5
    return [
        (cx, cy + h),
        (cx - h, cy - h),
        (cx + h, cy - h),
    ]


def regular_polygon_points(
    cx: float, cy: float, radius: float, n: int
) -> list[tuple[float, float]]:
    """
    Compute regular polygon vertices.

    Return points for a regular n-gon centered at (cx, cy).

    Parameters
    ----------
    cx
        Polygon center x coordinate.
    cy
        Polygon center y coordinate.
    radius
        Polygon radius in pixels.
    n
        Number of polygon sides.

    Returns
    -------
    list[tuple[float, float]]
        Polygon vertex points.
    """
    return [
        (
            cx + radius * math.cos(2 * math.pi * i / n),
            cy + radius * math.sin(2 * math.pi * i / n),
        )
        for i in range(n)
    ]
