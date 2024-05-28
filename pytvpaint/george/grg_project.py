"""Project related George functions and enums."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pytvpaint.george.client import send_cmd, try_cmd
from pytvpaint.george.client.parse import (
    tv_cast_to_type,
    tv_parse_list,
)
from pytvpaint.george.exceptions import NoObjectWithIdError
from pytvpaint.george.grg_base import (
    FieldOrder,
    GrgErrorValue,
    ResizeOption,
    RGBColor,
    TVPSound,
)


@dataclass(frozen=True)
class TVPProject:
    """TVPaint project info values."""

    id: str = field(metadata={"parsed": False})

    path: Path
    width: int
    height: int
    pixel_aspect_ratio: float
    frame_rate: float
    field_order: FieldOrder
    start_frame: int


class BackgroundMode(Enum):
    """The project background mode.

    Attributes:
        CHECK:
        COLOR:
        NONE:
    """

    CHECK = "check"
    COLOR = "color"
    NONE = "none"


def tv_background_get() -> (
    tuple[BackgroundMode, tuple[RGBColor, RGBColor] | RGBColor | None]
):
    """Get the background mode of the project, and the color(s) if in `color` or `check` mode.

    Returns:
        mode: the background mode
        colors: the background colors if any

    """
    res = send_cmd("tv_Background")

    mode, *values = res.split(" ")

    if mode == BackgroundMode.NONE.value:
        return BackgroundMode.NONE, None

    if mode == BackgroundMode.CHECK.value:
        c1 = map(int, values[:3])
        c2 = map(int, values[3:])
        return BackgroundMode.CHECK, (RGBColor(*c1), RGBColor(*c2))

    return BackgroundMode.COLOR, RGBColor(*map(int, values))


def tv_background_set(
    mode: BackgroundMode,
    color: tuple[RGBColor, RGBColor] | RGBColor | None = None,
) -> None:
    """Set the background mode of the project.

    Args:
        mode: color mode (None, checker or one color)
        color: None for None mode, RBGColor for one color, and tuple of RGBColors for checker
    """
    args = []

    if mode == BackgroundMode.CHECK and isinstance(color, tuple):
        c1, c2 = color
        args = [c1.r, c1.g, c1.b, c2.r, c2.g, c2.b]
    elif mode == BackgroundMode.COLOR and isinstance(color, RGBColor):
        args = [color.r, color.g, color.b]

    send_cmd("tv_Background", mode.value, *args)


@try_cmd(exception_msg="Project created but may be corrupted")
def tv_project_new(
    project_path: Path | str,
    width: int = 1920,
    height: int = 1080,
    pixel_aspect_ratio: float = 1.0,
    frame_rate: float = 24.0,
    field_order: FieldOrder = FieldOrder.NONE,
    start_frame: int = 1,
) -> str:
    """Create a new project.

    Raises:
        GeorgeError: if an error occurred during the project creation
    """
    return send_cmd(
        "tv_ProjectNew",
        Path(project_path).as_posix(),
        width,
        height,
        pixel_aspect_ratio,
        frame_rate,
        field_order.value,
        start_frame,
        error_values=[GrgErrorValue.EMPTY],
    )


@try_cmd(exception_msg="Invalid format")
def tv_load_project(project_path: Path | str, silent: bool = False) -> str:
    """Load a file as a project if possible or open Import panel.

    Raises:
        FileNotFoundError: if the project file doesn't exist
        GeorgeError: if the provided file is in an invalid format
    """
    project_path = Path(project_path)

    if not project_path.exists():
        raise FileNotFoundError(f"Project not found at: {project_path.as_posix()}")

    args: list[Any] = [project_path.as_posix()]

    if silent:
        args.extend(["silent", int(silent)])

    return send_cmd("tv_LoadProject", *args, error_values=[-1])


def tv_save_project(project_path: Path | str) -> None:
    """Save the current project as tvpp."""
    project_path = Path(project_path)
    parent = project_path.parent

    if not parent.exists():
        msg = f"Can't save because parent folder does not exist: {parent.as_posix()}"
        raise ValueError(msg)

    send_cmd("tv_SaveProject", project_path.as_posix())


@try_cmd(exception_msg="Can't duplicate the current project")
def tv_project_duplicate() -> None:
    """Duplicate the current project.

    Raises:
        GeorgeError: if an error occurred during the project creation.
    """
    send_cmd("tv_ProjectDuplicate", error_values=[0])


@try_cmd(exception_msg="No project at provided position")
def tv_project_enum_id(position: int) -> str:
    """Get the id of the project at the given position.

    Raises:
        GeorgeError: if no project found at the provided position.
    """
    return send_cmd("tv_ProjectEnumId", position, error_values=[GrgErrorValue.NONE])


def tv_project_current_id() -> str:
    """Get the id of the current project."""
    return send_cmd("tv_ProjectCurrentId")


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid project id",
)
def tv_project_info(project_id: str) -> TVPProject:
    """Get info of the given project.

    Raises:
        NoObjectWithIdError: if given an invalid project id
    """
    result = send_cmd("tv_ProjectInfo", project_id, error_values=[GrgErrorValue.EMPTY])
    project = tv_parse_list(result, with_fields=TVPProject)
    project["id"] = project_id
    return TVPProject(**project)


def tv_get_project_name() -> str:
    """Returns the save path of the current project."""
    return send_cmd("tv_GetProjectName")


def tv_project_select(project_id: str) -> str:
    """Make the given project current."""
    return send_cmd("tv_ProjectSelect", project_id)


def tv_project_close(project_id: str) -> None:
    """Close the given project."""
    send_cmd("tv_ProjectClose", project_id)


def tv_resize_project(width: int, height: int) -> None:
    """Resize the current project.

    Note:
        creates a resized copy of the project with a new id
    """
    send_cmd("tv_ResizeProject", width, height)


def tv_resize_page(width: int, height: int, resize_opt: ResizeOption) -> None:
    """Create a new resized project and close the current one."""
    send_cmd("tv_ResizePage", width, height, resize_opt.value)


def tv_get_width() -> int:
    """Get the current project width."""
    return int(send_cmd("tv_GetWidth"))


def tv_get_height() -> int:
    """Get the current project height."""
    return int(send_cmd("tv_GetHeight"))


def tv_ratio() -> float:
    """Get the current project pixel aspect ratio.

    Bug:
        Doesn't work and always returns an empty string
    """
    return float(send_cmd("tv_GetRatio", error_values=[GrgErrorValue.EMPTY]))


def tv_get_field() -> FieldOrder:
    """Get the current project field mode."""
    return tv_cast_to_type(send_cmd("tv_GetField"), cast_type=FieldOrder)


def tv_project_save_sequence(
    export_path: Path | str,
    use_camera: bool = False,
    start: int | None = None,
    end: int | None = None,
) -> None:
    """Save the current project."""
    export_path = Path(export_path).resolve()
    args: list[Any] = [export_path.as_posix()]

    if use_camera:
        args.append("camera")
    if start is not None and end is not None:
        args.extend((start, end))

    send_cmd(
        "tv_ProjectSaveSequence",
        *args,
        error_values=[-1],
    )


def tv_project_render_camera(project_id: str) -> str:
    """Render the given project's camera view to a new project.

    Returns:
        the new project id
    """
    return send_cmd(
        "tv_ProjectRenderCamera",
        project_id,
        error_values=[GrgErrorValue.ERROR],
    )


def tv_frame_rate_get() -> tuple[float, float]:
    """Get the framerate of the current project."""
    parse = tv_parse_list(
        send_cmd("tv_FrameRate", 1, "info"),
        with_fields=[
            ("project_fps", float),
            ("playback_fps", float),
        ],
    )
    project_fps, playback_fps = parse.values()
    return project_fps, playback_fps


def tv_frame_rate_set(
    frame_rate: float, time_stretch: bool = False, preview: bool = False
) -> None:
    """Get the framerate of the current project."""
    args: list[Any] = []
    if time_stretch:
        args = ["timestretch"]
    if preview:
        args = ["preview"]
    args.insert(0, frame_rate)
    send_cmd("tv_FrameRate", *args)


def tv_frame_rate_project_set(frame_rate: float, time_stretch: bool = False) -> None:
    """Set the framerate of the current project."""
    args: list[Any] = [frame_rate]
    if time_stretch:
        args.append("timestretch")
    send_cmd("tv_FrameRate", *args)


def tv_frame_rate_preview_set(frame_rate: float) -> None:
    """Set the framerate of the preview (playback)."""
    send_cmd("tv_FrameRate", frame_rate, "preview")


def tv_project_current_frame_get() -> int:
    """Get the current frame of the current project."""
    return int(send_cmd("tv_ProjectCurrentFrame"))


def tv_project_current_frame_set(frame: int) -> int:
    """Set the current frame of the current project.

    Note:
        this is relative to the current clip markin
    """
    return int(send_cmd("tv_ProjectCurrentFrame", frame))


def tv_load_palette(palette_path: Path | str) -> None:
    """Load a palette(s) from a file/directory.

    Raises:
        FileNotFoundError: if palette was not found at the provided path
    """
    palette_path = Path(palette_path)
    if not palette_path.exists():
        raise FileNotFoundError(f"Palette not found at: {palette_path.as_posix()}")
    send_cmd("tv_LoadPalette", palette_path.as_posix())


def tv_save_palette(palette_path: Path | str) -> None:
    """Save the current palette.

    Raises:
        FileNotFoundError: if palette save directory doesn't exist
    """
    palette_path = Path(palette_path)

    if not palette_path.parent.exists():
        parent_path = palette_path.parent.as_posix()
        raise NotADirectoryError(
            f"Can't save palette because parent folder doesn't exist: {parent_path}"
        )

    send_cmd("tv_SavePalette", palette_path.as_posix())


def tv_project_save_video_dependencies() -> None:
    """Saves current project video dependencies."""
    send_cmd("tv_ProjectSaveVideoDependencies")


def tv_project_save_audio_dependencies() -> None:
    """Saves current project audio dependencies."""
    send_cmd("tv_ProjectSaveAudioDependencies")


def tv_sound_project_info(project_id: str, track_index: int) -> TVPSound:
    """Get information about a project soundtrack."""
    res = send_cmd(
        "tv_SoundProjectInfo", project_id, track_index, error_values=[-1, -2, -3]
    )
    res_parse = tv_parse_list(res, with_fields=TVPSound)
    return TVPSound(**res_parse)


def tv_sound_project_new(sound_path: Path | str) -> None:
    """Add a new soundtrack to the current project."""
    path = Path(sound_path)
    if not path.exists():
        raise ValueError(f"Sound file not found at : {path.as_posix()}")

    send_cmd("tv_SoundProjectNew", path.as_posix(), error_values=[-1, -3, -4])


def tv_sound_project_remove(track_index: int) -> None:
    """Remove a soundtrack from the current project."""
    send_cmd("tv_SoundProjectRemove", track_index, error_values=[-2])


def tv_sound_project_reload(project_id: str, track_index: int) -> None:
    """Reload a project soundtracks file."""
    send_cmd(
        "tv_SoundProjectReload",
        project_id,
        track_index,
        error_values=[-1, -2, -3],
    )


def tv_sound_project_adjust(
    track_index: int,
    mute: bool | None = None,
    volume: float | None = None,
    offset: float | None = None,
    fade_in_start: float | None = None,
    fade_in_stop: float | None = None,
    fade_out_start: float | None = None,
    fade_out_stop: float | None = None,
    color_index: int | None = None,
) -> None:
    """Change the current project's soundtrack settings."""
    cur_options = tv_sound_project_info(tv_project_current_id(), track_index)
    args: list[int | float | None] = []

    optional_args = [
        (int(mute) if mute is not None else None, int(cur_options.mute)),
        (volume, cur_options.volume),
        (offset, cur_options.offset),
        (fade_in_start, cur_options.fade_in_start),
        (fade_in_stop, cur_options.fade_in_stop),
        (fade_out_start, cur_options.fade_out_start),
        (fade_out_stop, cur_options.fade_out_stop),
    ]
    for arg, default_value in optional_args:
        args.append(arg if arg is not None else default_value)

    args.append(color_index)
    send_cmd("tv_SoundProjectAdjust", track_index, *args, error_values=[-2, -3])


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid project id",
)
def tv_project_header_info_get(project_id: str) -> str:
    """Get the project header info.

    Raises:
        NoObjectWithIdError: if given an invalid project id
    """
    return send_cmd(
        "tv_ProjectHeaderInfo",
        project_id,
        error_values=[GrgErrorValue.ERROR],
    ).strip('"')


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid project id",
)
def tv_project_header_info_set(project_id: str, text: str) -> None:
    """Set the project header info.

    Raises:
        NoObjectWithIdError: if given an invalid project id
    """
    send_cmd(
        "tv_ProjectHeaderInfo",
        project_id,
        text,
        error_values=[GrgErrorValue.ERROR],
    )


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid project id",
)
def tv_project_header_author_get(project_id: str) -> str:
    """Get the project author info.

    Raises:
        NoObjectWithIdError: if given an invalid project id
    """
    return send_cmd(
        "tv_ProjectHeaderAuthor",
        project_id,
        error_values=[GrgErrorValue.ERROR],
    ).strip('"')


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid project id",
)
def tv_project_header_author_set(project_id: str, text: str) -> None:
    """Set the project author info.

    Raises:
        NoObjectWithIdError: if given an invalid project id
    """
    send_cmd(
        "tv_ProjectHeaderAuthor",
        project_id,
        text,
        error_values=[GrgErrorValue.ERROR],
    )


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid project id",
)
def tv_project_header_notes_get(project_id: str) -> str:
    """Get the project notes.

    Raises:
        NoObjectWithIdError: if given an invalid project id
    """
    return send_cmd(
        "tv_ProjectHeaderNotes",
        project_id,
        error_values=[GrgErrorValue.ERROR],
    ).strip('"')


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid project id",
)
def tv_project_header_notes_set(project_id: str, text: str) -> None:
    """Set the project notes.

    Raises:
        NoObjectWithIdError: if given an invalid project id
    """
    send_cmd(
        "tv_ProjectHeaderNotes",
        project_id,
        text,
        error_values=[GrgErrorValue.ERROR],
    )


def tv_start_frame_get() -> int:
    """Get the start frame of the current project."""
    return int(send_cmd("tv_StartFrame"))


def tv_start_frame_set(start_frame: int) -> int:
    """Set the start frame of the current project."""
    return int(send_cmd("tv_StartFrame", start_frame))
