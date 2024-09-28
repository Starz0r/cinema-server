from typing import Final

from .base import RPCResponse


class Seeking(RPCResponse):
    _method: Final[str] = "SEEKING"
    _rid: int = 0

    position: float
