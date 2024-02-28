from __future__ import annotations

import json
import sys
from typing import Any, Union, cast

from typing_extensions import NotRequired, TypedDict
from websocket import WebSocket

JSONValueType = Union[str, int, float, bool, None]


class JSONRPCError(TypedDict):
    code: int
    message: str
    data: NotRequired[Any]


class JSONRPCPayload(TypedDict):
    jsonrpc: str
    id: int
    method: str
    params: list[JSONValueType]


class JSONRPCResponse(TypedDict):
    jsonrpc: str
    id: int
    result: str
    error: NotRequired[JSONRPCError]


class RPCNotConnectedError(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(f"RPC client not connected: {msg}")


class JSONRPCResponseError(Exception):
    def __init__(self, error: JSONRPCError) -> None:
        super().__init__(f"JSON-RPC Server error ({error['code']}): {error['message']}")


class JSONRPCClient:
    """
    Simple JSON-RPC 2.0 client over websockets
    See: https://www.jsonrpc.org/specification#notification
    """

    def __init__(self, url: str, version: str = "2.0") -> None:
        self.ws_handle = WebSocket()
        self.ws_handle.settimeout(5)
        self.url = url
        self.rpc_id = 0
        self.jsonrpc_version = version

    @property
    def is_connected(self) -> bool:
        return self.ws_handle.connected

    def connect(self, timeout: float | None = None) -> None:
        self.ws_handle.connect(self.url, timeout=timeout)

    def disconnect(self) -> None:
        if not self.is_connected:
            raise RPCNotConnectedError("Can't disconnect")
        self.ws_handle.close()

    def increment_rpc_id(self) -> None:
        self.rpc_id = (self.rpc_id + 1) % sys.maxsize

    def execute_remote(
        self, method: str, params: list[JSONValueType] | None = None
    ) -> JSONRPCResponse:
        if not self.is_connected:
            raise RPCNotConnectedError("Can't send rpc message")

        payload: JSONRPCPayload = {
            "jsonrpc": self.jsonrpc_version,
            "id": self.rpc_id,
            "method": method,
            "params": params or [],
        }

        self.ws_handle.send(json.dumps(payload))
        self.increment_rpc_id()

        result = self.ws_handle.recv()
        response = cast(JSONRPCResponse, json.loads(result))

        if "error" in response:
            raise JSONRPCResponseError(response["error"])

        return response
