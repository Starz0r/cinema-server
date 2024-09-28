import random
import time
import weakref
from asyncio import CancelledError, Task, create_task, sleep
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Final, Optional

from fastapi import WebSocket
from fastapi.datastructures import State
from pydantic import BaseModel
from sqids.sqids import Sqids

from ..models.mediainfo import MediaInfo
from ..models.queueitem import QueueItem
from ..rpc.responses.base import RPCResponse
from ..rpc.responses.nowplaying import NowPlaying

RNG: Final[random.SystemRandom] = random.SystemRandom()
SQIDS_GEN: Final[Sqids] = Sqids(
    alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_length=4
)
MAX_QUEUE_LEN: Final[int] = 100


class TheaterMinimal(BaseModel):
    name: str
    id: str
    auth_req: bool
    seats: int = 2
    occupancy: int = 0


class Timer:
    __wait_time: float
    __callback: Optional[Callable[[], Coroutine[None, None, Any]]] = None
    __waiter: Optional[Task[None]] = None
    __started_at: float = 0.0
    __paused_at: float = 0.0
    __done: bool = False

    def __init__(
        self,
        wait_time: float,
    ):
        self.__wait_time = wait_time

    def set_callback(
        self,
        callback: Callable[[], Coroutine[None, None, Any]],
    ):
        self.__callback = callback

    def start(self):
        async def __wrapped_timer(
            delay: float,
        ):
            try:
                await sleep(delay)
            except CancelledError as e:
                raise e
            if self.__callback is not None:
                await self.__callback()

        def __set_done(ctx: Task[None]):
            self.__done = True

        self.__waiter = create_task(__wrapped_timer(self.__wait_time))
        self.__waiter.add_done_callback(__set_done, context=None)
        self.__started_at = time.time()

    def pause(self):
        if self.__waiter is None or self.__waiter.done() or self.__waiter.cancelled():
            return
        if not self.__waiter.cancel():
            raise Exception("Timer could not be paused")
        self.__waiter = None
        self.__paused_at = time.time()

    def resume(self):
        if (
            (
                self.__waiter is None
                and self.__paused_at == 0.0
                and self.__started_at == 0.0
            )
            or (self.__waiter is not None and self.__waiter.done())
            or (self.__waiter is not None and self.__waiter.cancelled())
        ):
            return
        self.__wait_time = self.__wait_time - (self.__paused_at - self.__started_at)
        self.__started_at = 0.0
        self.__paused_at = 0.0
        self.start()

    def elapsed(self) -> float:
        return time.time() - self.__started_at

    def abort(self):
        if self.__waiter is None or self.__waiter.done() or self.__waiter.cancelled():
            return
        _ = self.__waiter.cancel()
        self.__waiter = None

    def reschedule(self, wait_time: float):
        self.abort()
        self.__wait_time = wait_time

    async def wait_until_done(self):
        if self.__waiter is None:
            # NOTE: if we don't wait here it'll act as a spinlock instead.
            # which essential will just burn a CPU core.
            await sleep(1)
            return
        print(f"waiting for: {self.__wait_time}")
        await self.__waiter
        self.__waiter = None


@dataclass
class Theater:
    appstate: State
    name: str
    passwd: Optional[str]
    auth_req: bool
    id: str = SQIDS_GEN.encode([RNG.randrange(0, 9999)])
    seats: int = 2
    occupants: list[WebSocket] = field(default_factory=list)
    usernames: list[str] = field(default_factory=list)
    paused: bool = False
    queue: deque[QueueItem] = deque([], maxlen=MAX_QUEUE_LEN)
    nowplaying: Optional[QueueItem] = None
    scheduler: Timer = Timer(-0.0)

    # HACK: getting around python's instantiation model on dataclasses
    def __post_init__(self):
        self.id = SQIDS_GEN.encode([RNG.randrange(0, 9999)])
        self.scheduler = Timer(-0.0)
        self.queue = deque([], maxlen=MAX_QUEUE_LEN)

    def enter(self, occupant: WebSocket):
        self.occupants.append(occupant)

    def leave(self, occupant: WebSocket):
        self.occupants.remove(occupant)

    def seated(self, username: str):
        self.usernames.append(username)

    def unseat(self, username: str):
        self.usernames.remove(username)

    async def main_loop(self):
        try:
            while self.appstate.running:
                try:
                    await self.scheduler.wait_until_done()
                except CancelledError as e:
                    print(e)
                finally:
                    continue
        except KeyboardInterrupt:
            print("loop killed")
            return

    async def broadcast_opcode(self, data: RPCResponse):
        # TODO: convert this to a TaskGroup in py 3.11
        # evloop = get_running_loop()
        # tasks: list[Task[None]] = []
        for occupant in self.occupants:
            await data.send(occupant)
            # tasks.append(evloop.create_task(data.send(occupant)))
        # _ = await gather(*tasks)

    # sets the current media from FIFO queue
    # only call this when the media is finished or
    # you want to force the media to change
    async def pop_queue(self):
        if len(self.queue) == 0:
            self.nowplaying = None
            # QUEST: should we do something with the scheduler here?
            return

        self.nowplaying = self.queue.popleft()
        self.scheduler.reschedule(self.nowplaying.media.duration + 5.0)
        self.scheduler.set_callback(self.pop_queue)
        await self.broadcast_opcode(NowPlaying(_rid=0, media=None))
        self.scheduler.start()

    async def enqueue(self, url: str, title: str, duration: float, submitted_by: str):
        self.queue.append(
            QueueItem(
                media=MediaInfo(url=url, title=title, duration=duration),
                submitted_by=submitted_by,
            )
        )
        print(self.queue)
        if self.nowplaying is None:
            await self.pop_queue()

    def deque(self, index: int):
        try:
            del self.queue[index]
        except IndexError:
            return

    def pause_media(self) -> None:
        if self.paused:
            return
        if self.nowplaying is None:
            return
        self.scheduler.pause()
        self.paused = True

    def resume_media(self) -> None:
        if not self.paused:
            return
        if self.nowplaying is None:
            return
        self.scheduler.resume()
        self.paused = False

    def seek_media(self, position: float) -> None:
        if self.nowplaying is None:
            return
        self.scheduler.abort()
        self.scheduler.reschedule((self.nowplaying.media.duration - position) + 5.0)
        self.scheduler.start()

    # reductive data reference, used for providing information
    # on the theater.
    def as_minimal(self) -> TheaterMinimal:
        return TheaterMinimal(
            name=self.name,
            id=self.id,
            auth_req=self.auth_req,
            seats=self.seats,
            occupancy=len(self.occupants),
        )


class TheaterManager:
    __theaters: dict[str, Theater] = {}

    def insert(self, theater: Theater) -> None:
        id = theater.id
        self.__theaters[id] = theater

    def get(self, id: str) -> weakref.ReferenceType[Theater]:
        if id not in self.__theaters:
            raise IndexError("no room with that id")
        return weakref.ref(self.__theaters[id])

    def get_all(self):
        return self.__theaters.values()
