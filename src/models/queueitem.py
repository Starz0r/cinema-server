from pydantic import BaseModel

from .mediainfo import MediaInfo


class QueueItem(BaseModel):
    media: MediaInfo
    submitted_by: str
