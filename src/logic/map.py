from typing import Any, Annotated
from collections import deque

from pydantic import BaseModel, Field

from src.logic import Drone, Hub, Connection


MAX_TURN: int = 10000


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

    def compute_paths(self) -> None:
        assert self.start_hub is not None

        drones: list[Drone] = [Drone() for _ in range(self.nb_drones)]
        paths: dict[Drone, list[Hub | Connection]] = {}
        self.start_hub.drones.setdefault(0, [])
        self.start_hub.drones[0].extend(drones)

        # compute path for each drone
        for d in drones:
            paths[d] = self.find_best_path(d)

        # for each turn, fill the end hub with drones that already reached it
        for i in range(1, self.turn_count):
            for h in self.hubs.values():
                if h == self.end_hub:
                    prev = h.drones.get(i - 1, [])
                    cur = h.drones.setdefault(i, [])
                    for d in prev:
                        if d not in cur:
                            cur.append(d)

        # display logs
        logs: dict[int, list[str]] = {}
        for d in drones:
            for turn in range(1, len(paths[d])):
                cur_node: Hub | Connection = paths[d][turn]
                prev_node: Hub | Connection = paths[d][turn - 1]
                if cur_node == prev_node:
                    continue
                logs.setdefault(turn, []).append(
                    f"D{d.id}-{cur_node.name}"
                )
        for turn in range(1, self.turn_count):
            print(" ".join(logs.get(turn, [])))

    @staticmethod
    def is_node_valid(n: Hub | Connection, turn: int) -> bool:
        if isinstance(n, Hub) and n.zone == "blocked":
            return False
        return len(n.drones.get(turn, [])) < n.max_drones

    @staticmethod
    def get_connection(u: Hub, v: Hub) -> Connection:
        for c in u.linked:
            a, b = c.linked
            if (a is u and b is v) or (a is v and b is u):
                return c
        raise RuntimeError("no connection between hubs")

    @staticmethod
    def add_queue(
        dest_node: Hub | Connection,
        step_count: int,
        from_node: Hub | Connection,
        priority_count: int,
        queue: deque[Hub | Connection],
        step: dict[Hub | Connection, int],
        parents: dict[Hub | Connection, list[tuple[Hub | Connection, int]]]
    ) -> None:
        if dest_node not in step:
            step[dest_node] = step_count
            parents[dest_node] = [(from_node, priority_count)]
            queue.append(dest_node)
        elif step[dest_node] == step_count:
            prev_priority = max(p for _, p in parents[dest_node])
            parents[dest_node].append((from_node, priority_count))
            if priority_count > prev_priority:
                queue.append(dest_node)

    def find_best_path(self, drone: Drone) -> list[Hub | Connection]:
        assert self.start_hub is not None
        assert self.end_hub is not None

        start_turn: int = 0
        while True:

            max_step: float = float("inf")

            queue: deque[Hub | Connection] = deque()
            step: dict[Hub | Connection, int] = {}
            parents: dict[
                Hub | Connection, list[tuple[Hub | Connection, int]]
            ] = {}

            queue.append(self.start_hub)
            step[self.start_hub] = 0
            parents[self.start_hub] = [(self.start_hub, 0)]

            # BFS
            while queue:
                node: Hub | Connection = queue.popleft()
                if step[node] > max_step:
                    continue

                if node == self.end_hub:
                    max_step = step[node]

                node_priority = max(p for _, p in parents[node])
                step_count = step[node] + 1
                turn = start_turn + step_count

                # process Hub
                if isinstance(node, Hub):
                    for c in node.linked:
                        a, b = c.linked
                        dest: Hub = b if node is a else a

                        if not self.is_node_valid(c, turn):
                            continue

                        if dest.zone == "restricted":
                            self.add_queue(
                                c, step_count, node, node_priority,
                                queue, step, parents
                            )
                            continue

                        if not self.is_node_valid(dest, turn):
                            continue

                        dest_prio: int = node_priority + (
                            1 if dest.zone == "priority" else 0
                        )
                        self.add_queue(
                            dest, step_count, node, dest_prio,
                            queue, step, parents
                        )
                # process Connection
                else:
                    for dest in node.linked:
                        if not self.is_node_valid(dest, turn):
                            continue

                        dest_prio = node_priority + (
                            1 if dest.zone == "priority" else 0
                        )
                        self.add_queue(
                            dest, step_count, node, dest_prio,
                            queue, step, parents
                        )

            # must wait
            if self.end_hub not in parents:
                start_turn += 1
                if start_turn > MAX_TURN:
                    raise RuntimeError("can'start_turn find any existing path")
                continue

            # recreate best path
            path: list[Hub | Connection] = []

            prev: Hub | Connection = self.end_hub
            path.append(prev)

            while prev != self.start_hub:
                # care about priority
                prev = max(parents[prev], key=lambda x: x[1])[0]
                path.append(prev)

            path.reverse()

            current_turn_count: int = start_turn + len(path)
            self.turn_count = max(current_turn_count, self.turn_count)

            for wait_turn in range(1, start_turn + 1):
                self.start_hub.drones.setdefault(wait_turn, []).append(drone)

            for i, p in enumerate(path[1:], start=1):
                prev_node = path[i - 1]

                if isinstance(prev_node, Hub) and isinstance(p, Hub):
                    c = self.get_connection(prev_node, p)
                    c.drones.setdefault(start_turn + i, []).append(drone)
                if isinstance(p, Connection):
                    p.drone_count[start_turn + i] = p.drone_count.get(start_turn + i, 0) + 1
                    p.drones.setdefault(start_turn + i, []).append(drone)
                else:
                    p.drones.setdefault(start_turn + i, []).append(drone)

            return [self.start_hub] * (start_turn + 1) + path[1:]
