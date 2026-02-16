import arcade
from arcade.shape_list import (
    ShapeElementList,
    create_ellipse_filled,
    create_line
)

from src.logic import Map
from .helpers import parse_color


class MapView(arcade.View):
    def __init__(self, m, *, cell_size: float = 112, pad: float = 1.2) -> None:
        super().__init__()

        self.cell_size: float = cell_size
        self.pad: float = pad
        self.elapsed_time: float = 0

        self.map: Map = m
        for name in m.hubs:
            x: int = m.hubs[name].x
            y: int = m.hubs[name].y
            m.hubs[name].x, m.hubs[name].y = self.grid_to_world(x, y)

        self.camera: arcade.Camera2D = arcade.Camera2D()

        self.static_shapes: ShapeElementList = ShapeElementList()
        self.hub_name: dict[str, arcade.Text] = {}
        self.hub_count: dict[str, arcade.Text] = {}
        self.world_bounds: tuple[float, float, float, float] | None = None

    def grid_to_world(self, x: int, y: int) -> tuple[float, float]:
        return float(x) * self.cell_size, float(y) * self.cell_size

    def screen_to_world(
        self, screen_x: float, screen_y: float
    ) -> tuple[float, float]:
        c_x, c_y = self.camera.position
        w_x = c_x + (screen_x - self.window.width * 0.5) / self.camera.zoom
        w_y = c_y + (screen_y - self.window.height * 0.5) / self.camera.zoom
        return w_x, w_y

    def static_layer(self) -> None:
        self.static_shapes.clear()
        self.hub_name.clear()
        self.hub_count.clear()

        for connection in self.map.connections:
            a_x, a_y = connection.a.x, connection.a.y
            b_x, b_y = connection.b.x, connection.b.y
            self.static_shapes.append(
                create_line(a_x, a_y, b_x, b_y, arcade.color.SNOW, 5)
            )

        for hub in self.map.hubs.values():
            x, y = hub.x, hub.y
            color: arcade.types.Color = parse_color(hub.color)
            self.static_shapes.append(
                create_ellipse_filled(x, y, 30, 30, color)
            )

        x_list = [hub.x for hub in self.map.hubs.values()]
        y_list = [hub.y for hub in self.map.hubs.values()]
        min_x, max_x = min(x_list), max(x_list)
        min_y, max_y = min(y_list), max(y_list)
        self.world_bounds = (min_x, min_y, max_x, max_y)

        for name, hub in self.map.hubs.items():
            x, y = hub.x, hub.y
            t = arcade.Text(
                name,
                x,
                y - 32,
                arcade.color.SNOW,
                9,
                anchor_x="center",
                anchor_y="bottom"
            )
            self.hub_name[name] = t

        for name, hub in self.map.hubs.items():
            x, y = hub.x, hub.y
            t = arcade.Text(
                "0",
                x - 18,
                y + 32,
                arcade.color.SNOW,
                9,
                anchor_x="center",
                anchor_y="top",
            )
            self.hub_count[name] = t

    def camera_to_bounds(self) -> None:
        if self.world_bounds is None:
            return None

        min_x, min_y, max_x, max_y = self.world_bounds
        w = max_x - min_x
        h = max_y - min_y

        if w <= 0 or h <= 0:
            return None

        zoom_x = self.window.width / w
        zoom_y = self.window.height / h
        zoom = min(zoom_x, zoom_y) / self.pad

        center_x = (min_x + max_x) * 0.5
        center_y = (min_y + max_y) * 0.5
        self.camera.position = (center_x, center_y)
        self.camera.zoom = zoom

    def on_show_view(self) -> None:
        arcade.set_background_color(arcade.color.SMOKY_BLACK)
        self.static_layer()
        self.camera_to_bounds()

    def on_update(self, dt: float) -> None:
        from src.logic import Drone

        self.elapsed_time += dt
        if self.elapsed_time >= 1.0:
            for hub in self.map.hubs.values():
                if hub.start_hub:
                    hub.drones.append(Drone())
            self.elapsed_time = 0.0

    def on_draw(self) -> None:
        self.clear()

        self.camera.use()
        self.static_shapes.draw()

        for name, hub in self.map.hubs.items():
            self.hub_count[name].text = str(len(hub.drones))
            self.hub_count[name].draw()

        for name in self.map.hubs.keys():
            self.hub_name[name].draw()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        #  for linters
        del x, y, modifiers

        if buttons & arcade.MOUSE_BUTTON_LEFT:
            cx, cy = self.camera.position
            self.camera.position = (
                cx - dx / self.camera.zoom, cy - dy / self.camera.zoom
            )

    def on_mouse_scroll(
        self, x: int, y: int, scroll_x: int, scroll_y: int
    ) -> None:
        #  for linters
        del scroll_x

        if scroll_y == 0:
            return

        pre_x, pre_y = self.screen_to_world(x, y)

        factor = 1.1 if scroll_y > 0 else (1.0 / 1.1)
        new_zoom = self.camera.zoom * factor

        if new_zoom < 0.45:
            new_zoom = 0.45
        if new_zoom > 7:
            new_zoom = 7

        self.camera.zoom = new_zoom

        new_x, new_y = self.screen_to_world(x, y)
        camera_x, camera_y = self.camera.position
        self.camera.position = (
            camera_x + (pre_x - new_x), camera_y + (pre_y - new_y)
        )
