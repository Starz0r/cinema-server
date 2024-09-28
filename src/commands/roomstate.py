from typing import Optional

from fastapi import WebSocket
from pydantic import BaseModel

from ..events.update import Update
from ..main import APP, EVLOOP


class RoomState(BaseModel):
    media: Optional[str] = None
    position: float
    paused: bool


async def room_state(id: str, ws: WebSocket, payload: RoomState):
    # TODO: check user authorization
    # TODO: validate room state
    theater = APP.state.rooms[id]

    if payload.paused and theater.scheduler:
        theater.scheduler.cancel()
        theater.scheduler = None
    elif (not payload.paused) and theater.scheduler and theater.nowplaying:
        theater.scheduler.cancel()
        theater.scheduler = EVLOOP.create_task(
            theater.schedule_next(theater.nowplaying.length - payload.position)
        )

    upd = Update(_type="statechange", details=payload)
    for occupant in theater.occupants:
        await occupant.send_text(f"update {upd.model_dump_json()}")
