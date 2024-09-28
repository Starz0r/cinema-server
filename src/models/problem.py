from typing import Any, Dict, Mapping, Optional, Union

import ujson
from fastapi import Response


class Problem(Response):
    media_type: str = "application/problem+json"
    content: Dict[str, Union[str, int]] = {}

    def __init__(
        self,
        _type: str,
        title: str,
        status: int,
        detail: str,
        instance: str,
        status_code: int = 200,
        headers: Optional[Mapping[str, str]] = None,
        background: Optional[Any] = None,
    ):
        self.content = {
            "type": _type,
            "title": title,
            "status": status,
            "detail": detail,
            "instance": instance,
        }
        super().__init__(
            self.content, status_code, headers, self.media_type, background
        )

    def render(self, content) -> bytes:
        return ujson.dumps(content).encode("utf-8")
