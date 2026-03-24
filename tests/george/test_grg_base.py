from __future__ import annotations

import pytest
from packaging import version
from pytest_mock import MockFixture

from pytvpaint import george
from pytvpaint.george.client import send_cmd


def test_tv_version() -> None:
    name, tvp_version, lang = george.tv_version()
    min_version = version.parse("11.0")
    current_version = version.parse(tvp_version)

    assert "TVP Animation" in name or "TVPaint Animation" in name
    assert current_version >= min_version
    assert lang in ["en", "fr", "ja", "zh"]


@pytest.mark.skip("Will break the UI")
@pytest.mark.parametrize(
    "cmd",
    [
        george.MenuElement.CLIP,
        george.MenuElement.PROJECT,
        george.MenuElement.XSHEET,
        george.MenuElement.NOTES,
    ],
)
def test_tv_menu_show_simple(cmd: george.MenuElement) -> None:
    george.tv_menu_show(cmd)


@pytest.mark.skip("Will break the UI")
@pytest.mark.parametrize(
    "cmd",
    [
        george.MenuElement.SHOW_UI,
        george.MenuElement.HIDE_UI,
        george.MenuElement.CENTER_DISPLAY,
        george.MenuElement.FIT_DISPLAY,
        george.MenuElement.FRONT,
        george.MenuElement.BACK,
    ],
)
@pytest.mark.parametrize("current", [True, False])
def test_tv_menu_show_current(cmd: george.MenuElement, current: bool) -> None:
    george.tv_menu_show(cmd, current=current)


@pytest.mark.skip("Will break the UI")
@pytest.mark.parametrize("args", [(0, 0, 50, 50), (-10, -50, 20, 20)])
@pytest.mark.parametrize("current", [True, False])
def test_tv_menu_show_resize_ui(args: tuple[int], current: bool) -> None:
    george.tv_menu_show(george.MenuElement.RESIZE_UI, *args, current=current)


@pytest.mark.skip("Will break the UI")
@pytest.mark.parametrize("arg", [0, 1])
@pytest.mark.parametrize("current", [True, False])
def test_tv_menu_show_aspect_ratio(arg: int, current: bool) -> None:
    george.tv_menu_show(george.MenuElement.ASPECT_RATIO, arg, current=current)


@pytest.mark.skip(reason="Will block TVPaint")
def test_tv_request() -> None:
    george.tv_request("ksehfkjhkj", "ouiii", "NOOOOO")


@pytest.mark.skip(reason="Will block TVPaint")
def test_tv_req_num() -> None:
    george.tv_req_num(15, 0, 100, title="Request an int")


@pytest.mark.skip(reason="Will block TVPaint")
def test_tv_req_angle(mocker: MockFixture) -> None:
    george.tv_req_angle(15, 0, 100, title="Request an angle")


@pytest.mark.skip(reason="Will block TVPaint")
def test_tv_req_float(mocker: MockFixture) -> None:
    george.tv_req_float(15.0, 0.0, 100.0, title="Request a float")


@pytest.mark.skip(reason="Will block TVPaint")
def test_tv_req_string() -> None:
    george.tv_req_string("Request a string", "Hello this is text\nleo")


@pytest.mark.skip(reason="Needs user action")
def test_tv_list_request() -> None:
    george.tv_list_request(["a/b/c|d"])


@pytest.mark.skip(reason="Needs user action")
def test_tv_req_file() -> None:
    george.tv_req_file(george.FileMode.LOAD, "Open requester", "C:/Users", "out.py", ".py")


@pytest.mark.skip("Doesn't work?")
def test_undo_command(test_project: george.TVPProject) -> None:
    def create_layer() -> int:
        return int(send_cmd("tv_LayerCreate", "test_layer"))

    layer_id = create_layer()
    assert layer_id

    george.tv_undo()

    # The layer doesn't exist anymore
    with pytest.raises(george.GeorgeError):
        george.tv_layer_info(layer_id)


def test_save_mode_get() -> None:
    fmt, res = george.tv_save_mode_get()
    assert len(fmt.value) > 2
    assert res


def test_tv_save_mode_set() -> None:
    george.tv_save_mode_set(george.SaveFormat.BMP)


def test_tv_alpha_load_mode_get() -> None:
    george.tv_alpha_load_mode_get()


@pytest.mark.parametrize("mode", george.AlphaMode)
def test_tv_alpha_load_mode_set(test_project: george.TVPProject, mode: george.AlphaMode) -> None:
    george.tv_alpha_load_mode_set(mode)
    assert george.tv_alpha_load_mode_get() == mode


def test_tv_alpha_save_mode_get() -> None:
    george.tv_alpha_save_mode_get()


@pytest.mark.skip("It does not work for no reason...")
@pytest.mark.parametrize("mode", list(george.AlphaSaveMode))
def test_tv_alpha_save_mode_set(test_project: george.TVPProject, mode: george.AlphaSaveMode) -> None:
    george.tv_alpha_save_mode_set(mode)
    assert george.tv_alpha_save_mode_get() == mode


@pytest.mark.parametrize("ref", george.MarkReference)
def test_tv_mark_in_get(ref: george.MarkReference) -> None:
    george.tv_mark_in_get(ref)


