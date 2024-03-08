"""All George values as enum and functions which are not specific to any TVPaint element."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Generator, Type, TypeVar, cast, overload

from typing_extensions import Literal, TypeAlias

from pytvpaint.george.client import send_cmd
from pytvpaint.george.client.parse import (
    FieldTypes,
    args_dict_to_list,
    tv_cast_to_type,
    tv_parse_dict,
    tv_parse_list,
)


class GrgErrorValue:
    """Common George error values."""

    EMPTY = ""
    NONE = "none"
    ERROR = "error"


class GrgBoolState(Enum):
    """George booleans."""

    ON = "on"
    OFF = "off"


class FieldOrder(Enum):
    """Field order of the camera."""

    NONE = "none"
    LOWER = "lower"
    UPPER = "upper"


class MarkType(Enum):
    """The mark command."""

    MARKIN = "tv_markin"
    MARKOUT = "tv_markout"


class MarkReference(Enum):
    """The object on which the mark is applied."""

    PROJECT = "project"
    CLIP = "clip"


class MarkAction(Enum):
    """The mark action."""

    SET = "set"
    CLEAR = "clear"


class RectButton(Enum):
    """The rect button when drawing."""

    LEFT = 0
    RIGHT = 1


class TVPShape(Enum):
    """The shape tools."""

    B_SPLINE = "bspline"
    BEZIER = "bezier"
    BEZIER_FILL = "bezierfill"
    CAMERA = "camera"
    CIRCLE = "circle"
    CIRCLE_2PTS = "circle2pts"
    CIRCLE_3PTS = "circle3pts"
    CIRCLE_FILL = "circlefill"
    CIRCLE_2PTS_FILL = "circle2ptsfill"
    CIRCLE_3PTS_FILL = "circle3ptsfill"
    CROP = "crop"
    CUT_RECT = "cutrect"
    CUT_POLY = "cutpoly"
    CUT_FREE_HAND = "cutfreehand"
    CUT_FLOOD = "cutflood"
    DOT = "dot"
    FLOOD = "flood"
    FREE_HAND_LINE = "freehandline"
    FREE_HAND_FILL = "freehandfill"
    ELLIPSE = "ellipse"
    ELLIPSE_FILL = "ellipsefill"
    ELLIPSE_2PTS = "ellipse2pts"
    ELLIPSE_2PTS_FILL = "ellipse2ptsfill"
    LINE = "line"
    LINE_FILL = "linefill"
    PLANNING = "panning"
    POSITION = "position"
    RECTANGLE = "rectangle"
    RECTANGLE_FILL = "rectanglefill"
    SELECT_RECTANGLE = "selectrectangle"
    SELECT_ELLIPSE = "selectellipse"
    SELECT_2PTS = "select2pts"
    SELECT_3PTS = "select3pts"
    SELECT_POLY = "selectpoly"
    SELECT_FREE_HAND = "selectfreehand"
    SELECT_FLOOD = "selectflood"
    SELECT_COLOR = "selectcolor"
    SELECT_BEZIER = "selectbezier"
    SELECT_B_SPLINE = "selectbspline"
    SINGLE_DOT = "singledot"
    SPLIT_3PTS = "spline3pts"
    SPLINE_FILL = "splinefill"
    WARP = "warp"
    WRAP = "wrap"
    ZOOM_IN = "zoomin"
    ZOOM_OUT = "zoomout"
    ZOOM_HAND = "zoomhand"
    ZOOM_RECT = "zoomrect"


class ResizeOption(Enum):
    """Resize options for project."""

    EMPTY = 0
    CROP = 1
    STRETCH = 2


class SpriteLayout(Enum):
    """Sprite layout when exporting as sprites."""

    RECTANGLE = "rectangle"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    DIAGONAL = "diagonal"
    ANTI_DIAGONAL = "antidiagonal"


class AlphaMode(Enum):
    """The alpha load mode."""

    PREMULTIPLY = "premultiply"
    NO_PREMULTIPLY = "nopremultiply"
    NO_ALPHA = "noalpha"
    ALPHA_ONLY = "alphaonly"
    GUESS = "guess"


class AlphaSaveMode(Enum):
    """The alpha save mode."""

    PREMULTIPLY = "premultiply"
    NO_PREMULTIPLY = "nopremultiply"
    NO_ALPHA = "noalpha"
    ALPHA_ONLY = "alphaonly"
    GUESS = "guess"
    ALPHA_BINARY = "alphabinary"


class SaveFormat(Enum):
    """All save formats."""

    AVI = "avi"
    BMP = "bmp"
    CINEON = "cin"
    DEEP = "deep"
    DPX = "dpx"
    FLI = "flc"
    GIF = "gif"
    ILBM = "ilbm"
    JPG = "jpeg"
    MKV = "Mode=1017"
    MOV = "Mode=1015"
    MP4 = "Mode=1016"
    PCX = "pcx"
    PDF = "pdf"
    PNG = "png"
    PSD = "psd"
    SGI = "Mode=16"
    SOFTIMAGE = "Mode=10"
    SUNRASTER = "sun"
    TGA = "tga"
    TIFF = "Mode=15"
    VPB = "vpb"
    WEBM = "Mode=1018"

    @classmethod
    def from_extension(cls, extension: str) -> SaveFormat:
        """Returns the enum value from a string extension."""
        extension = extension.replace(".", "").lower()
        if not hasattr(SaveFormat, extension.upper()):
            raise ValueError(
                f"Could not find format ({extension}) in accepted formats ({SaveFormat})"
            )
        return cast(SaveFormat, getattr(cls, extension.upper()))


@dataclass(frozen=True)
class RGBColor:
    """RGB color with 0-255 range values."""

    r: int
    g: int
    b: int


@dataclass(frozen=True)
class HSLColor:
    """HSL color. Maximum values are (360, 100, 100) for h, s, l."""

    h: int
    s: int
    l: int  # noqa: E741


class BlendingMode(Enum):
    """All the blending modes."""

    COLOR = "color"
    BEHIND = "behind"
    ERASE = "erase"
    SHADE = "shade"
    LIGHT = "light"
    COLORIZE = "colorize"
    HUE = "hue"
    SATURATION = "saturation"
    VALUE = "value"
    ADD = "add"
    SUB = "sub"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    REPLACE = "replace"
    COPY = "copy"
    DIFFERENCE = "difference"
    DIVIDE = "divide"
    OVERLAY = "overlay"
    OVERLAY2 = "overlay2"
    LIGHT2 = "light2"
    SHADE2 = "shade2"
    HARDLIGHT = "hardlight"
    SOFTLIGHT = "softlight"
    GRAIN_EXTRACT = "grainextract"
    GRAIN_MERGE = "grainmerge"
    SUB2 = "sub2"
    DARKEN = "darken"
    LIGHTEN = "lighten"


class DrawingMode(Enum):
    """All the drawing modes."""

    COLOR = "color"
    BEHIND = "behind"
    ERASE = "erase"
    PANTO = "panto"
    MERGE = "merge"
    SHADE = "shade"
    LIGHT = "light"
    COLORIZE = "colorize"
    TINT = "tint"
    GRAIN = "grain"
    BLUR = "blur"
    NOISE = "noise"
    NEGATIVE = "negative"
    SHARP = "sharp"
    EMBOSS = "emboss"
    SOLARIZE = "solarize"
    SATURATE = "saturate"
    UNSATURATE = "unsaturate"
    ADD = "add"
    SUB = "sub"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    DIFF = "diff"
    HEALING = "healing"
    BURN = "burn"
    DODGE = "dodge"
    DARKEN = "darken"
    LIGHTEN = "lighten"


class MenuElement(Enum):
    """All the TVPaint menu elements."""

    SHOW_UI = "showui"
    HIDE_UI = "hideui"
    RESIZE_UI = "resizeui"
    CENTER_DISPLAY = "centerdisplay"
    FIT_DISPLAY = "fitdisplay"
    FRONT = "front"
    BACK = "back"
    ASPECT_RATIO = "aspectratio"
    CLIP = "clip"
    PROJECT = "project"
    XSHEET = "xsheet"
    NOTES = "notes"


class FileMode(Enum):
    """File mode save or load."""

    SAVE = "<"
    LOAD = ">"


@dataclass(frozen=True)
class TVPPenBrush:
    """A TVPaint brush."""

    mode: DrawingMode
    size: float
    power: int
    opacity: int
    dry: bool
    aaliasing: bool
    gradient: bool
    csize: str
    cpower: str


@dataclass(frozen=True)
class TVPSound:
    """A TVPaint sound (clip and project)."""

    offset: float
    volume: float
    mute: bool
    fade_in_start: float
    fade_in_stop: float
    fade_out_start: float
    fade_out_stop: float
    path: Path
    sound_in: float
    sound_out: float
    color_index: int


T = TypeVar("T", bound=Callable[..., Any])


def undoable(func: T) -> T:
    """Decorator to register actions in the TVPaint undo stack."""

    def wrapper(*args: Any, **kwargs: Any) -> T:
        tv_undo_open_stack()
        res = func(*args, **kwargs)
        tv_undo_close_stack(func.__name__)
        return cast(T, res)

    return cast(T, wrapper)


@contextlib.contextmanager
def undoable_stack() -> Generator[None, None, None]:
    """Context manager that creates an undo stack. Useful to undo a sequence of George actions."""
    tv_undo_open_stack()
    yield
    tv_undo_close_stack()


def tv_warn(msg: str) -> None:
    """Display a warning message."""
    send_cmd("tv_Warn", msg)


def tv_version() -> tuple[str, str, str]:
    """Returns the software name, version and language."""
    cmd_fields = [
        ("software_name", str),
        ("version", str),
        ("language", str),
    ]
    res = tv_parse_list(send_cmd("tv_Version"), with_fields=cmd_fields)
    software_name, version, language = res.values()
    return software_name, version, language


def tv_host2back() -> None:
    """Minimize the TVPaint window."""
    send_cmd("tv_Host2Back")


def tv_host2front() -> None:
    """Restore the TVPaint window after being minimized."""
    send_cmd("tv_Host2Front")


def tv_menu_hide() -> None:
    """Switch to inlay view and hide all non-docking panels."""
    send_cmd("tv_MenuHide")


def tv_menu_show(
    menu_element: MenuElement | None = None, *args: Any, current: bool = False
) -> None:
    """For the complete documentation, see: https://www.tvpaint.com/doc/tvpaint-animation-11/george-commands#tv_menushow."""
    cmd_args: list[str] = []

    if current:
        cmd_args.append("current")

    if menu_element:
        cmd_args.append(menu_element.value)

    send_cmd("tv_MenuShow", *cmd_args, *args)


