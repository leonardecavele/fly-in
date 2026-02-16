import arcade

from src.display import MapView


def run(game_map) -> None:
    window = arcade.Window(1000, 700, "Fly-in")
    view = MapView(game_map)
    window.show_view(view)
    arcade.run()
