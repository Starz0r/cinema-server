from typing import Final

from .base import RPCResponse


class Ok(RPCResponse):
    _method: Final[str] = "OK"
    _rid: int
