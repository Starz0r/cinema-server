from asyncio import Task, create_task, gather
from typing import ClassVar, Optional

from fastapi import WebSocket
from pydantic import BaseModel

from ...models.theater import Theater
from ..responses.base import RPCResponse
from ..responses.err import Err
from ..responses.ok import Ok
from ..responses.results import Results


class RPCRequest(BaseModel):
    _rid: int

    def set_rid(self, rid: int):
        self._rid = rid

    async def ok(self, ws: WebSocket):
        k = Ok()
        k.set_rid(self._rid)
        await k.send(ws)

    async def err(
        self,
        ws: WebSocket,
        error: str,
        code: int,
        reason: Optional[str] = None,
        details: Optional[str] = None,
    ):
        e: Err = Err(
            _rid=self._rid, err=error, code=code, reason=reason, details=details
        )
        e.set_rid(self._rid)
        await e.send(ws)

    async def res(self, ws: WebSocket, contents: BaseModel):
        r: Results = Results(_rid=self._rid, output=contents)
        r.set_rid(self._rid)
        await r.send(ws)

    async def prop(self, room: Theater, resp: RPCResponse):
        tasks: list[Task[None]] = []
        for occupant in room.occupants:
            tasks.append(create_task(resp.send(occupant)))
        _ = await gather(*tasks)
