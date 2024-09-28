import time

from fastapi import WebSocket
from pydantic import BaseModel


class Ping(BaseModel):
    rtt: float = time.time()


async def ping(id: str, ws: WebSocket, payload: Ping):
    await ws.send_text(f"pong {Ping().model_dump_json()}")