def tv_request(msg: str, confirm_text: str = "Yes", cancel_text: str = "No") -> bool:
    """Open a custom requester.

    Args:
        msg: the message to display
        confirm_text: the confirm button text. Defaults to "Yes".
        cancel_text: the cancel button text. Defaults to "No".

    Returns:
        bool: True if clicked on "Yes"
    """
    return bool(int(send_cmd("tv_Request", msg, confirm_text, cancel_text)))


def tv_req_num(
    value: int, min: int, max: int, title: str = "Enter Value"
) -> int | None:
    """Open an integer requester.

    Args:
        value: the initial value
        min: the minimum value
        max: the maximum value
        title: title of the requester. Defaults to "Enter Value".

    Returns:
        the value or None if cancelled
    """
    res = send_cmd("tv_ReqNum", value, min, max, title, handle_string=False)
    return None if res.lower() == "cancel" else int(res)


def tv_req_angle(
    value: float, min: float, max: float, title: str = "Enter Value"
) -> float | None:
    """Open an angle (in degree) requester.

    Args:
        value: the initial value
        min: the minimum value
        max: the maximum value
        title: title of the requester. Defaults to "Enter Value".

    Returns:
        the value or None if cancelled
    """
    res = send_cmd("tv_ReqAngle", value, min, max, title, handle_string=False)
    return None if res.lower() == "cancel" else float(res)


