from typing import Any, Annotated
from collections import deque

from pydantic import BaseModel, Field

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
        self.start_hub: Hub | None = None
        self.end_hub: Hub | None = None

        for name, data in hubs.items():
            self.hubs[name] = Hub(name, **data)
            self.hubs[name].drones.append(list())
            if "start_hub" in data:
                self.start_hub = self.hubs[name]
                for _ in range(nb_drones):
                    self.hubs[name].drones[0].append(Drone())
            if "end_hub" in data:
                self.end_hub = self.hubs[name]

        for h1, h2, max_drones in connections:
            c: Connection = Connection(
                self.hubs[h1], self.hubs[h2], max_drones
            )
            c.drones.append(list())
            self.connections.append(c)
            self.hubs[h1].linked.append(c)
            self.hubs[h2].linked.append(c)

    class Validate(BaseModel):
        nb_drones: int = Field(ge=0)
        hubs: dict[str, Hub.Validate]
        connections: list[tuple[str, str, Annotated[int, Field(ge=0)]]]

    def solve(self) -> None:
        # create drones[t] for each hub each taken turn, increase turn_count
        # bfs to get better paths and take the one with the most priority hubs
        # to move a drone pop index 0 of list to get the object and append 
        # it to the destination list

        paths: list[list[Hub | Connection]] = []

        assert self.start_hub is not None
        queue: deque[Hub | Connection] = deque()
        visited: set[Hub | Connection] = set()
        step: dict[Hub | Connection, int] = {}
        max_step: float = float("inf")
        parents: dict[
            Hub | Connection, list[tuple[Hub | Connection, int]]
        ] = {}

        visited.add(self.start_hub)
        queue.append(self.start_hub)
        step[self.start_hub] = 0
        parents[self.start_hub] = [(self.start_hub, 0)]
        while queue:
            current: Hub | Connection = queue.popleft()
            if step[current] > max_step:
                break

            if current == self.end_hub:
                max_step = step[current]

                new_path: list[Hub | Connection] = []
                new_path.append(current)
                prev: Connection | Hub = current
                while prev != self.start_hub:
                    prev = max(parents[prev], key=lambda t: t[1])[0]

                paths.append(new_path)

            for to_explore in current.linked:
                if to_explore not in visited:
                    priority_count: int = max(p for _, p in parents[current])
                    if (
                        isinstance(to_explore, Hub)
                        and to_explore.zone == "priority"
                    ):
                        priority_count += 1
                    parents.setdefault(to_explore, []).append(
                        (current, priority_count)
                    )
                    step[to_explore] = step[current] + 1
                    queue.append(to_explore)
                    visited.add(to_explore)

        for path in paths:
            print(path)
