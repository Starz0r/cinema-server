from dataclasses import dataclass
from typing import Annotated, Final, Optional, cast

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    Request,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    status,
)
from pydantic import BaseModel, ValidationError

from ..models.problem import Problem
from ..models.theater import Theater, TheaterManager, TheaterMinimal
from ..rpc.manager import RPCManager

MAX_QUEUE_LEN: Final[int] = 100

ROUTER: Final[APIRouter] = APIRouter()


class CreateTheaterResponse(BaseModel):
    id: str
    name: str
    passwd: Optional[str]
    auth_req: bool
    seats: int = 2
    occupancy: int = 0

    def from_theater(self, theater: Theater):
        self.id = theater.id
        self.name = theater.name
        self.passwd = theater.passwd
        self.auth_req = theater.auth_req
        self.seats = theater.seats
        self.occupancy = len(theater.occupants)


@dataclass
class TheaterRequest:
    name: str
    passwd: Optional[str]
    auth_req: bool
    seats: int = 2

    def into_theater(self) -> Theater:
        return Theater(self.name, self.passwd, self.auth_req, seats=self.seats)


async def state_theatermanager(req: Request) -> TheaterManager:
    app: FastAPI = cast(FastAPI, req.app)  # type: ignore[no-any-expr]
    rooms: TheaterManager = cast(TheaterManager, app.state.rooms)  # type: ignore[no-any-expr]
    return rooms


RoomsDep = Annotated[TheaterManager, Depends(state_theatermanager)]


async def state_theatermanager_ws(req: WebSocket) -> TheaterManager:
    app: FastAPI = cast(FastAPI, req.app)  # type: ignore[no-any-expr]
    rooms: TheaterManager = cast(TheaterManager, app.state.rooms)  # type: ignore[no-any-expr]
    return rooms


RoomsDepWS = Annotated[TheaterManager, Depends(state_theatermanager_ws)]


async def state_rpcmanager(req: WebSocket) -> RPCManager:
    app: FastAPI = cast(FastAPI, req.app)  # type: ignore[no-any-expr]
    rpcman: RPCManager = cast(RPCManager, app.state.rpcman)  # type: ignore[no-any-expr]
    return rpcman


RPCDep = Annotated[RPCManager, Depends(state_rpcmanager)]


@ROUTER.post("/theaters")
async def create_theater(rooms: RoomsDep, content: TheaterRequest):
    # TODO: unimplemented for now
    return Problem(
        "/errors/unimplemented",
        "API Call is unimplemented",
        501,
        "This API Call is not implemented currently and is unavailable",
        f"/theaters",
    )
    # theater = content.into_theater()
    # rooms.insert(theater)
    # del content
    # return rooms.get(theater.id).as_created_response(id)


@ROUTER.get("/theaters")
async def list_theaters(rooms: RoomsDep) -> list[TheaterMinimal]:
    theaters: list[TheaterMinimal] = []
    for room in rooms.get_all():
        theaters.append(room.as_minimal())
    return theaters


@ROUTER.get("/theaters/{id}")
async def query_theater(rooms: RoomsDep, id: str):
    try:
        theater = rooms.get(id)()
        if theater is None:
            raise TypeError("Theater weakref evaluated to None")
        return theater.as_minimal()
    except (IndexError, ValidationError, TypeError) as e:
        # G_LOGGER.warn("theater with id does not exist", id=id, err=e)
        return Problem(
            "/errors/not-found",
            "Resource Does Not Exist",
            404,
            "The resource specified is missing and does not exist.",
            f"/theaters/{id}",
        )


@ROUTER.websocket("/theaters/{id}/rpc/ws")
async def rpc_ws_theater(*, rooms: RoomsDepWS, rpc: RPCDep, ws: WebSocket, id: str):
    try:
        theater = rooms.get(id)()
        if theater is None:
            raise TypeError("Theater weakref evaluated to None")
        if len(theater.occupants) >= theater.seats:
            # G_LOGGER.info(
            # "no occupancy, theater is full!",
            # occupancy=len(theater.occupants),
            # seats=theater.seats,
            # )
            return
    except (IndexError, TypeError) as e:
        # G_LOGGER.warn("user tried to join non-existant theater.", id=id, err=e)
        return await ws.close(status.WS_1001_GOING_AWAY, "this theater does not exist!")

    await ws.accept()
    try:
        # TODO: check the password
        theater.enter(ws)
        while True:
            await rpc.perform_dispatch(theater, ws)
    except WebSocketException as e:
        pass
        # G_LOGGER.error("eventstream client dispatcher ran into a problem.", err=e)
    except WebSocketDisconnect as e:
        pass
        # G_LOGGER.debug("client disconnected from eventstream.", err=e)
    theater.leave(ws)