def tv_req_float(
    value: float, min: float, max: float, title: str = "Enter value"
) -> float | None:
    """Open a decimal requester.

    Args:
        value: the initial value
        min: the minimum value
        max: the maximum value
        title: title of the requester. Defaults to "Enter Value".

    Returns:
        the value or None if cancelled
    """
    res = send_cmd("tv_ReqFloat", value, min, max, title, handle_string=False)
    return None if res.lower() == "cancel" else float(res)


def tv_req_string(title: str, text: str) -> str | None:
    """Open a string requester.

    Args:
        title: title of the requester. Defaults to "Enter Value".
        text: the initial value

    Returns:
        the value or None if cancelled
    """
    cmd_args = ["|".join([title, text])]
    if "\n" in text:
        cmd_args.insert(0, "multiline")
    res = send_cmd("tv_ReqString", *cmd_args, handle_string=False)
    return None if res.lower() == "cancel" else res


Entry: TypeAlias = "str | tuple[str, list[Entry]]"


def _entry_to_str(entry: Entry) -> str:
    """Utility function to format entries for `tv_list_request`."""
    if isinstance(entry, str):
        return entry

    value, children = entry
    return value + "/" + "|".join(map(_entry_to_str, children))


def tv_list_request(entries: list[Entry]) -> tuple[int, str]:
    """Open a popup to select an entry.

    Args:
        entries: the list of entries (either a single entry or sub entries)

    Returns:
        the position, the entry
    """
    entries_str = "|".join(map(_entry_to_str, entries))
    res = send_cmd("tv_ListRequest", entries_str, error_values=["-1 Cancel"])
    res_obj = tv_parse_list(
        res,
        with_fields=[
            ("index", int),
            ("entry", str),
        ],
    )
    index, entry = tuple(res_obj.values())
    return int(index), entry


