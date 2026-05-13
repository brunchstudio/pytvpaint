"""JSON-RPC client and data models."""

from __future__ import annotations

import json
import select
import socket
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

    def __init__(self, url: str, timeout: int = 60, max_retries: int = 5, version: str = "2.0") -> None:
        """Initialize a new JSON-RPC client with a WebSocket url endpoint.

        Args:
            url: the WebSocket url endpoint
            timeout: the socket operation timeout
            max_retries: the maximum socket connection retries
            version: The JSON-RPC version. Defaults to "2.0".
        """
        self.ws_handle = WebSocket()
        self.url = url
        self.rpc_id = 0
        self.timeout = timeout
        self.max_retries = max_retries
        self.jsonrpc_version = version

    def __del__(self) -> None:
        """Called when the client goes out of scope."""
        self.disconnect()

    @property
    def is_connected(self) -> bool:
        """Returns True if the client is connected and the socket is active."""
        if not self.ws_handle.connected or self.ws_handle.sock is None:
            return False

        try:
            # check if the socket is readable.
            readable_sockets, _, _ = select.select([self.ws_handle.sock], [], [], 0.0)
            if readable_sockets:
                # MSG_PEEK reads data without consuming it from the buffer.
                # If recv returns 0 bytes on a readable socket, the peer has disconnected.
                data = self.ws_handle.sock.recv(1, socket.MSG_PEEK)
                if not data:
                    return False
        except (BlockingIOError, InterruptedError):
            pass  # Normal non-blocking behavior
        except Exception:
            return False  # Socket error indicates disconnection

        return True

    def connect(self, timeout: int = 0) -> None:
        """Connects to the WebSocket endpoint and configures TCP keepalive."""
        self.ws_handle.connect(self.url, timeout=timeout)

        if self.ws_handle.sock:
            sock = self.ws_handle.sock
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            # Apply OS-specific keepalive configurations if available
            if hasattr(socket, "TCP_KEEPIDLE"):
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, self.timeout)
            if hasattr(socket, "TCP_KEEPINTVL"):
                probe_interval = max(1, max(self.timeout, 1) // 6)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, probe_interval)
            if hasattr(socket, "TCP_KEEPCNT"):
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, self.max_retries)

    def disconnect(self) -> None:
        """Disconnects from the server."""
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
            raise ConnectionError(f"Can't send rpc message because the client is not connected to {self.url}")

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
