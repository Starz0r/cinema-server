from typing import Final, Optional

from .base import RPCResponse


class NowPlaying(RPCResponse):
    _method: Final[str] = "NOWPLAYING"
    media: Optional[str]
