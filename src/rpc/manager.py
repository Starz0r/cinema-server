from typing import Final

from fastapi import WebSocket
from pydantic import ValidationError

from ..models.theater import Theater
from .handlergroup import RPCHandler
from .requests.base import RPCRequest

MAX_COMMAND_LEN: Final[int] = 1024


class RPCManager:
    __handlers: dict[str, tuple[RPCHandler, type[RPCRequest]]] = {}

    def get_handlers(self) -> dict[str, tuple[RPCHandler, type[RPCRequest]]]:
        return self.__handlers

    def import_handlers(
        self, handlers: dict[str, tuple[RPCHandler, type[RPCRequest]]]
    ) -> None:
        self.__handlers = self.__handlers | handlers

    async def perform_dispatch(self, room: Theater, ws: WebSocket):
        data = await ws.receive_text()

        if len(data) > MAX_COMMAND_LEN:
            # LOGGER.warn("command is too large", _len=len(data), max=MAX_COMMAND_LEN)
            return
        try:
            rid, method, payload_json = data.split(" ", maxsplit=2)
        except ValueError:
            # LOGGER.warn("not enough spaces in message", err=e)
            return

        handler_info = self.__handlers.get(method)
        if not handler_info:
            # LOGGER.warn("no handler exists for the specified method", method=method)
            return
        handler, clsname = handler_info

        try:
            rid = int(rid)
        except ValueError:
            # LOGGER.warn("rid was not a number", err=e)
            return

        try:
            payload = clsname.model_validate_json(json_data=payload_json)
        except ValidationError as e:
            # LOGGER.warn("malformed json in payload", err=e)
            return
        payload.set_rid(rid)

        await handler(room, ws, payload)
