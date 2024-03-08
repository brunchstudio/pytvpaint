"""JSON-RPC client and data models."""

from __future__ import annotations

import json
import sys
from typing import Any, Union, cast

from typing_extensions import NotRequired, TypedDict
from websocket import WebSocket

JSONValueType = Union[str, int, float, bool, None]


class JSONRPCPayload(TypedDict):
    """A rpc call is represented by sending a Request object to a Server.

    See: https://www.jsonrpc.org/specification#request_object
    """

    jsonrpc: str
    id: int
    method: str
    params: list[JSONValueType]


class JSONRPCResponse(TypedDict):
    """When a rpc call is made, the Server MUST reply with a Response.

    See: https://www.jsonrpc.org/specification#response_object
    """

    jsonrpc: str
    id: int
    result: str
    error: NotRequired[JSONRPCError]


class JSONRPCError(TypedDict):
    """When a rpc call encounters an error.

    See: https://www.jsonrpc.org/specification#error_object
    """

    code: int
    message: str
    data: NotRequired[Any]


class JSONRPCResponseError(Exception):
    """Exception used when a rpc call encounters an error."""

    def __init__(self, error: JSONRPCError) -> None:
        super().__init__(f"JSON-RPC Server error ({error['code']}): {error['message']}")


class JSONRPCClient:
    """Simple JSON-RPC 2.0 client over websockets.

    See: https://www.jsonrpc.org/specification#notification
    """

    def __init__(self, url: str, version: str = "2.0") -> None:
        """Initialize a new JSON-RPC client with a WebSocket url endpoint.

        Args:
            url (str): the WebSocket url endpoint
            version (str, optional): The JSON-RPC version. Defaults to "2.0".
        """
        self.ws_handle = WebSocket()
        self.ws_handle.settimeout(5)
        self.url = url
        self.rpc_id = 0
        self.jsonrpc_version = version

    @property
    def is_connected(self) -> bool:
        """Returns True if the client is connected."""
        return self.ws_handle.connected

    def connect(self, timeout: float | None = None) -> None:
        """Connects to the WebSocket endpoint."""
        self.ws_handle.connect(self.url, timeout=timeout)

    def disconnect(self) -> None:
        """Disconnects from the server."""
        if not self.is_connected:
            raise ConnectionError("Can't disconnect")
        self.ws_handle.close()

    def increment_rpc_id(self) -> None:
        """Increments the internal RPC id until it reaches `sys.maxsize`."""
        self.rpc_id = (self.rpc_id + 1) % sys.maxsize

    def execute_remote(
        self,
        method: str,
        params: list[JSONValueType] | None = None,
    ) -> JSONRPCResponse:
        """Executes a remote procedure call.

        Args:
            method: the name of the method to be invoked
            params: the parameter values to be used during the invocation of the method. Defaults to None.

        Raises:
            ConnectionError: if the client is not connected
            JSONRPCResponseError: if there was an error server-side

        Returns:
            JSONRPCResponse: the JSON-RPC response payload
        """
        if not self.is_connected:
            raise ConnectionError("Can't send rpc message")

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
