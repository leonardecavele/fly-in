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
            self.hubs[name].drones[0] = []
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
            c.drones[0] = []
            self.connections.append(c)
            self.hubs[h1].linked.append(c)
            self.hubs[h2].linked.append(c)

    class Validate(BaseModel):
        nb_drones: int = Field(ge=0)
        hubs: dict[str, Hub.Validate]
        connections: list[tuple[str, str, Annotated[int, Field(ge=0)]]]

    def solve(self) -> None:
        assert self.start_hub is not None

        paths: list[list[Hub | Connection]] = []
        queue: deque[Hub | Connection] = deque()
        visited: set[Hub | Connection] = set()
        step: dict[Hub | Connection, int] = {}
        max_step: float = float("inf")
        parents: dict[
            Hub | Connection, list[tuple[Hub | Connection, int]]
        ] = {}

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
                    new_path.append(prev)

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

        best_path: list[Hub | Connection] = paths[0]
        best_path.reverse()
        d: Drone = best_path[0].drones[self.turn_count][0]
        for hc in best_path:
            hc.drones.setdefault(self.turn_count, []).append(d)
            self.turn_count += 1

        for i in range(self.turn_count):
            for c in self.connections:
                c.drones.setdefault(i, [])
            for h in self.hubs.values():
                h.drones.setdefault(i, [])
