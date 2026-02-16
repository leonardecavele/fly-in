class Drone():
    n_id: int = 0

    def __init__(self) -> None:
        self.id = Drone.n_id
        Drone.n_id += 1
