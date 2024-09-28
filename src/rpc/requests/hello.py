from copy import deepcopy
from typing import Optional

from fastapi import WebSocket
from pydantic import BaseModel

from ...models.queueitem import QueueItem
from ...models.roomstate import RoomState
from ...models.theater import Theater
from ..responses.join import Join
from .base import RPCRequest
from .groups import GROUP_V0


class HelloResults(BaseModel):
    occupants: list[str]
    queue: Optional[list[QueueItem]] = None
    roomstate: RoomState


class Hello(RPCRequest):
    name: str
    passwd: Optional[str] = None


@GROUP_V0.register(method="HELLO", clsname=Hello)
async def hello(room: Theater, ws: WebSocket, payload: Hello):
    # TODO: check password here
    results = HelloResults(
        occupants=room.usernames,
        queue=list(deepcopy(room.queue)),
        roomstate=RoomState(
            nowplaying=(
                lambda: "" if room.nowplaying is None else room.nowplaying.media.url
            )(),
            position=(
                lambda: -0.0
                if room.nowplaying is None
                else room.nowplaying.media.duration
            )(),
            paused=room.paused,
        ),
    )
    print(results)
    ws.state.username = payload.name
    await payload.res(ws, results)
    await payload.prop(room, Join(_rid=0, user=payload.name))
    room.seated(payload.name)
