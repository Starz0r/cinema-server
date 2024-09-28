from typing import Final, Optional

from .base import RPCResponse


class Dequeued(RPCResponse):
    _method: Final[str] = "DEQUEUED"
    _rid: int = 0

    index: int
    url: Optional[str]
