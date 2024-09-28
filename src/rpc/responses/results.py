from typing import Any, Final, Union

from pydantic import BaseModel, field_serializer

from .base import RPCResponse


class Results(RPCResponse):
    _method: Final[str] = "RESULTS"
    _rid: int = 0

    output: Union[dict[str, Any], BaseModel]

    @field_serializer("output")
    def serialize_nested_output_field(self, output):
        return output.model_dump()
