from fastapi import WebSocket

from ...models.theater import Theater
from ..responses.resuming import Resuming
from .base import RPCRequest
from .groups import GROUP_V0


class Resume(RPCRequest):
    pass


@GROUP_V0.register(method="RESUME", clsname=Resume)
async def resume(room: Theater, ws: WebSocket, payload: Resume):
    # TODO: check authz
    room.resume_media()
    await payload.ok(ws)
    await payload.prop(room, Resuming(_rid=0))