def tv_req_file(
    mode: FileMode,
    title: str = "",
    working_dir: Path | str | None = None,
    default_name: str | None = None,
    extension_filter: str | None = None,
) -> Path | None:
    """Open a file requester.

    Args:
        mode: save or load
        title: the title of the request
        working_dir: the default folder to go. Defaults to None.
        default_name: the default name. Defaults to None.
        extension_filter: display the files with this extension. Defaults to None.

    Returns:
        the choosen path or None if cancelled
    """
    cmd_args = [
        title,
        Path(working_dir).as_posix() if working_dir else None,
        default_name,
        extension_filter,
    ]

    arg_str = "|".join([v if v is not None else "" for v in cmd_args])
    res = send_cmd("tv_ReqFile", f"{mode.value} {arg_str}", handle_string=False)

    return None if res.lower() == "cancel" else Path(res)


def tv_undo() -> None:
    """Do an undo."""
    send_cmd("tv_Undo")


def tv_update_undo() -> None:
    """Copies the contents of the current image in the current layer into the buffer undo memory.

    None of the draw commands described in this section updates this buffer memory.
    If you click on the Undo button after executing a George program, everything that the program has drawn in your image will be deleted.
    With this function you can update the undo buffer memory whenever you wish (for example at the beginning of the program).
    """
    send_cmd("tv_UpdateUndo")


def tv_undo_open_stack() -> None:
    """Open an 'undo' stack.

    Surround a piece of code with tv_undoopenstack ... tv_undoclosestack, then multiple undo will be added to this stack, and closing this stack will undo everything inside.
    (To be sure the script returns to the expected result use tv_updateundo before tv_undoopenstack)
    """
    send_cmd("tv_UndoOpenStack")


def tv_undo_close_stack(name: str = "") -> None:
    """Close an 'undo' stack (See tv_undo_open_stack)."""
    send_cmd("tv_UndoCloseStack", name)


def tv_save_mode_get() -> tuple[SaveFormat, list[str]]:
    """Get the saving alpha mode."""
    res = send_cmd("tv_SaveMode")
    res_split = res.split()
    save_format = tv_cast_to_type(res_split.pop(0), SaveFormat)
    return save_format, res_split


def tv_save_mode_set(save_format: SaveFormat, *args: str) -> None:
    """Set the saving alpha mode."""
    send_cmd("tv_SaveMode", save_format.value, *args)


