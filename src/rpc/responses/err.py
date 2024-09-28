from typing import Final, Optional

from .base import RPCResponse


class Err(RPCResponse):
    _method: Final[str] = "ERR"
    _rid: int

    err: str
    code: Optional[int] = None
    reason: Optional[str] = None
    details: Optional[str] = None
