import pyglet
import arcade


def screen_size() -> tuple[int, int]:
    screen = pyglet.display.get_display().get_default_screen()
    return screen.width, screen.height


def parse_color(name: str) -> arcade.types.Color:
    key = name.strip().upper().replace(" ", "_").replace("-", "_")
    return getattr(arcade.color, key, arcade.color.RED)