@pytest.mark.parametrize("ref", george.MarkReference)
def test_tv_mark_in_set(test_project: george.TVPProject, ref: george.MarkReference) -> None:
    george.tv_mark_in_set(ref, 20, george.MarkAction.SET)
    assert george.tv_mark_in_get(ref) == (20, george.MarkAction.SET)


@pytest.mark.parametrize("ref", george.MarkReference)
def test_tv_mark_in_set_clear(test_project: george.TVPProject, ref: george.MarkReference) -> None:
    george.tv_mark_in_set(ref, 20, george.MarkAction.SET)
    assert george.tv_mark_in_get(ref) == (20, george.MarkAction.SET)
    george.tv_mark_in_set(ref, 20, george.MarkAction.CLEAR)
    assert george.tv_mark_in_get(ref) == (20, george.MarkAction.CLEAR)


@pytest.mark.parametrize("ref", george.MarkReference)
def test_tv_mark_out_get(ref: george.MarkReference) -> None:
    george.tv_mark_out_get(ref)


@pytest.mark.parametrize("ref", george.MarkReference)
def test_tv_mark_out_set(test_project: george.TVPProject, ref: george.MarkReference) -> None:
    george.tv_mark_out_set(ref, 20, george.MarkAction.SET)
    assert george.tv_mark_out_get(ref) == (20, george.MarkAction.SET)


@pytest.mark.parametrize("ref", george.MarkReference)
def test_tv_mark_out_set_clear(test_project: george.TVPProject, ref: george.MarkReference) -> None:
    george.tv_mark_out_set(ref, 20, george.MarkAction.SET)
    assert george.tv_mark_out_get(ref) == (20, george.MarkAction.SET)
    george.tv_mark_out_set(ref, 20, george.MarkAction.CLEAR)
    assert george.tv_mark_out_get(ref) == (20, george.MarkAction.CLEAR)


def test_tv_get_active_shape() -> None:
    assert george.tv_get_active_shape() in george.TVPShape


@pytest.mark.parametrize("shape", george.TVPShape)
def test_tv_set_active_shape(shape: george.TVPShape) -> None:
    george.tv_set_active_shape(shape)


def test_tv_set_a_pen_rgba() -> None:
    c = george.RGBColor(0, 255, 0)
    george.tv_set_a_pen_rgba(c, alpha=40)
    assert george.tv_set_a_pen_rgba(c, alpha=40) == c


def test_tv_set_a_pen_hsl() -> None:
    c = george.HSLColor(50, 51, 100)
    george.tv_set_a_pen_hsl(c)
    result = george.tv_set_a_pen_hsl(c)
    assert c.h - 1 <= result.h <= c.h + 1
    assert c.s - 1 <= result.s <= c.s + 1
    assert c.l - 1 <= result.l <= c.l + 1


@pytest.mark.parametrize("tool_mode", [True, False])
def test_tv_pen_brush_get(tool_mode: bool) -> None:
    assert george.tv_pen_brush_get(tool_mode)


@pytest.mark.parametrize("mode", george.DrawingMode)
@pytest.mark.parametrize("tool_mode", [True, False])
def test_tv_pen_brush_set(pen_brush_reset: None, mode: george.DrawingMode, tool_mode: bool) -> None:
    george.tv_pen_brush_set(mode, tool_mode=tool_mode)


@pytest.mark.parametrize("button", [None, *george.RectButton])
def test_tv_rect(test_project: george.TVPProject, button: george.RectButton | None) -> None:
    width = test_project.width
    height = test_project.height
    george.tv_rect(0, 0, width, height)


@pytest.mark.parametrize("erase_mode", [True, False])
@pytest.mark.parametrize("tool_mode", [True, False])
def test_tv_rect_fill(test_project: george.TVPProject, erase_mode: bool, tool_mode: bool) -> None:
    width = test_project.width
    height = test_project.height
    george.tv_rect_fill(0, 0, width, height, 0, width, erase_mode, tool_mode)


@pytest.mark.parametrize("xy1, xy2", [[(0, 0), (0, 0)], [(0, 0), (100, 100)]])
@pytest.mark.parametrize("right_click", [True, False])
@pytest.mark.parametrize("dry", [True, False])
def test_tv_line(
    test_project: george.TVPProject,
    xy1: tuple[int, int],
    xy2: tuple[int, int],
    right_click: bool,
    dry: bool,
) -> None:
    george.tv_line(xy1, xy2, right_click, dry)


@pytest.mark.parametrize("text", ["", "Hello", "sp a c e s", "$$"])
@pytest.mark.parametrize("x, y", [(0, 0), (-5, 0), (100, 100)])
@pytest.mark.parametrize("use_b_pen", [True, False])
def test_tv_text(
    test_project: george.TVPProject,
    text: str,
    x: int,
    y: int,
    use_b_pen: bool,
) -> None:
    george.tv_text(text, x, y, use_b_pen)


@pytest.mark.parametrize("text", ["", "Hello", "sp a c e s", "$$"])
def test_tv_text_brush(text: str) -> None:
    george.tv_text_brush(text)
