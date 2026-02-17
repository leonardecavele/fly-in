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
        self.turn_count: int = 0
        for name, data in hubs.items():
            self.hubs[name] = Hub(name, **data)
            self.hubs[name].drones.append(list())
            if "start_hub" in data:
                for _ in range(nb_drones):
                    self.hubs[name].drones[0].append(Drone())
        for h1, h2, max_drones in connections:
            c = Connection(self.hubs[h1], self.hubs[h2], max_drones)
            self.connections.append(c)
            self.hubs[h1].connections.append(c)
            self.hubs[h2].connections.append(c)

    class Validate(BaseModel):
        nb_drones: int = Field(ge=0)
        hubs: dict[str, Hub.Validate]
        connections: list[tuple[str, str, Annotated[int, Field(ge=0)]]]

    def solve(self) -> None:
        # create drones[t] for each hub each taken turn, increase turn_count
        # bfs to get better paths and take the one with the most priority hubs
        # to move a drone pop index 0 of list to get the object and append it to the destination list
        pass
