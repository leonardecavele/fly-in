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
        self.linked: list[Connection] = []
        self.drones: dict[int, list[Drone]] = {}

        self.name: str = name
        self.x: int | float = x
        self.y: int | float = y
        self.zone: str = zone
        self.color: str = color
        self.max_drones: int = max_drones
        self.start_hub: bool = start_hub
        self.end_hub: bool = end_hub

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
        self.name: str = f"{a.name}/{b.name}"
        self.drones: dict[int, list[Drone]] = {}
        self.linked: list[Hub] = []

        self.drone_count: dict[int, int] = {}
        self.max_drones: int = max_drones

        self.linked.append(a)
        self.linked.append(b)
