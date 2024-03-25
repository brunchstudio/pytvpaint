from __future__ import annotations

import pytest
from pytest_mock import MockFixture

from pytvpaint.george.client import send_cmd
from pytvpaint.george.exceptions import GeorgeError
from pytvpaint.george.grg_base import (
    AlphaMode,
    AlphaSaveMode,
    DrawingMode,
    FileMode,
    HSLColor,
    MarkAction,
    MarkReference,
    MenuElement,
    RectButton,
    RGBColor,
    SaveFormat,
    TVPShape,
    tv_alpha_load_mode_get,
    tv_alpha_load_mode_set,
    tv_alpha_save_mode_get,
    tv_alpha_save_mode_set,
    tv_get_active_shape,
    tv_line,
    tv_list_request,
    tv_mark_in_get,
    tv_mark_in_set,
    tv_mark_out_get,
    tv_mark_out_set,
    tv_menu_show,
    tv_pen_brush_get,
    tv_pen_brush_set,
    tv_rect,
    tv_rect_fill,
    tv_req_angle,
    tv_req_file,
    tv_req_float,
    tv_req_num,
    tv_req_string,
    tv_request,
    tv_save_mode_get,
    tv_save_mode_set,
    tv_set_a_pen_hsl,
    tv_set_a_pen_rgba,
    tv_set_active_shape,
    tv_text,
    tv_text_brush,
    tv_undo,
    tv_version,
)
from pytvpaint.george.grg_layer import tv_layer_info
from pytvpaint.george.grg_project import TVPProject


def test_tv_version() -> None:
    from packaging import version as version_utils

    name, version, lang = tv_version()
    min_version = version_utils.parse("1.0")

    assert "TVP Animation" in name
    assert version_utils.parse(version) >= min_version
    assert lang in ["en", "fr", "ja", "zh"]


@pytest.mark.skip("Will break the UI")
@pytest.mark.parametrize(
    "cmd",
    [
        MenuElement.CLIP,
        MenuElement.PROJECT,
        MenuElement.XSHEET,
        MenuElement.NOTES,
    ],
)
def test_tv_menu_show_simple(cmd: MenuElement) -> None:
    tv_menu_show(cmd)


@pytest.mark.skip("Will break the UI")
@pytest.mark.parametrize(
    "cmd",
    [
        MenuElement.SHOW_UI,
        MenuElement.HIDE_UI,
        MenuElement.CENTER_DISPLAY,
        MenuElement.FIT_DISPLAY,
        MenuElement.FRONT,
        MenuElement.BACK,
    ],
)
@pytest.mark.parametrize("current", [True, False])
def test_tv_menu_show_current(cmd: MenuElement, current: bool) -> None:
    tv_menu_show(cmd, current=current)


@pytest.mark.skip("Will break the UI")
@pytest.mark.parametrize("args", [(0, 0, 50, 50), (-10, -50, 20, 20)])
@pytest.mark.parametrize("current", [True, False])
def test_tv_menu_show_resize_ui(args: tuple[int], current: bool) -> None:
    tv_menu_show(MenuElement.RESIZE_UI, *args, current=current)


@pytest.mark.skip("Will break the UI")
@pytest.mark.parametrize("arg", [0, 1])
@pytest.mark.parametrize("current", [True, False])
def test_tv_menu_show_aspect_ratio(arg: int, current: bool) -> None:
    tv_menu_show(MenuElement.ASPECT_RATIO, arg, current=current)


@pytest.mark.skip(reason="Will block TVPaint")
def test_tv_request() -> None:
    tv_request("ksehfkjhkj", "ouiii", "NOOOOO")


@pytest.mark.skip(reason="Will block TVPaint")
def test_tv_req_num() -> None:
    tv_req_num(15, 0, 100, title="Request an int")


@pytest.mark.skip(reason="Will block TVPaint")
def test_tv_req_angle(mocker: MockFixture) -> None:
    tv_req_angle(15, 0, 100, title="Request an angle")


@pytest.mark.skip(reason="Will block TVPaint")
def test_tv_req_float(mocker: MockFixture) -> None:
    tv_req_float(15.0, 0.0, 100.0, title="Request a float")


@pytest.mark.skip(reason="Will block TVPaint")
def test_tv_req_string() -> None:
    tv_req_string("Request a string", "Hello this is text\nleo")


@pytest.mark.skip(reason="Needs user action")
def test_tv_list_request() -> None:
    tv_list_request(["a/b/c|d"])


@pytest.mark.skip(reason="Needs user action")
def test_tv_req_file() -> None:
    tv_req_file(FileMode.LOAD, "Open requester", "C:/Users", "out.py", ".py")


@pytest.mark.skip("Doesn't work?")
def test_undo_command(test_project: TVPProject) -> None:
    def create_layer() -> int:
        return int(send_cmd("tv_LayerCreate", "test_layer"))

    layer_id = create_layer()
    assert layer_id

    tv_undo()

    # The layer doesn't exist anymore
    with pytest.raises(GeorgeError):
        tv_layer_info(layer_id)


def test_save_mode_get() -> None:
    fmt, res = tv_save_mode_get()
    assert len(fmt.value) > 2
    assert res


def test_tv_save_mode_set() -> None:
    tv_save_mode_set(SaveFormat.BMP)


def test_tv_alpha_load_mode_get() -> None:
    tv_alpha_load_mode_get()


