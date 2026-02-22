from typing import Any, Annotated
from collections import deque

from pydantic import BaseModel, Field

from src.logic import Drone, Hub, Connection


MAX_TURN: int = 10000


class Map():
    """
    Map model with hubs, connections, and routing logic.
    """
    def __init__(
        self,
        nb_drones: int,
        hubs: dict[str, dict[str, Any]],
        connections: list[tuple[str, str, int]]
    ) -> None:
        """
        Create a Map from parsed specs.

        Instantiate hubs and connections from validated input data.

        Parameters
        ----------
        nb_drones
            Number of drones to simulate.
        hubs
            Hub specs from the parser.
        connections
            Connection specs from the parser.
        """
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
        """
        Pydantic model used to validate map specs.

        Attributes
        ----------
        nb_drones
            Number of drones to simulate.
        hubs
            Validated hub specifications.
        connections
            Validated connection specifications.
        """
        nb_drones: int = Field(ge=0)
        hubs: dict[str, Hub.Validate]
        connections: list[tuple[str, str, Annotated[int, Field(ge=0)]]]

    def display_logs(
        self, drones: list[Drone], paths: dict[Drone, list[Hub | Connection]]
    ) -> None:
        """
        Print per-turn movement logs.

        Format and print the computed path for each drone.

        Parameters
        ----------
        drones
            List of drones to display.
        paths
            Computed path for each drone.
        """
        logs: dict[int, list[str]] = {}
        for d in drones:
            for turn in range(1, len(paths[d])):
                node: Hub | Connection = paths[d][turn]
                prev_node: Hub | Connection = paths[d][turn - 1]
                if node == prev_node:
                    continue
                logs.setdefault(turn, []).append(
                    f"D{d.id}-{node.name}"
                )
        for turn in range(1, self.turn_count):
            print(" ".join(logs.get(turn, [])))

    def compute_paths(self) -> None:
        """
        Compute paths for all drones.

        Compute each drone path and update per-turn occupancy.
        """
        assert self.start_hub is not None

        drones: list[Drone] = [Drone() for _ in range(self.nb_drones)]
        paths: dict[Drone, list[Hub | Connection]] = {}
        self.start_hub.drones.setdefault(0, [])
        self.start_hub.drones[0].extend(drones)

        # compute path for each drone
        for d in drones:
            paths[d] = self.find_best_path(d)

            # fill path
            for i, node in enumerate(paths[d]):
                if node == self.start_hub:
                    continue
                prev_node = paths[d][i - 1]
                if isinstance(prev_node, Hub) and isinstance(node, Hub):
                    c = self.get_connection(prev_node, node)
                    c.drones.setdefault(i, []).append(d)

                if isinstance(node, Connection):
                    node.drone_count[i] = node.drone_count.get(i, 0) + 1
                    node.drones.setdefault(i, []).append(d)
                else:
                    node.drones.setdefault(i, []).append(d)

        # get turn_count
        self.turn_count = max(len(p) for p in paths.values())

        # for each turn, fill the end hub with drones that already reached it
        for i in range(1, self.turn_count):
            for h in self.hubs.values():
                if h == self.end_hub:
                    prev = h.drones.get(i - 1, [])
                    cur = h.drones.setdefault(i, [])
                    for d in prev:
                        if d not in cur:
                            cur.append(d)

        self.display_logs(drones, paths)

    @staticmethod
    def is_node_valid(n: Hub | Connection, turn: int) -> bool:
        """
        Check if a node is available.

        Enforce capacity and blocked-zone rules for a given turn.

        Parameters
        ----------
        n
            Hub or connection to check.
        turn
            Turn index to check.

        Returns
        -------
        bool
            True if the node can accept a drone at this turn.
        """
        if isinstance(n, Hub) and n.zone == "blocked":
            return False
        return len(n.drones.get(turn, [])) < n.max_drones

    @staticmethod
    def get_connection(u: Hub, v: Hub) -> Connection:
        """
        Get the connection between two hubs.

        Search linked edges and return the matching connection.

        Parameters
        ----------
        u
            First endpoint hub.
        v
            Second endpoint hub.

        Returns
        -------
        Connection
            Connection linking the two hubs.

        Raises
        ------
        RuntimeError:
            Raised if no connection exists between the hubs.
        """
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
        """
        Update search state for a queued node.

        Record steps and parents, then enqueue nodes when needed.

        Parameters
        ----------
        dest_node
            Candidate node to enqueue.
        step_count
            Step count to reach dest_node.
        from_node
            Parent node for dest_node.
        priority_count
            Priority used to break ties.
        queue
            Search queue.
        step
            Best step count per node.
        parents
            Parent tracking per node.
        """
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
        """
        Find the best path for one drone.

        Search a valid route from start to end with constraints.

        Parameters
        ----------
        drone
            Drone to route.

        Returns
        -------
        list[Hub | Connection]
            Sequence of hubs and connections for this drone.

        Raises
        ------
        RuntimeError:
            Raised if no valid path can be found.
        """
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

            # fill wait at start hub
            for wait_turn in range(1, start_turn + 1):
                self.start_hub.drones.setdefault(wait_turn, []).append(drone)

            # recreate best path
            path: list[Hub | Connection] = []

            prev: Hub | Connection = self.end_hub
            path.append(prev)

            while prev != self.start_hub:
                # care about priority
                prev = max(parents[prev], key=lambda x: x[1])[0]
                path.append(prev)
            path.reverse()
            start_padding: list[Hub | Connection] = [
                self.start_hub
            ] * (start_turn + 1)
            path = start_padding + path[1:]

            return path
