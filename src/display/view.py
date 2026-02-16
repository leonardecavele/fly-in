import arcade
from arcade.shape_list import (
    ShapeElementList,
    create_ellipse_filled,
    create_line
)


class MapView(arcade.View):
    def __init__(self, game_map, *, cell_size: int = 80, margin: int = 60) -> None:
        super().__init__()
        self.map = game_map
        self.cell_size = cell_size
        self.margin = margin

        self.static_shapes = ShapeElementList()
        self.hub_pos: dict[str, tuple[float, float]] = {}

    def _grid_to_px(self, x: int, y: int) -> tuple[float, float]:
        px = self.margin + x * self.cell_size
        py = self.margin + y * self.cell_size
        return float(px), float(py)

    def build_static_layer(self) -> None:
        self.static_shapes = ShapeElementList()
        self.hub_pos.clear()

        # cache hub positions + draw hub nodes (static)
        for name, hub in self.map.hubs.items():
            px, py = self._grid_to_px(hub.x, hub.y)
            self.hub_pos[name] = (px, py)

            self.static_shapes.append(
                create_ellipse_filled(px, py, 30, 30, arcade.color.DARK_SLATE_GRAY)
            )

        # draw connections (static)
        for c in self.map.connections:
            ax, ay = self.hub_pos[c.a.name]
            bx, by = self.hub_pos[c.b.name]
            self.static_shapes.append(
                create_line(ax, ay, bx, by, arcade.color.DIM_GRAY, 3)
            )

    def on_show_view(self) -> None:
        self.build_static_layer()

    def on_draw(self) -> None:
        self.clear()
        self.static_shapes.draw()

        # dynamic layer: drones count on each hub
        for name, hub in self.map.hubs.items():
            px, py = self.hub_pos[name]
            n = len(hub.drones)
            arcade.draw_text(
                str(n),
                px + 18,
                py + 18,
                arcade.color.WHITE,
                12,
            )

            # optional: hub name (debug)
            arcade.draw_text(
                name,
                px + 18,
                py - 24,
                arcade.color.LIGHT_GRAY,
                10,
            )
