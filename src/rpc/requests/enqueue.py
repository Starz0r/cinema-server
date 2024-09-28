from typing import cast

from fastapi import WebSocket
from yt_dlp import DownloadError, YoutubeDL

from ...models.theater import Theater
from ..responses.enqueued import Enqueued
from .base import RPCRequest
from .groups import GROUP_V0


class Enqueue(RPCRequest):
    url: str


@GROUP_V0.register(method="ENQUEUE", clsname=Enqueue)
async def enqueue(room: Theater, ws: WebSocket, payload: Enqueue):
    # TODO: check authz
    with YoutubeDL() as ytdl:
        try:
            info = ytdl.extract_info(payload.url, download=False)
        except DownloadError as e:
            return await payload.err(
                ws,
                "FETCHINFO",
                3,
                "Could not fetch infomation on the requested media.",
                f"{e}",
            )
        if info is None:
            return
        if type(info) is not dict:
            return
        # not having duration is a hard-error, we rely
        # on this information too much not to have it
        try:
            duration = info["duration"]
        except KeyError as e:
            return await payload.err(
                ws,
                "PARTIALINFO",
                3,
                "The requested media did not have a known length.",
                f"{e}",
            )

        title = info.get("title", "")
        if type(title) is not str:
            title = ""
        try:
            if type(duration) is not float:
                duration = float(duration)
        except ValueError as e:
            return
        username = cast(str, ws.state.username)  # type: ignore[no-any-expr]
        await payload.ok(ws)
        await payload.prop(
            room, Enqueued(_rid=0, url=payload.url, media=None, submitted_by=username)
        )
        # this step has to be done last as it might propagate a
        # NOWPLAYING opcode to all listeners when there was nothing
        # in the queue before
        await room.enqueue(payload.url, title, duration, username)
