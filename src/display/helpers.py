import pyglet


def screen_size() -> tuple[int, int]:
    screen = pyglet.display.get_display().get_default_screen()
    return screen.width, screen.height
