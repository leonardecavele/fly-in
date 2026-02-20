class Drone():
    max_registered_id: int = 0

    def __init__(self) -> None:
        self.id = Drone.max_registered_id
        Drone.max_registered_id += 1
