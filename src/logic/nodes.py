from pydantic import BaseModel, Field, ConfigDict

from src.logic import Drone


class Hub():
    def __init__(
        self,
        name: str,
        x: int | float,
        y: int | float,
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

    class Validate(BaseModel):
        model_config = ConfigDict(extra="forbid")

        x: int
        y: int
        max_drones: int = Field(ge=0)
        zone: str
        color: str
        # in case it is a start or end hub
        start_hub: bool = False
        end_hub: bool = False


class Connection():
    def __init__(self, a: Hub, b: Hub, max_drones: int) -> None:
        self.drones: list[Drone] = []

        self.a = a
        self.b = b
        self.cap = max_drones
