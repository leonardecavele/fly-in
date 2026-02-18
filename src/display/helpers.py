import math

import pyglet
import arcade


def screen_size() -> tuple[int, int]:
    screen = pyglet.display.get_display().get_default_screen()
    return screen.width, screen.height


def parse_color(name: str) -> arcade.types.Color:
    key = name.strip().upper().replace(" ", "_").replace("-", "_")
    return getattr(arcade.color, key, arcade.color.RED)


def triangle_points(
    cx: float, cy: float, size: float
) -> list[tuple[float, float]]:
    h = size * 0.5
    return [
        (cx, cy + h),
        (cx - h, cy - h),
        (cx + h, cy - h),
    ]


def regular_polygon_points(
    cx: float, cy: float, radius: float, n: int
) -> list[tuple[float, float]]:
    return [
        (
            cx + radius * math.cos(2 * math.pi * i / n),
            cy + radius * math.sin(2 * math.pi * i / n),
        )
        for i in range(n)
    ]
