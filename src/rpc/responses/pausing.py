from typing import Final, Optional

from .base import RPCResponse


class Pausing(RPCResponse):
    _method: Final[str] = "PAUSING"
    _rid: int = 0

    position: Optional[float]
