"""This modules handles the WebSocket client and automatically connect to the server running in TVPaint.

It also has crucial functions like `send_cmd` that send George commands and get the result.
"""

from __future__ import annotations

import contextlib
import functools
import os
import re
from pathlib import Path
from time import sleep, time
from typing import Any, Callable, TypeVar, cast

from pytvpaint import log
from pytvpaint.george.client.parse import tv_handle_string
from pytvpaint.george.client.rpc import JSONRPCClient
from pytvpaint.george.exceptions import GeorgeError


def _connect_client(
    host: str = "ws://localhost", port: int = 3000, timeout: int = 60
) -> JSONRPCClient:
    host = os.getenv("PYTVPAINT_WS_HOST", host)
    port = int(os.getenv("PYTVPAINT_WS_PORT", port))
    startup_connect = bool(int(os.getenv("PYTVPAINT_WS_STARTUP_CONNECT", 1)))
    timeout = int(os.getenv("PYTVPAINT_WS_TIMEOUT", timeout))

    rpc_client = JSONRPCClient(f"{host}:{port}", timeout)

    if not startup_connect:
        return rpc_client

    start_time = time()
    wait_duration = 5
    connection_successful = False

    while True:
        if timeout and (time() - start_time) > timeout:
            break
        with contextlib.suppress(ConnectionRefusedError):
            rpc_client.connect()
            connection_successful = True
            break

        log.warning(f"Connection refused, trying again in {wait_duration} seconds...")
        sleep(wait_duration)

    if not connection_successful:
        # Connection could not be established after timeout
        if rpc_client.is_connected:
            rpc_client.disconnect()

        raise ConnectionRefusedError(
            "Could not establish connection with a tvpaint instance before timeout !"
        )

    if connection_successful:
        log.info(f"Connected to TVPaint on port {port}")

    return rpc_client


rpc_client = _connect_client()

T = TypeVar("T", bound=Callable[..., Any])


def try_cmd(
    raise_exc: type[Exception] = GeorgeError,
    catch_exc: type[Exception] = GeorgeError,
    exception_msg: str | None = None,
) -> Callable[[T], T]:
    """Decorator that does a try/except with GeorgeError by default.

    It raises the error with the custom exception message provided.

    Args:
        raise_exc: the exception to raise. Defaults to GeorgeError.
        catch_exc: the exception to catch. Defaults to GeorgeError.
        exception_msg: Custom exception message. Defaults to None.

    Returns:
        the decorated function
    """

    def decorate(func: T) -> T:
        @functools.wraps(func)
        def applicator(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except catch_exc as e:
                raise raise_exc(exception_msg or e)

        return cast(T, applicator)

    return decorate


def send_cmd(
    command: str,
    *args: Any,
    error_values: list[Any] | None = None,
    handle_string: bool = True,
) -> str:
    """Send a George command with the provided arguments to TVPaint.

    Catch basic `ERROR XX` errors returned from George, but you can provide your own error values.

    Args:
        command: the George command to send
        *args: pass any arguments you want to that function
        error_values: a list of error values to catch from George. Defaults to None.
        handle_string: control the quote wrapping of string with spaces. Defaults to True.

    Raises:
        GeorgeError: if we received `ERROR XX` or any of the custom error codes

    Returns:
        the George return string
    """
    tv_args = [
        tv_handle_string(arg) if handle_string and isinstance(arg, str) else arg
        for arg in args
    ]
    cmd_str = " ".join([str(arg) for arg in [command, *tv_args]])

    is_undo_stack = command in [
        "tv_UndoOpenStack",
        "tv_UpdateUndo",
        "tv_UndoCloseStack",
    ]

    if not is_undo_stack:
        log.debug(f"[RPC] >> {cmd_str}")

    response = rpc_client.execute_remote("execute_george", [cmd_str])
    result = response["result"]

    if not is_undo_stack:
        log.debug(f"[RPC] << {result}")

    # Test for basic ERROR X values and user provided custom errors
    res_in_error_values = error_values and result in list(map(str, error_values))
    if res_in_error_values or re.match(r"ERROR -?\d+", result, re.IGNORECASE):
        msg = f"Received value: '{result}' considered as an error"
        raise GeorgeError(msg, error_value=result)

    return result


def run_script(script: Path | str) -> None:
    """Execute a George script from a .grg file.

    Args:
        script: the path to the script

    Raises:
        ValueError: if the script was not found
    """
    script = Path(script)
    if not script.exists():
        raise ValueError(f"Script not found at : {script.as_posix()}")
    send_cmd("tv_RunScript", script.as_posix())
