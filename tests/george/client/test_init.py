from __future__ import annotations

from pathlib import Path
from typing import NoReturn

import pytest
from pytvpaint.george import GrgErrorValue
from pytvpaint.george.client import run_script, send_cmd, try_cmd
from pytvpaint.george import GeorgeError


def test_decorate_try_cmd() -> None:
    class TestError(GeorgeError):
        pass

    @try_cmd(raise_exc=TestError, exception_msg="Test exc")
    def test() -> NoReturn:
        raise TestError()

    with pytest.raises(GeorgeError, match="Test exc"):
        test()


def test_decorate_try_cmd_wrong_error() -> None:
    class TestError(GeorgeError):
        pass

    @try_cmd(raise_exc=TestError, exception_msg="Test exc")
    def test() -> NoReturn:
        raise Exception()

    with pytest.raises(Exception):
        test()


def test_run_grg_script(tmp_path: Path) -> None:
    tmp_script = tmp_path / "script.grg"
    tmp_img = tmp_path / "out.png"

    with tmp_script.open("w") as script:
        script.write(f'tv_SaveImage "{tmp_img}"')

    send_cmd("tv_savemode", "png")
    run_script(tmp_script)
    assert tmp_img.exists()


def test_send_cmd(tmp_path: Path) -> None:
    tmp_img = tmp_path / "out.png"
    send_cmd("tv_savemode", "png")
    send_cmd("tv_SaveImage", tmp_img)
    assert tmp_img.exists()


def test_send_cmd_error() -> None:
    # Without any arguments it should return an "ERROR XX"
    with pytest.raises(GeorgeError, match="ERROR -1"):
        send_cmd("tv_SaveImage")


def test_send_cmd_custom_error_value() -> None:
    with pytest.raises(GeorgeError, match="none"):
        send_cmd("tv_LayerGetID", -56, error_values=[GrgErrorValue.NONE])
