"""All George values as enum and functions which are not specific to any TVPaint element."""

from __future__ import annotations

import contextlib
from collections.abc import Generator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, TypeVar, cast, overload

from typing_extensions import Literal, TypeAlias

from pytvpaint import log
from pytvpaint.george.client import send_cmd
from pytvpaint.george.client.parse import (
    FieldTypes,
    args_dict_to_list,
    tv_cast_to_type,
    tv_parse_dict,
    tv_parse_list,
)


class GrgErrorValue:
    """Common George error values.

    Attributes:
        EMPTY (str): See `tv_clipinfo` for example
        NONE (str): See `tv_clipenumid` for example
        ERROR (str): See `tv_setapen` for example
    """

    EMPTY = ""
    NONE = "none"
    ERROR = "error"


class GrgBoolState(Enum):
    """George booleans.

    Attributes:
        ON:
        OFF:
    """

    ON = "on"
    OFF = "off"


class FieldOrder(Enum):
    """Field order of the camera.

    Attributes:
        NONE:
        LOWER:
        UPPER:
    """

    NONE = "none"
    LOWER = "lower"
    UPPER = "upper"


class MarkType(Enum):
    """The mark command.

    Attributes:
        MARKIN:
        MARKOUT:
    """

    MARKIN = "tv_markin"
    MARKOUT = "tv_markout"


class MarkReference(Enum):
    """The object to mark.

    Attributes:
        PROJECT:
        CLIP:
    """

    PROJECT = "project"
    CLIP = "clip"


class MarkAction(Enum):
    """The mark action.

    Attributes:
        SET:
        CLEAR:
    """

    SET = "set"
    CLEAR = "clear"


class RectButton(Enum):
    """The rect button when drawing.

    Attributes:
        LEFT:
        RIGHT:
    """

    LEFT = 0
    RIGHT = 1


class TVPShape(Enum):
    """The shape tools.

    Attributes:
        B_SPLINE:
        BEZIER:
        BEZIER_FILL:
        CAMERA:
        CIRCLE:
        CIRCLE_2PTS:
        CIRCLE_3PTS:
        CIRCLE_FILL:
        CIRCLE_2PTS_FILL:
        CIRCLE_3PTS_FILL:
        CROP:
        CUT_RECT:
        CUT_POLY:
        CUT_FREE_HAND:
        CUT_FLOOD:
        DOT:
        FLOOD:
        FREE_HAND_LINE:
        FREE_HAND_FILL:
        ELLIPSE:
        ELLIPSE_FILL:
        ELLIPSE_2PTS:
        ELLIPSE_2PTS_FILL:
        LINE:
        LINE_FILL:
        PLANNING:
        POSITION:
        RECTANGLE:
        RECTANGLE_FILL:
        SELECT_RECTANGLE:
        SELECT_ELLIPSE:
        SELECT_2PTS:
        SELECT_3PTS:
        SELECT_POLY:
        SELECT_FREE_HAND:
        SELECT_FLOOD:
        SELECT_COLOR:
        SELECT_BEZIER:
        SELECT_B_SPLINE:
        SINGLE_DOT:
        SPLIT_3PTS:
        SPLINE_FILL:
        WARP:
        WRAP:
        ZOOM_IN:
        ZOOM_OUT:
        ZOOM_HAND:
        ZOOM_RECT:
    """

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
    """Resize options for projects.

    Attributes:
        EMPTY:
        CROP:
        STRETCH:
    """

    EMPTY = 0
    CROP = 1
    STRETCH = 2


class SpriteLayout(Enum):
    """Sprite layout when exporting as sprites.

    Attributes:
        RECTANGLE:
        HORIZONTAL:
        VERTICAL:
        DIAGONAL:
        ANTI_DIAGONAL:
    """

    RECTANGLE = "rectangle"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    DIAGONAL = "diagonal"
    ANTI_DIAGONAL = "antidiagonal"


class AlphaMode(Enum):
    """The alpha load mode.

    Attributes:
        PREMULTIPLY:
        NO_PREMULTIPLY:
        NO_ALPHA:
        ALPHA_ONLY:
        GUESS:
    """

    PREMULTIPLY = "premultiply"
    NO_PREMULTIPLY = "nopremultiply"
    NO_ALPHA = "noalpha"
    ALPHA_ONLY = "alphaonly"
    GUESS = "guess"


