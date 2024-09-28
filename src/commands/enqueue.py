import asyncio
import functools
import os
from typing import Final

import requests
from fastapi import WebSocket
from pydantic import BaseModel

from ..events.err import Err
from ..events.update import Update
from ..main import APP, EVLOOP
from .queue import QueueItem

YTDL_SVC_AGENT_URL: Final[str] = os.environ["YTDL_SVC_AGENT_URL"]


class Enqueue(BaseModel):
    media: str


class MediaInfo(BaseModel):
    url: str
    title: str
    duration: float


async def enqueue(id: str, ws: WebSocket, payload: Enqueue):
    # TODO: check user authorization
    # TODO: validate room state
    theater = APP.state.rooms[id]
    resp = await EVLOOP.run_in_executor(
        EVLOOP,
        functools.partial(
            requests.get,
            url=f"http://{YTDL_SVC_AGENT_URL}/api/v0/media_info",
            json={"url": payload.media},
        ),
    )
    if resp.status_code != 200:
        err = Err(err="unable to get information on media")
        return await ws.send_text(f"err {err.model_dump_json()}")

    info = MediaInfo.model_validate(resp.json())
    item = QueueItem(
        media=info.url, title=info.title, length=info.duration, added_by="anon"
    )
    upd = Update(_type="enqueued", details=item)
    await asyncio.gather(
        *[
            ws.send_text("ok"),
            theater.broadcast_text(f"update {upd.model_dump_json()}"),
        ],
    )

    if theater.scheduler is None and theater.nowplaying is None:
        upd = Update(_type="nowplaying", details={})
        await theater.broadcast_text(f"update {upd.model_dump_json()}")
        theater.nowplaying = item
        theater.scheduler = EVLOOP.create_task(theater.schedule_next(info.duration))
    else:
        theater.queue.append(item)
