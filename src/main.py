import asyncio
import signal
import sys
from os import getenv
from typing import Final

import anyio
import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from .models.problem import Problem
from .models.serverinfo import ServerInfo
from .models.theater import Theater, TheaterManager
from .routers import theaters
from .rpc.manager import RPCManager
from .rpc.requests import (  # pyright: ignore[reportUnusedImport] # type: ignore # noqa F401
    deque,
    enqueue,
    hello,
    pause,
    resume,
    seek,
)
from .rpc.requests.groups import GROUP_V0

APP: Final[FastAPI] = FastAPI()
LOGGER: Final[structlog.stdlib.BoundLogger] = structlog.getLogger()
EVLOOP: Final[asyncio.AbstractEventLoop] = asyncio.get_event_loop()


@APP.get("/api", tags=["_openapi"])
async def openapi():
    return APP.openapi_schema


@APP.get("/", tags=["_root"])
async def index() -> Problem:
    return Problem(
        "https://example.com/errors/all-systems-go",
        "All Systems Ready!",
        200,
        "Nothing is wrong, and this response merely exists to inform the operatiors everything is ok.",
        "/",
    )


@APP.get("/info", tags=["_root"])
async def info() -> ServerInfo:
    return ServerInfo()


@APP.on_event("shutdown")
def on_shutdown():
    APP.state.running = False


async def main() -> int:
    APP.state.running = True

    #LOGGER.info("activating CORS middleware")
    #origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    #APP.add_middleware(
    #    CORSMiddleware,
    #    allow_origins=origins,
    #    allow_credentials=True,
    #    allow_methods=["*"],
    #    allow_headers=["*"],
    #)

    LOGGER.info("exposing Theaters REST API")
    APP.include_router(theaters.ROUTER, prefix="/api/v0", tags=["theaters"])

    LOGGER.info("generating and exposing the OpenAPI schema")
    openapi_schema = get_openapi(
        title="Cinema API",
        version="0.0.1",
        description="Watch videos together.",
        routes=APP.routes,
        servers=[{"url": "http://localhost:5050"}],
    )
    APP.openapi_schema = openapi_schema

    LOGGER.info("setting up RPC management")
    APP.state.rpcman = RPCManager()

    LOGGER.info("assigning handlers for RPC v0 commands")
    APP.state.rpcman.import_handlers(GROUP_V0.export_handlers())

    LOGGER.info("setting up app state management")
    APP.state.rooms = TheaterManager()

    LOGGER.info("setting up default rooms")
    try:
        default_room_amt = int(getenv("DEFAULT_THEATER_AMT", default=4))
    except ValueError as e:
        LOGGER.warn(
            "DEFAULT_THEATER_AMT was set but was not a valid number, defaulting to 4",
            err=e,
        )
        default_room_amt = 4
    try:
        default_seat_amt: int = int(getenv("DEFAULT_THEATER_MAX_OCCUPANCY", default=8))
    except ValueError as e:
        LOGGER.warn(
            "DEFAULT_THEATER_MAX_OCCUPANCY was set but was not a valid number, defaulting to 8",
            err=e,
        )
        default_seat_amt = 8
    for i in range(default_room_amt):
        APP.state.rooms.insert(
            Theater(
                appstate=APP.state,
                name=f"Theater {i + 1}",
                passwd=None,
                auth_req=False,
                seats=default_seat_amt,
            )
        )

    LOGGER.info("starting the HTTP server")
    uv_cfg = uvicorn.Config(APP, host="0.0.0.0", port=5050, log_level="debug")
    srv = uvicorn.Server(uv_cfg)

    for room in APP.state.rooms.get_all():
        LOGGER.debug("Running Theater's main loop", theater=room)

    async def sig_handler(scope: anyio.CancelScope) -> None:
        with anyio.open_signal_receiver(
            signal.SIGTERM, signal.SIGHUP, signal.SIGINT
        ) as signals:
            async for signum in signals:
                _ = scope.cancel()
                await scope.cancel()

    async with anyio.create_task_group() as tg:
        APP.state.tg = tg
        # tg.start_soon(sig_handler, tg.cancel_scope)

        tg.start_soon(srv.serve)
        for room in APP.state.rooms.get_all():
            tg.start_soon(room.main_loop)

    LOGGER.info("application has finished, shutting down...")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
