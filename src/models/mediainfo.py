from pydantic import BaseModel


class MediaInfo(BaseModel):
    url: str
    title: str
    duration: float
