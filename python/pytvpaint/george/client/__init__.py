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
    timeout = int(os.getenv("PYTVPAINT_WS_CONNECT_TIMEOUT", timeout))

    rpc_client = JSONRPCClient(f"{host}:{port}")

    start_time = time()
    failed_attempts = 0
    wait_duration = 1

    while failed_attempts < 3:
        with contextlib.suppress(ConnectionRefusedError):
            rpc_client.connect()
            break

        # Connection could not be established after timeout
        if time() > start_time + timeout:
            raise ConnectionRefusedError(
                "Could not establish connection with a tvpaint instance !"
            )

        log.warning(f"Connection refused, trying again in {wait_duration} seconds...")

        # Use exponential backoff duration to reconnect
        sleep(wait_duration)

        wait_duration *= 2
        failed_attempts += 1

    log.info("Connected to TVPaint")
    return rpc_client


rpc_client = _connect_client()

T = TypeVar("T", bound=Callable[..., Any])


def try_cmd(
    raise_exc: type[Exception] = GeorgeError,
    catch_exc: type[Exception] = GeorgeError,
    exception_msg: str = "",
) -> Callable[[T], T]:
    """
    Decorator that does a try/except with GeorgeError by default
    It raises the error with the custom exception message provided
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
    """
    Send a George command with the provided arguments to TVPaint.
    Catch basic "ERROR XX" errors, but you can provide your own error values.
    Use handle_string to control the quote wrapping of string with spaces
    """
    tv_args = [
        tv_handle_string(arg) if handle_string and isinstance(arg, str) else arg
        for arg in args
    ]
    cmd_str = " ".join([str(arg) for arg in [command, *tv_args]])

    is_stack = command in ["tv_UndoOpenStack", "tv_UpdateUndo", "tv_UndoCloseStack"]

    if not is_stack:
        log.debug(f"[RPC] >> {cmd_str}")

    response = rpc_client.execute_remote("execute_george", [cmd_str])
    result = response["result"]

    if not is_stack:
        log.debug(f"[RPC] << {result}")

    # Test for basic ERROR X values and user provided custom errors
    res_in_error_values = error_values and result in list(map(str, error_values))
    if res_in_error_values or re.match(r"ERROR -?\d+", result, re.IGNORECASE):
        msg = f"Received value: '{result}' considered as an error"
        raise GeorgeError(msg, error_value=result)

    return result


def run_script(script: Path | str) -> str:
    """
    Execute a George script from a .grg file
    """
    script = Path(script)
    if not script.exists():
        raise ValueError(f"Script not found at : {script.as_posix()}")
    return send_cmd("tv_RunScript", script.as_posix())
