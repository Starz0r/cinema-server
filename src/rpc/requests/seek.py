from fastapi import WebSocket

from ...models.theater import Theater
from ..responses.seeking import Seeking
from .base import RPCRequest
from .groups import GROUP_V0


class Seek(RPCRequest):
    position: float


@GROUP_V0.register(method="SEEK", clsname=Seek)
async def seek(room: Theater, ws: WebSocket, payload: Seek):
    # TODO: check authz
    # TODO: validate that position is within the duration
    room.seek_media(payload.position)
    await payload.ok(ws)
    await payload.prop(room, Seeking(_rid=0, position=payload.position))
