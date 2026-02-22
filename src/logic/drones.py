class Drone():
    """
    Simple drone model with an auto-incremented id.

    Attributes
    ----------
    max_registered_id
        Class-level counter for assigning new ids.
    """
    max_registered_id: int = 0

    def __init__(self) -> None:
        """
        Create a new Drone.

        Assign a unique id and increment the class counter.
        """
        self.id = Drone.max_registered_id
        Drone.max_registered_id += 1
