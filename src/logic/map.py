from pydantic import BaseModel, Field
from typing import Any, Annotated

from src.logic import Drone, Hub, Connection


class Map():
    def __init__(
        self,
        nb_drones: int,
        hubs: dict[str, dict[str, Any]],
        connections: list[tuple[str, str, int]]
    ) -> None:
        self.hubs: dict[str, Hub] = {}
        self.connections: list[Connection] = []
        for name, data in hubs.items():
            self.hubs[name] = Hub(name, **data)
            if "start_hub" in data:
                for _ in range(nb_drones):
                    self.hubs[name].drones.append(Drone())
        for h1, h2, max_drones in connections:
            c = Connection(self.hubs[h1], self.hubs[h2], max_drones)
            self.connections.append(c)
            self.hubs[h1].connections.append(c)
            self.hubs[h2].connections.append(c)

    class Validate(BaseModel):
        nb_drones: int = Field(ge=0)
        hubs: dict[str, Hub.Validate]
        connections: list[tuple[str, str, Annotated[int, Field(ge=0)]]]
