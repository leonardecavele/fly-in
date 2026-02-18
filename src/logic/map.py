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
        self.nb_drones: int = nb_drones

        for name, data in hubs.items():
            self.hubs[name] = Hub(name, **data)
            self.hubs[name].drones[0] = []
            if "start_hub" in data:
                self.start_hub = self.hubs[name]
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

    @staticmethod
    def is_hub_ok(h: Hub, turn: int) -> bool:
        if h.zone == "blocked":
            return False
        return len(h.drones.get(turn, [])) < h.max_drones

    def solve(self) -> None:
        assert self.start_hub is not None

        drones = [Drone() for _ in range(self.nb_drones)]
        self.start_hub.drones.setdefault(0, [])
        self.start_hub.drones[0].extend(drones)

        for d in drones:
            self.algorithm(d)

        for i in range(self.turn_count):
            for c in self.connections:
                c.drones.setdefault(i, [])
            for h in self.hubs.values():
                h.drones.setdefault(i, [])

    def algorithm(self, drone: Drone) -> None:
        assert self.start_hub is not None
        assert self.end_hub is not None

        t = 0
        while True:
            queue: deque[Hub | Connection] = deque()
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
                    continue

                if current == self.end_hub:
                    max_step = step[current]

                for to_explore in current.linked:

                    new_step = step[current] + 1
                    real_turn = t + new_step

                    if len(
                        to_explore.drones.get(real_turn, [])
                    ) >= to_explore.max_drones:
                        continue

                    priority_count = max(p for _, p in parents[current])
                    if isinstance(
                        to_explore, Hub
                    ) and to_explore.zone == "priority":
                        priority_count += 1

                    if isinstance(to_explore, Connection):
                        a, b = to_explore.linked
                        dest_hub: Hub = b if a in step else a
                        prev_hub: Hub = a if a in step else a
                        if dest_hub.zone == "blocked":
                            continue
                        elif dest_hub.zone != "restricted":
                            step[dest_hub] = new_step
                            parents.setdefault(
                                dest_hub, []
                            ).append((prev_hub, priority_count))
                            queue.append(dest_hub)

                    if to_explore not in step:
                        step[to_explore] = new_step
                        parents[to_explore] = [(current, priority_count)]
                        queue.append(to_explore)
                    elif step[to_explore] == new_step:
                        old_best = max(p for _, p in parents[to_explore])
                        parents[to_explore].append((current, priority_count))
                        if priority_count > old_best:
                            queue.append(to_explore)



            if t > 10000:
                return # raise and display msg not exit & repair display center

            if self.end_hub not in parents:
                t += 1
                continue

            path: list[Hub | Connection] = []
            prev: Hub | Connection = self.end_hub
            path.append(prev)

            while prev != self.start_hub:
                prev = max(parents[prev], key=lambda x: x[1])[0]
                path.append(prev)

            path.reverse()

            current_turn_count: int = t + len(path)
            self.turn_count = max(current_turn_count, self.turn_count)

            for wait_turn in range(1, t + 1):
                self.start_hub.drones.setdefault(wait_turn, []).append(drone)

            for i, p in enumerate(path[1:], start=1):
                p.drones.setdefault(t + i, []).append(drone)

            return
