from typing import Final

from .base import RPCResponse


class Resuming(RPCResponse):
    _method: Final[str] = "RESUMING"
    _rid: int = 0
