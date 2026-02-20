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

    def compute_paths(self) -> None:
        assert self.start_hub is not None

        drones: list[Drone] = [Drone() for _ in range(self.nb_drones)]
        paths: dict[Drone, list[Hub | Connection]] = {}
        self.start_hub.drones.setdefault(0, [])
        self.start_hub.drones[0].extend(drones)

        # compute path for each drone
        for d in drones:
            paths[d] = self.find_best_path(d)

        # for each turn, fill the end_hub with drones that already reached it
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
            for t in range(1, len(paths[d])):
                cur_node: Hub | Connection = paths[d][t]
                prev_node: Hub | Connection = paths[d][t - 1]
                if cur_node == prev_node:
                    continue
                logs.setdefault(t, []).append(f"D{d.id}-{cur_node.name}")

        for t in range(1, self.turn_count):
            print(logs.get(t, []))

    def find_best_path(self, drone: Drone) -> list[Hub | Connection]:
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

            def relax(
                node: Hub | Connection,
                new_step: int,
                parent_node: Hub | Connection,
                priority_count: int,
            ) -> None:
                if node not in step:
                    step[node] = new_step
                    parents[node] = [(parent_node, priority_count)]
                    queue.append(node)
                elif step[node] == new_step:
                    old_best = max(p for _, p in parents[node])
                    parents[node].append((parent_node, priority_count))
                    if priority_count > old_best:
                        queue.append(node)

            queue.append(self.start_hub)
            step[self.start_hub] = 0
            parents[self.start_hub] = [(self.start_hub, 0)]

            while queue:
                current: Hub | Connection = queue.popleft()
                if step[current] > max_step:
                    continue

                if current == self.end_hub:
                    max_step = step[current]

                cur_prio = max(p for _, p in parents[current])
                new_step = step[current] + 1
                real_turn = t + new_step

                if isinstance(current, Hub):
                    for conn in current.linked:
                        a, b = conn.linked
                        dest: Hub = b if current is a else a

                        if dest.zone == "blocked":
                            continue

                        if dest.zone == "restricted":
                            if len(
                                conn.drones.get(real_turn, [])
                            ) >= conn.max_drones:
                                continue
                            relax(conn, new_step, current, cur_prio)
                            continue
                        if len(conn.drones.get(
                            real_turn, [])
                        ) >= conn.max_drones:
                            continue
                        if not self.is_hub_ok(dest, real_turn):
                            continue

                        prio2 = cur_prio + (
                            1 if dest.zone == "priority" else 0
                        )
                        relax(dest, new_step, current, prio2)
                else:
                    conn = current
                    for dest in conn.linked:
                        if dest.zone == "blocked":
                            continue
                        if not self.is_hub_ok(dest, real_turn):
                            continue

                        prio2 = cur_prio + (
                            1 if dest.zone == "priority" else 0
                        )
                        relax(dest, new_step, conn, prio2)

            if t > 10000:
                raise RuntimeError("can't find any existing path")

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

            def get_conn(u: Hub, v: Hub) -> Connection:
                for c in u.linked:
                    a, b = c.linked
                    if (a is u and b is v) or (a is v and b is u):
                        return c
                raise RuntimeError("no connection between hubs")

            for i, p in enumerate(path[1:], start=1):
                prev_node = path[i - 1]

                if isinstance(prev_node, Hub) and isinstance(p, Hub):
                    conn = get_conn(prev_node, p)
                    conn.drones.setdefault(t + i, []).append(drone)
                if isinstance(p, Connection):
                    p.drone_count[t + i] = p.drone_count.get(t + i, 0) + 1
                    p.drones.setdefault(t + i, []).append(drone)
                else:
                    p.drones.setdefault(t + i, []).append(drone)

            return [self.start_hub] * (t + 1) + path[1:]
