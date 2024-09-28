from collections.abc import Awaitable
from typing import Any, Callable, Final, TypeVar

from fastapi import WebSocket

from ..models.theater import Theater
from .requests.base import RPCRequest

# HACK:uncomment on py 3.10
# RPCHandler: TypeAlias = Callable[[str, WebSocket, RPCRequest], Awaitable[Any]]
RPCHandler = TypeVar(
    "RPCHandler", bound=Callable[[Theater, WebSocket, RPCRequest], Awaitable[Any]]
)
# TODO: rework into a TypeAlias on py 3.10
Decorator = TypeVar("Decorator", bound=Callable[..., Any])


class RPCHandlerGroup:
    __handlers: Final[dict[str, tuple[RPCHandler, type[RPCRequest]]]]

    def __init__(self):
        self.__handlers = {}

    def register(
        self,
        *,
        method: str,
        clsname: type[RPCRequest],
    ) -> Decorator:
        def decorator(func: RPCHandler) -> Decorator:
            self.__handlers.update({f"{method}": (func, clsname)})
            return func

        return decorator

    def export_handlers(self) -> dict[str, tuple[RPCHandler, type[RPCRequest]]]:
        return self.__handlers