class AlphaSaveMode(Enum):
    """The alpha save mode.

    Attributes:
        PREMULTIPLY:
        NO_PREMULTIPLY:
        NO_ALPHA:
        ALPHA_ONLY:
        GUESS:
        ALPHA_BINARY:
    """

    PREMULTIPLY = "premultiply"
    NO_PREMULTIPLY = "nopremultiply"
    NO_ALPHA = "noalpha"
    ALPHA_ONLY = "alphaonly"
    GUESS = "guess"
    ALPHA_BINARY = "alphabinary"


class SaveFormat(Enum):
    """All save formats.

    Attributes:
        AVI:
        BMP:
        CINEON:
        DEEP:
        DPX:
        FLI:
        GIF:
        ILBM:
        JPG: jpeg
        MKV: Mode=1017
        MOV: Mode=1015
        MP4: Mode=1016
        PCX:
        PDF:
        PNG:
        PSD:
        SGI: Mode=16
        SOFTIMAGE: Mode=10
        SUNRASTER: sun
        TGA: tga
        TIFF: Mode=15
        VPB:
        WEBM: Mode=1018
    """

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
        """Returns the correct tvpaint format value from a string extension."""
        extension = extension.replace(".", "").upper()
        if not hasattr(SaveFormat, extension):
            raise ValueError(
                f"Could not find format ({extension}) in accepted formats ({SaveFormat})"
            )
        return cast(SaveFormat, getattr(cls, extension.upper()))

    @classmethod
    def is_image(cls, extension: str) -> bool:
        """Returns True if the extension correspond to an image format."""
        extension = extension.replace(".", "").lower()
        image_formats = [
            "bmp",
            "cin",
            "deep",
            "dpx",
            "ilbm",
            "jpg",
            "jpeg",
            "pcx",
            "png",
            "psd",
            "sgi",
            "pic",
            "ras",
            "sun",
            "tga",
            "tiff",
        ]
        return extension in image_formats


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
    """All the blending modes.

    Attributes:
        COLOR:
        BEHIND:
        ERASE:
        SHADE:
        LIGHT:
        COLORIZE:
        HUE:
        SATURATION:
        VALUE:
        ADD:
        SUB:
        MULTIPLY:
        SCREEN:
        REPLACE:
        COPY:
        DIFFERENCE:
        DIVIDE:
        OVERLAY:
        OVERLAY2:
        LIGHT2:
        SHADE2:
        HARDLIGHT:
        SOFTLIGHT:
        GRAIN_EXTRACT:
        GRAIN_MERGE:
        SUB2:
        DARKEN:
        LIGHTEN:
    """

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
    """All the drawing modes.

    Attributes:
        COLOR:
        BEHIND:
        ERASE:
        PANTO:
        MERGE:
        SHADE:
        LIGHT:
        COLORIZE:
        TINT:
        GRAIN:
        BLUR:
        NOISE:
        NEGATIVE:
        SHARP:
        EMBOSS:
        SOLARIZE:
        SATURATE:
        UNSATURATE:
        ADD:
        SUB:
        MULTIPLY:
        SCREEN:
        DIFF:
        HEALING:
        BURN:
        DODGE:
        DARKEN:
        LIGHTEN:
    """

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
    """All the TVPaint menu elements.

    Attributes:
        SHOW_UI:
        HIDE_UI:
        RESIZE_UI:
        CENTER_DISPLAY:
        FIT_DISPLAY:
        FRONT:
        BACK:
        ASPECT_RATIO:
        CLIP:
        PROJECT:
        XSHEET:
        NOTES:
    """

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
    """File mode save or load.

    Attributes:
        SAVE:
        LOAD:
    """

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


def tv_quit() -> None:
    """Closes the TVPaint instance."""
    send_cmd("tv_Quit")


def tv_host2back() -> None:
    """Minimize the TVPaint window."""
    send_cmd("tv_Host2Back")


def tv_host2front() -> None:
    """Restore the TVPaint window after being minimized."""
    send_cmd("tv_Host2Front")


def tv_menu_hide() -> None:
    """Switch to inlay view and hide all non-docking panels."""
    send_cmd("tv_MenuHide")


def add_some_magic(
    i_am_a_badass: bool = False, magic_number: int | None = None
) -> None:
    """Don't use ! Will change your life forever..."""
    if not i_am_a_badass:
        log.warning("Sorry, you're not enough of a badass for this function...")

    magic_number = magic_number or 14
    send_cmd("tv_MagicNumber", magic_number)
    log.info("Totally worth it, right ? ^^")


