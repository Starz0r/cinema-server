from typing import Any, Final, Union

from pydantic import BaseModel

from .base import RPCResponse


class Update(RPCResponse):
    _method: Final[str] = "UPDATE"

    t: str
    details: Union[dict[str, Any], BaseModel]
