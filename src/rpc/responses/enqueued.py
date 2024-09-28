from typing import Final, Optional

from ...models.mediainfo import MediaInfo
from .base import RPCResponse


class Enqueued(RPCResponse):
    _method: Final[str] = "ENQUEUED"
    _rid: int = 0

    url: str
    media: Optional[MediaInfo] = None
    submitted_by: Optional[str] = None