def tv_alpha_load_mode_get() -> AlphaMode:
    """Set the loading alpha mode."""
    res = send_cmd("tv_AlphaLoadMode")
    return tv_cast_to_type(res, AlphaMode)


def tv_alpha_load_mode_set(mode: AlphaMode) -> None:
    """Get the loading alpha mode."""
    send_cmd("tv_AlphaLoadMode", mode.value)


def tv_alpha_save_mode_get() -> AlphaSaveMode:
    """Get the saving alpha mode."""
    res = send_cmd("tv_AlphaSaveMode")
    return tv_cast_to_type(res, AlphaSaveMode)


def tv_alpha_save_mode_set(mode: AlphaSaveMode) -> None:
    """Set the saving alpha mode."""
    send_cmd("tv_AlphaSaveMode", mode.value)


def tv_mark_in_get(
    reference: MarkReference,
) -> tuple[int, MarkAction]:
    """Get markin of the project / clip."""
    return _tv_mark(MarkType.MARKIN, reference)


def tv_mark_in_set(
    reference: MarkReference,
    frame: int | None,
    action: MarkAction,
) -> tuple[int, MarkAction]:
    """Set markin of the project / clip."""
    return _tv_mark(MarkType.MARKIN, reference, frame, action)


def tv_mark_out_get(
    reference: MarkReference,
) -> tuple[int, MarkAction]:
    """Get markout of the project / clip."""
    return _tv_mark(MarkType.MARKOUT, reference)


def tv_mark_out_set(
    reference: MarkReference, frame: int | None, action: MarkAction
) -> tuple[int, MarkAction]:
    """Set markout of the project / clip."""
    return _tv_mark(MarkType.MARKOUT, reference, frame, action)


def _tv_mark(
    mark_type: MarkType,
    reference: MarkReference,
    frame: int | None = None,
    action: MarkAction | None = None,
) -> tuple[int, MarkAction]:
    """Manage mark (markin or markout) for the project/clip.

    Args:
        mark_type: either `tv_markin` or `tv_markout` the command to send to George
        reference: `clip` or `project` the object to apply on
        frame: the frame to set the mark or None to get it
        action: `set` or `clear` the mark

    Returns:
        a tuple of the frame and the mark type
    """
    cmd_fields: FieldTypes = [("frame", int), ("mark_action", MarkAction)]
    if reference and reference == MarkReference.PROJECT:
        cmd_fields.insert(0, ("reference", MarkReference))

    cmds_args: list[Any] = [mark_type.value, reference.value]

    if frame is not None:
        cmds_args.append(frame)
    if action:
        cmds_args.append(action.value)

    result = list(tv_parse_list(send_cmd(*cmds_args), with_fields=cmd_fields).values())

    frame, mark_action = result[1:] if reference == MarkReference.PROJECT else result
    return cast(int, frame), mark_action


def tv_get_active_shape() -> TVPShape:
    """Get the current shape."""
    return tv_cast_to_type(send_cmd("tv_GetActiveShape"), TVPShape)


def tv_set_active_shape(shape: TVPShape) -> None:
    """Set the current shape and its tool parameters."""
    send_cmd("tv_SetActiveShape", shape.value)


@overload
def _tv_set_ab_pen(
    pen: Literal["a", "b"],
    x: int,
    y: int,
    z: int,
    color_format: Literal["rgb"],
    a: int | None = None,
) -> RGBColor:
    ...


@overload
def _tv_set_ab_pen(
    pen: Literal["a", "b"],
    x: int,
    y: int,
    z: int,
    color_format: Literal["hsl"],
    a: int | None = None,
) -> HSLColor:
    ...


def _tv_set_ab_pen(
    pen: Literal["a", "b"],
    x: int,
    y: int,
    z: int,
    color_format: Literal["rgb", "hsl"],
    a: int | None = None,
) -> RGBColor | HSLColor:
    """Combined function to set the `a` or `b` pen color."""
    args: list[Any] = [x, y, z]

    if a is not None:
        args.append(max(0, min(a, 255)))
    elif color_format:
        args.insert(0, color_format)

    res = send_cmd(f"tv_Set{pen.upper()}Pen", *args)
    fmt, r, g, b = res.split(" ")

    color_type: Type[RGBColor] | Type[HSLColor] = (
        RGBColor if a is not None or fmt == "rgb" else HSLColor
    )
    return color_type(int(r), int(g), int(b))