def tv_menu_show(
    menu_element: MenuElement | None = None, *menu_options: Any, current: bool = False
) -> None:
    """For the complete documentation, see: https://www.tvpaint.com/doc/tvpaint-animation-11/george-commands#tv_menushow."""
    cmd_args: list[str] = []

    if current:
        cmd_args.append("current")

    if menu_element:
        cmd_args.append(menu_element.value)

    send_cmd("tv_MenuShow", *cmd_args, *menu_options)


def tv_request(msg: str, confirm_text: str = "Yes", cancel_text: str = "No") -> bool:
    """Open a confirmation prompt with a message.

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
    """Open a prompt to request an integer (within a range).

    Args:
        value: the initial value
        min: the minimum value
        max: the maximum value
        title: title of the prompt dialog. Defaults to "Enter Value".

    Returns:
        the value or None if cancelled
    """
    res = send_cmd("tv_ReqNum", value, min, max, title, handle_string=False)
    return None if res.lower() == "cancel" else int(res)


def tv_req_angle(
    value: float, min: float, max: float, title: str = "Enter Value"
) -> float | None:
    """Open a prompt to request an angle (in degree).

    Args:
        value: the initial value
        min: the minimum value
        max: the maximum value
        title: title of the prompt. Defaults to "Enter Value".

    Returns:
        the value or None if cancelled
    """
    res = send_cmd("tv_ReqAngle", value, min, max, title, handle_string=False)
    return None if res.lower() == "cancel" else float(res)


def tv_req_float(
    value: float, min: float, max: float, title: str = "Enter value"
) -> float | None:
    """Open a prompt to request a float.

    Args:
        value: the initial value
        min: the minimum value
        max: the maximum value
        title: title of the prompt. Defaults to "Enter Value".

    Returns:
        the value or None if cancelled
    """
    res = send_cmd("tv_ReqFloat", value, min, max, title, handle_string=False)
    return None if res.lower() == "cancel" else float(res)


def tv_req_string(title: str, text: str) -> str | None:
    """Open a prompt to request a string.

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
    """Open a prompt to request a selection in a list.

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
    """Open a prompt to request a file.

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


def tv_save_mode_set(
    save_format: SaveFormat, *format_options: str | int | float
) -> None:
    """Set the saving alpha mode."""
    send_cmd("tv_SaveMode", save_format.value, *format_options)


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


def tv_set_active_shape(shape: TVPShape, **shape_kwargs: Any) -> None:
    """Set the current shape and its tool parameters.

    Args:
        shape: the shape to set
        **shape_kwargs: the shape specific parameters as keyword arguments
    """
    send_cmd("tv_SetActiveShape", shape.value, *args_dict_to_list(shape_kwargs))


@overload
def _tv_set_ab_pen(
    pen: Literal["a", "b"],
    x: int,
    y: int,
    z: int,
    color_format: Literal["rgb"],
    a: int | None = None,
) -> RGBColor: ...


@overload
def _tv_set_ab_pen(
    pen: Literal["a", "b"],
    x: int,
    y: int,
    z: int,
    color_format: Literal["hsl"],
    a: int | None = None,
) -> HSLColor: ...


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

    color_type: type[RGBColor] | type[HSLColor] = (
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
    """Change current pen tool size. This function is most likely deprecated it is undocumented in the George reference but still works."""
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


def tv_line(
    xy1: tuple[int, int],
    xy2: tuple[int, int],
    right_click: bool = False,
    dry: bool = False,
) -> None:
    """Draw a line (with the current brush).

    Args:
        xy1: start position as (x, y)
        xy2: end position as (x, y)
        right_click: True to emulate right click, False to emulate left click. Default is False
        dry: True for dry mode
    """
    args = [
        *xy1,
        *xy2,
        bool(right_click),
        bool(dry),
    ]
    send_cmd("tv_Line", *args)


def tv_text(text: str, x: int, y: int, use_b_pen: bool = False) -> None:
    """Write text in a layer instance.

    Args:
        text: text to write
        x: text x position
        y: text y position
        use_b_pen: True will use b pen, False will use A pen
    """
    send_cmd("tv_Text", x, y, int(use_b_pen), text)


def tv_text_brush(text: str) -> None:
    """Set the text for the text brush.

    Args:
        text: text to write
    """
    send_cmd("tv_TextBrush", text)


def tv_rect(
    tlx: float,
    tly: float,
    brx: float,
    bry: float,
    button: RectButton | None = None,
) -> None:
    """Draws an unfilled rectangle.

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


def tv_fast_line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    r: int = 255,
    b: int = 255,
    g: int = 0,
    a: int = 255,
) -> None:
    """Draw a line (1 pixel size and not antialiased)."""
    send_cmd("tv_fastline", x1, y1, x2, y2, r, g, b, a)
