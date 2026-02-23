import arcade
from arcade.shape_list import (
    Shape,
    create_rectangle_filled,
    create_ellipse_filled,
    create_polygon,
    create_line
)

from src.logic import Map, Connection
from .helpers import parse_color, triangle_points, regular_polygon_points


class MapView(arcade.View):
    """
    Arcade view that draws the map and simulation state.
    """
    def __init__(
        self, m: Map, *, cell_size: float = 112, pad: float = 1.2
    ) -> None:
        """
        Initialize the map view.

        Prepare cameras, layers, and coordinate transforms.

        Parameters
        ----------
        m
            Map instance to display.
        cell_size
            Pixel size of one grid cell.
        pad
            Padding factor around bounds.
        """
        super().__init__()

        self.cell_size: float = cell_size
        self.pad: float = pad
        self.elapsed_time: float = 0

        self.pause: bool = True
        self._current_turn: int = 0

        self.map: Map = m
        for name in m.hubs:
            x: int = int(m.hubs[name].x)
            y: int = int(m.hubs[name].y)
            m.hubs[name].x, m.hubs[name].y = self.grid_to_world(x, y)

        self.camera: arcade.Camera2D = arcade.Camera2D()
        self.gui_camera: arcade.Camera2D = arcade.Camera2D()

        self.static_shapes: list[Shape] = []
        self.hub_name: dict[str, arcade.Text] = {}
        self.hub_count: dict[str, arcade.Text] = {}
        self.connection_count: dict[Connection, arcade.Text] = {}
        self.world_bounds: tuple[float, float, float, float] | None = None

        self.turn_display: arcade.Text | None = None
        self.title_display: arcade.Text | None = None

    @property
    def current_turn(self) -> int:
        """
        Get the current simulation turn.

        Return the current turn index used for display.

        Parameters
        ----------
        self : MapView
            Value for param.

        Returns
        -------
        int
            Current simulation turn index.
        """
        return self._current_turn

    @current_turn.setter
    def current_turn(self, value: int) -> None:
        """
        Set the current simulation turn.

        Update the turn index used for display.

        Parameters
        ----------
        self : MapView
            Value for param.
        value
            New simulation turn index.
        """
        if self.map.turn_count <= 0:
            self._current_turn = 0
            return
        self._current_turn = value % self.map.turn_count

    def grid_to_world(self, x: int, y: int) -> tuple[float, float]:
        """
        Convert grid coords to world coords.

        Scale grid coordinates into world pixel space.

        Parameters
        ----------
        x
            Grid x coordinate.
        y
            Grid y coordinate.

        Returns
        -------
        tuple[float, float]
            World coordinates in pixels.
        """
        return float(x) * self.cell_size, float(y) * self.cell_size

    def screen_to_world(
        self, screen_x: float, screen_y: float
    ) -> tuple[float, float]:
        """
        Convert screen coords to world coords.

        Translate screen pixels into world coordinates.

        Parameters
        ----------
        screen_x
            Screen x position in pixels.
        screen_y
            Screen y position in pixels.

        Returns
        -------
        tuple[float, float]
            World coordinates in pixels.
        """
        c_x, c_y = self.camera.position
        w_x = c_x + (screen_x - self.window.width * 0.5) / self.camera.zoom
        w_y = c_y + (screen_y - self.window.height * 0.5) / self.camera.zoom
        return w_x, w_y

    def hud_layer(self) -> None:
        """
        Build the HUD layer.

        Create HUD texts for the title and current turn.
        """
        t = arcade.Text(
            "0",
            0,
            0,
            arcade.color.SNOW,
            self.window.width // 30,
            anchor_x="left",
            anchor_y="bottom"
        )
        self.turn_display = t

        t = arcade.Text(
            "Fly-in",
            0,
            0,
            arcade.color.SNOW,
            self.window.width // 30,
            anchor_x="left",
            anchor_y="top"
        )
        self.title_display = t

    def static_layer(self) -> None:
        """
        Build static map shapes.

        Create shapes and labels that do not change per turn.
        """
        self.static_shapes.clear()
        self.hub_name.clear()
        self.hub_count.clear()
        self.connection_count.clear()

        for connection in self.map.connections:
            a, b = connection.linked
            a_x, a_y = a.x, a.y
            b_x, b_y = b.x, b.y
            self.static_shapes.append(
                create_line(a_x, a_y, b_x, b_y, arcade.color.DAVY_GREY, 6.3)
            )
            x = (a_x + b_x) / 2
            y = (a_y + b_y) / 2
            t = arcade.Text(
                "0",
                x,
                y,
                arcade.color.SNOW,
                8,
                anchor_x="center",
                anchor_y="center"
            )
            self.connection_count[connection] = t

        for hub in self.map.hubs.values():
            x, y = hub.x, hub.y
            color: arcade.types.Color = parse_color(hub.color)
            if hub.zone == "normal":
                self.static_shapes.append(
                    create_ellipse_filled(x, y, 30, 30, color)
                )
            elif hub.zone == "restricted":
                self.static_shapes.append(
                    create_rectangle_filled(x, y, 30, 29, color)
                )
            elif hub.zone == "priority":
                pts = triangle_points(x, y + 3.3, 29)
                self.static_shapes.append(create_polygon(pts, color))
            elif hub.zone == "blocked":
                pts = regular_polygon_points(x, y, 17.5, 6)
                self.static_shapes.append(create_polygon(pts, color))

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
                x,
                y,
                arcade.color.CHARCOAL,
                11,
                anchor_x="center",
                anchor_y="center"
            )
            self.hub_count[name] = t

    def camera_to_bounds(self) -> None:
        """
        Fit the camera to map bounds.

        Center and zoom the camera to fit the map.
        """
        if self.world_bounds is None:
            return None

        min_x, min_y, max_x, max_y = self.world_bounds
        w = max_x - min_x
        h = max_y - min_y

        min_extent = self.cell_size * 0.5
        if w < min_extent:
            w = min_extent
        if h < min_extent:
            h = min_extent

        zoom_x = self.window.width / w
        zoom_y = self.window.height / h
        zoom = min(zoom_x, zoom_y) / self.pad

        center_x = (min_x + max_x) * 0.5
        center_y = (min_y + max_y) * 0.5
        self.camera.position = (center_x, center_y)
        self.camera.zoom = zoom

    def on_show_view(self) -> None:
        """
        Set up the view when shown.

        Initialize background, layers, and camera settings.
        """
        arcade.set_background_color(arcade.color.SMOKY_BLACK)
        self.static_layer()
        self.hud_layer()
        self.camera_to_bounds()

    def on_update(self, dt: float) -> None:
        """
        Update the simulation state.

        Advance turns when not paused.

        Parameters
        ----------
        dt
            Elapsed time since last update.
        """
        if self.pause:
            return
        self.elapsed_time += dt
        if self.elapsed_time >= 0.6:
            self.elapsed_time = 0.0
            self.current_turn += 1

    def on_draw(self) -> None:
        """
        Draw the current frame.

        Draw map shapes, counts, and HUD overlays.
        """
        self.clear()

        self.camera.use()
        for s in self.static_shapes:
            s.draw()

        for name, hub in self.map.hubs.items():
            self.hub_count[name].text = str(
                len(hub.drones.get(self.current_turn, []))
            )
            self.hub_count[name].draw()

        for c in self.map.connections:
            self.connection_count[c].text = str(
                c.drone_count.get(self.current_turn, 0)
            )
            self.connection_count[c].draw()

        for name in self.map.hubs.keys():
            self.hub_name[name].draw()

        self.gui_camera.use()
        assert self.turn_display is not None
        assert self.world_bounds is not None
        assert self.title_display is not None

        self.turn_display.x = self.window.height * 0.01
        self.turn_display.y = self.window.height * 0.01
        self.turn_display.text = (
            f"{self.current_turn + 1}/{self.map.turn_count}"
        )
        self.turn_display.draw()

        self.title_display.x = self.window.height * 0.01
        self.title_display.y = self.window.height - self.window.height * 0.01
        self.title_display.draw()

    def on_mouse_drag(
        self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int
    ) -> None:
        """
        Handle mouse dragging.

        Pan the camera when dragging with the left button.

        Parameters
        ----------
        x
            Mouse x position in pixels.
        y
            Mouse y position in pixels.
        dx
            Mouse delta x in pixels.
        dy
            Mouse delta y in pixels.
        buttons
            Mouse button state bitmask.
        modifiers
            Modifier keys bitmask.
        """
        #  for linters
        del x, y, modifiers

        if buttons & arcade.MOUSE_BUTTON_LEFT:
            cx, cy = self.camera.position
            self.camera.position = (
                cx - dx / self.camera.zoom, cy - dy / self.camera.zoom
            )

    def on_resize(self, width: int, height: int) -> None:
        """
        Handle window resize.

        Refit the camera after resizing the window.

        Parameters
        ----------
        width
            New window width in pixels.
        height
            New window height in pixels.
        """
        super().on_resize(width, height)
        self.camera_to_bounds()

    def on_mouse_scroll(
        self, x: int, y: int, scroll_x: int, scroll_y: int
    ) -> None:
        """
        Handle mouse wheel scrolling.

        Zoom the camera around the cursor position.

        Parameters
        ----------
        x
            Mouse x position in pixels.
        y
            Mouse y position in pixels.
        scroll_x
            Horizontal scroll amount.
        scroll_y
            Vertical scroll amount.
        """
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

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        """
        Handle key press events.

        Handle pause, stepping, reset, and quit controls.

        Parameters
        ----------
        symbol
            Pressed key code.
        modifiers
            Modifier keys bitmask.

        Returns
        -------
        bool | None
            True if handled, else delegate to the base handler.
        """
        if symbol == arcade.key.Q:
            arcade.exit()
            return True
        if symbol == arcade.key.SPACE:
            self.pause = not self.pause
            self.elapsed_time = 0
            return True
        if symbol == arcade.key.R:
            self.current_turn = 0
            return True
        if (
            (symbol == arcade.key.L or symbol == arcade.key.RIGHT)
            and self.pause
        ):
            self.current_turn += 1
            return True
        if (
            (symbol == arcade.key.H or symbol == arcade.key.LEFT)
            and self.pause
        ):
            self.current_turn -= 1
            return True
        return super().on_key_press(symbol, modifiers)
