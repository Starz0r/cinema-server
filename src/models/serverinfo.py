from pydantic import BaseModel


class ServerInfo(BaseModel):
    version: str = "Cinema 0.0.1"
    protocol: str = "0-alpha.0+0"
