from __future__ import annotations

from typing import Any

import pytest
from pytest_mock import MockFixture
from pytvpaint.george.client import JSONRPCClient
from websocket import WebSocket


@pytest.fixture
def json_rpc_client(mocker: MockFixture) -> JSONRPCClient:
    def connect(w: WebSocket, url: str, **options: Any) -> None:
        w.connected = True

    mocker.patch.object(WebSocket, "connect", connect)
    return JSONRPCClient("ws://localhost:3000")


def test_rpc_connect(mocker: MockFixture, json_rpc_client: JSONRPCClient) -> None:
    json_rpc_client.connect()
    assert json_rpc_client.is_connected


def test_rpc_increment_id(json_rpc_client: JSONRPCClient) -> None:
    assert json_rpc_client.rpc_id == 0
    json_rpc_client.increment_rpc_id()
    assert json_rpc_client.rpc_id == 1


def test_rpc_increment_max_sys_int(json_rpc_client: JSONRPCClient) -> None:
    import sys

    json_rpc_client.rpc_id = sys.maxsize - 1
    json_rpc_client.increment_rpc_id()
    assert json_rpc_client.rpc_id == 0


def test_rpc_execute_remote(
    mocker: MockFixture, json_rpc_client: JSONRPCClient
) -> None:
    def send(*args: Any) -> int:
        return 0

    json_response_test = (
        '{"id": 0, "jsonrpc": "2.0", "result": "TVP Animation 11 Pro 11.5.3 fr"}'
    )

    def recv(w: WebSocket) -> str | bytes:
        return json_response_test

    mocker.patch.object(WebSocket, "recv", recv)
    mocker.patch.object(WebSocket, "send", send)

    json_rpc_client.connect()
    result = json_rpc_client.execute_remote("push", [True, "hello", 7])
    assert result == {
        "id": 0,
        "jsonrpc": "2.0",
        "result": "TVP Animation 11 Pro 11.5.3 fr",
    }
