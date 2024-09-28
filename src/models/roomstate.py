from pydantic import BaseModel


class RoomState(BaseModel):
    nowplaying: str
    position: float
    paused: bool
