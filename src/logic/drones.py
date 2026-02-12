from pydantic import BaseModel, Field


class Drone(BaseModel):
    n_id: int = Field(ge=0)
