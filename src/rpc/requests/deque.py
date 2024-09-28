from fastapi import WebSocket

from ...models.theater import Theater
from ..responses.dequeued import Dequeued
from .base import RPCRequest
from .groups import GROUP_V0


class Deque(RPCRequest):
    index: int


@GROUP_V0.register(method="DEQUE", clsname=Deque)
async def deque(room: Theater, ws: WebSocket, payload: Deque):
    # TODO: check if user owns submission
    # TODO: check authz
    room.deque(payload.index)
    await payload.ok(ws)
    await payload.prop(room, Dequeued(_rid=0, index=payload.index, url=None))
