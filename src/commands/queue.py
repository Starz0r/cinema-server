from typing import List

from fastapi import WebSocket
from pydantic import BaseModel


class QueueItem(BaseModel):
    media: str
    title: str
    length: float
    added_by: str


class QueueDetails(BaseModel):
    queue: List[QueueItem] = []


class QueueUpdated(BaseModel):
    item: QueueItem


async def queue_details(id: str, ws: WebSocket, payload: QueueDetails):
    # TODO: check user authorization
    # TODO: validate room state
    # theater = APP.state.rooms[id]
    # await theater.broadcast_text(f"roomstate {payload.model_dump_json()}")
    pass


async def queue_updated(id: str, payload: QueueUpdated):
    # theater = APP.state.rooms[id]
    # await theater.broadcast_text(f"queueupdated {payload.model_dump_json()}")
    pass
