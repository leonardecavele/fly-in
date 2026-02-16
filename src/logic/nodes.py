from src.logic import Drone


class Hub():
    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone: str,
        color: str,
        max_drones: int,
        start_hub: bool = False,
        end_hub: bool = False
    ) -> None:
        self.connections: list[Connection] = []
        self.drones: list[Drone] = []

        self.name = name
        self.x = x
        self.y = y
        self.zone = zone
        self.color = color
        self.max_drones = max_drones
        self.start_hub = start_hub
        self.end_hub = end_hub


class Connection():
    def __init__(self, a: Hub, b: Hub, max_drones: int) -> None:
        self.a = a
        self.b = b
        self.cap = max_drones