def tv_set_a_pen_rgba(color: RGBColor, alpha: int | None = None) -> RGBColor:
    """Set the APen RGBA color."""
    return _tv_set_ab_pen("a", color.r, color.g, color.b, "rgb", a=alpha)


def tv_set_a_pen_hsl(color: HSLColor) -> HSLColor:
    """Set the A Pen HSL color."""
    return _tv_set_ab_pen("a", color.h, color.s, color.l, color_format="hsl")


def tv_set_b_pen_rgba(color: RGBColor, alpha: int | None = None) -> RGBColor:
    """Set the B Pen RGBA color."""
    return _tv_set_ab_pen("b", color.r, color.g, color.b, color_format="rgb", a=alpha)


def tv_set_b_pen_hsl(color: HSLColor) -> HSLColor:
    """Set the B Pen HSL color."""
    return _tv_set_ab_pen("b", color.h, color.s, color.l, color_format="hsl")


def tv_pen(size: float) -> float:
    """Change current pen tool size."""
    res = tv_parse_dict(send_cmd("tv_Pen", size), with_fields=[("size", float)])
    return cast(float, res["size"])


def tv_pen_brush_get(tool_mode: bool = False) -> TVPPenBrush:
    """Get pen brush parameters."""
    args = ("toolmode", "backup") if tool_mode else ("backup",)
    result = send_cmd("tv_PenBrush", *args)

    # Remove the first value which is tv_penbrush
    result = result[len("tv_penbrush") + 1 :]

    res = tv_parse_dict(result, with_fields=TVPPenBrush)
    return TVPPenBrush(**res)


def tv_pen_brush_set(
    mode: DrawingMode | None = None,
    size: int | None = None,
    opacity: int | None = None,
    tool_mode: bool = False,
    reset: bool = False,
) -> TVPPenBrush:
    """Manage pen brush."""
    args = {
        "mode": mode.value if mode else None,
        "size": size,
        "opacity": opacity,
    }

    args_list = args_dict_to_list(args)

    if tool_mode:
        args_list.append("toolmode")
    if reset:
        args_list.append("reset")

    send_cmd("tv_PenBrush", *args_list)

    # Since TVPaint is returning only the values that were modified
    # this is almost impossible to parse so we call get
    return tv_pen_brush_get()


def tv_rect(
    tlx: float,
    tly: float,
    brx: float,
    bry: float,
    button: RectButton | None = None,
) -> None:
    """Draws a rectangle with stroke only.

    Args:
        tlx: top left x coordinate
        tly: top left y coordinate
        brx: bottom right x coordinate
        bry: bottom right y coordinate
        button: use left or right click button (left draws, right erases)
    """
    args: list[float] = [tlx, tly, brx, bry]
    if button:
        args.append(button.value)
    send_cmd("tv_Rect", *args)


def tv_rect_fill(
    tlx: float,
    tly: float,
    brx: float,
    bry: float,
    grx: float = 0,
    gry: float = 0,
    erase_mode: bool = False,
    tool_mode: bool = False,
) -> None:
    """Draws a filled rectangle.

    Args:
        tlx: top left x coordinate
        tly: top left y coordinate
        brx: bottom right x coordinate
        bry: bottom right y coordinate
        grx: gradient vector x
        gry: gradient vector y
        erase_mode: erase drawing mode
        tool_mode: manage drawing mode
    """
    args: list[Any] = [tlx, tly, brx, bry, grx, gry, int(erase_mode)]
    if tool_mode:
        args.insert(0, "toolmode")
    send_cmd("tv_RectFill", *args)


def tv_exposure_next() -> int:
    """Go to the next instance head.

    Returns:
        The 'new' current frame
    """
    return int(send_cmd("tv_ExposureNext"))


def tv_exposure_prev() -> int:
    """Go to the previous instance head (*before* the current instance).

    Returns:
        The 'new' current frame
    """
    return int(send_cmd("tv_ExposurePrev"))
