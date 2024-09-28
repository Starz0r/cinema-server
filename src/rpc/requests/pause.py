from typing import Optional

from fastapi import WebSocket

from ...models.theater import Theater
from ..responses.pausing import Pausing
from .base import RPCRequest
from .groups import GROUP_V0


class Pause(RPCRequest):
    position: Optional[float] = None


@GROUP_V0.register(method="PAUSE", clsname=Pause)
async def pause(room: Theater, ws: WebSocket, payload: Pause):
    # TODO: check authz
    room.pause_media()
    await payload.ok(ws)
    # TODO: pass along position hint
    await payload.prop(room, Pausing(_rid=0, position=None))
