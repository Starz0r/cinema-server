from typing import Final

from .base import RPCResponse


class Join(RPCResponse):
    _method: Final[str] = "JOIN"
    _rid: int = 0

    user: str