@pytest.mark.parametrize("mode", AlphaMode)
def test_tv_alpha_load_mode_set(test_project: TVPProject, mode: AlphaMode) -> None:
    tv_alpha_load_mode_set(mode)
    assert tv_alpha_load_mode_get() == mode


def test_tv_alpha_save_mode_get() -> None:
    tv_alpha_save_mode_get()


@pytest.mark.skip("It does not work for no reason...")
@pytest.mark.parametrize("mode", list(AlphaSaveMode))
def test_tv_alpha_save_mode_set(test_project: TVPProject, mode: AlphaSaveMode) -> None:
    tv_alpha_save_mode_set(mode)
    assert tv_alpha_save_mode_get() == mode


@pytest.mark.parametrize("ref", MarkReference)
def test_tv_mark_in_get(ref: MarkReference) -> None:
    tv_mark_in_get(ref)


@pytest.mark.parametrize("ref", MarkReference)
def test_tv_mark_in_set(test_project: TVPProject, ref: MarkReference) -> None:
    tv_mark_in_set(ref, 20, MarkAction.SET)
    assert tv_mark_in_get(ref) == (20, MarkAction.SET)


@pytest.mark.parametrize("ref", MarkReference)
def test_tv_mark_in_set_clear(test_project: TVPProject, ref: MarkReference) -> None:
    tv_mark_in_set(ref, 20, MarkAction.SET)
    assert tv_mark_in_get(ref) == (20, MarkAction.SET)
    tv_mark_in_set(ref, 20, MarkAction.CLEAR)
    assert tv_mark_in_get(ref) == (20, MarkAction.CLEAR)


@pytest.mark.parametrize("ref", MarkReference)
def test_tv_mark_out_get(ref: MarkReference) -> None:
    tv_mark_out_get(ref)


@pytest.mark.parametrize("ref", MarkReference)
def test_tv_mark_out_set(test_project: TVPProject, ref: MarkReference) -> None:
    tv_mark_out_set(ref, 20, MarkAction.SET)
    assert tv_mark_out_get(ref) == (20, MarkAction.SET)


@pytest.mark.parametrize("ref", MarkReference)
def test_tv_mark_out_set_clear(test_project: TVPProject, ref: MarkReference) -> None:
    tv_mark_out_set(ref, 20, MarkAction.SET)
    assert tv_mark_out_get(ref) == (20, MarkAction.SET)
    tv_mark_out_set(ref, 20, MarkAction.CLEAR)
    assert tv_mark_out_get(ref) == (20, MarkAction.CLEAR)


def test_tv_get_active_shape() -> None:
    assert tv_get_active_shape() in TVPShape


@pytest.mark.parametrize("shape", TVPShape)
def test_tv_set_active_shape(shape: TVPShape) -> None:
    tv_set_active_shape(shape)


def test_tv_set_a_pen_rgba() -> None:
    c = RGBColor(0, 255, 0)
    tv_set_a_pen_rgba(c, alpha=40)
    assert tv_set_a_pen_rgba(c, alpha=40) == c


def test_tv_set_a_pen_hsl() -> None:
    c = HSLColor(50, 51, 100)
    tv_set_a_pen_hsl(c)
    result = tv_set_a_pen_hsl(c)
    assert c.h - 1 <= result.h <= c.h + 1
    assert c.s - 1 <= result.s <= c.s + 1
    assert c.l - 1 <= result.l <= c.l + 1


@pytest.mark.parametrize("tool_mode", [True, False])
def test_tv_pen_brush_get(tool_mode: bool) -> None:
    assert tv_pen_brush_get(tool_mode)


@pytest.mark.parametrize("mode", DrawingMode)
@pytest.mark.parametrize("tool_mode", [True, False])
def test_tv_pen_brush_set(
    pen_brush_reset: None, mode: DrawingMode, tool_mode: bool
) -> None:
    tv_pen_brush_set(mode, tool_mode=tool_mode)


@pytest.mark.parametrize("button", [None, *RectButton])
def test_tv_rect(test_project: TVPProject, button: RectButton | None) -> None:
    width = test_project.width
    height = test_project.height
    tv_rect(0, 0, width, height)


@pytest.mark.parametrize("erase_mode", [True, False])
@pytest.mark.parametrize("tool_mode", [True, False])
def test_tv_rect_fill(
    test_project: TVPProject, erase_mode: bool, tool_mode: bool
) -> None:
    width = test_project.width
    height = test_project.height
    tv_rect_fill(0, 0, width, height, 0, width, erase_mode, tool_mode)


@pytest.mark.parametrize("xy1, xy2", [[(0, 0), (0, 0)], [(0, 0), (100, 100)]])
@pytest.mark.parametrize("right_click", [True, False])
@pytest.mark.parametrize("dry", [True, False])
def test_tv_line(
    test_project: TVPProject,
    xy1: tuple[int, int],
    xy2: tuple[int, int],
    right_click: bool,
    dry: bool,
) -> None:
    tv_line(xy1, xy2, right_click, dry)


@pytest.mark.parametrize("text", ["", "Hello", "sp a c e s", "$$"])
@pytest.mark.parametrize("x, y", [(0, 0), (-5, 0), (100, 100)])
@pytest.mark.parametrize("use_b_pen", [True, False])
def test_tv_text(
    test_project: TVPProject,
    text: str,
    x: int,
    y: int,
    use_b_pen: bool,
) -> None:
    tv_text(text, x, y, use_b_pen)


@pytest.mark.parametrize("text", ["", "Hello", "sp a c e s", "$$"])
def test_tv_text_brush(text: str) -> None:
    tv_text_brush(text)
