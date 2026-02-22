from pydantic import BaseModel, Field, ConfigDict

from src.logic import Drone


class Hub():
    """
    Hub node with position, style, and per-turn capacity.
    """
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
        """
        Create a Hub.

        Store hub metadata and initialize links and occupancy tracking.

        Parameters
        ----------
        name
            Hub name.
        x
            Hub x coordinate.
        y
            Hub y coordinate.
        zone
            Hub zone type.
        color
            Hub display color name.
        max_drones
            Maximum drones allowed at the hub.
        start_hub
            Whether this hub is the start hub.
        end_hub
            Whether this hub is the end hub.
        """
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
        """
        Pydantic schema for validating hub metadata.

        Attributes
        ----------
        model_config : Any
            Attribute description.
        x
            Hub x coordinate.
        y
            Hub y coordinate.
        max_drones
            Maximum drones allowed at the hub.
        zone
            Hub zone type.
        color
            Hub display color name.
        start_hub
            Whether this hub is the start hub.
        end_hub
            Whether this hub is the end hub.
        """
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
    """
    Undirected edge between two hubs with a capacity.
    """
    def __init__(self, a: Hub, b: Hub, max_drones: int) -> None:
        """
        Create a Connection.

        Link the hubs and initialize per-turn capacity tracking.

        Parameters
        ----------
        a
            First endpoint hub.
        b
            Second endpoint hub.
        max_drones
            Maximum drones on the connection.
        """
        self.name: str = f"{a.name}/{b.name}"
        self.drones: dict[int, list[Drone]] = {}
        self.linked: list[Hub] = []

        self.drone_count: dict[int, int] = {}
        self.max_drones: int = max_drones

        self.linked.append(a)
        self.linked.append(b)
