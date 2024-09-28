from fastapi import WebSocket
from pydantic import BaseModel


class RPCResponse(BaseModel):
    _method = "BASE"
    _rid = 0

    async def send(self, ws: WebSocket):
        await ws.send_text(f"{self._rid} {self._method} {self.model_dump_json()}")

    def set_rid(self, rid: int) -> None:
        self._rid = rid
