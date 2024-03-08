"""Clip related George functions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pytvpaint.george.base import (
    FieldOrder,
    GrgErrorValue,
    SaveFormat,
    SpriteLayout,
    TVPSound,
)
from pytvpaint.george.client import send_cmd, try_cmd
from pytvpaint.george.client.parse import (
    args_dict_to_list,
    consecutive_optional_args_to_list,
    tv_parse_dict,
    tv_parse_list,
)
from pytvpaint.george.exceptions import NoObjectWithIdError


@dataclass(frozen=True)
class TVPClip:
    """A TVPaint clip."""

    id: int = field(metadata={"parsed": False})

    name: str
    is_current: bool
    is_hidden: bool
    is_selected: bool
    storyboard_start_frame: int
    first_frame: int
    last_frame: int
    frame_count: int
    mark_in: int
    mark_out: int
    color_idx: int


class PSDSaveMode(Enum):
    """PSD save modes."""

    ALL = "all"
    IMAGE = "image"
    MARKIN = "markin"


@try_cmd(raise_exc=NoObjectWithIdError)
def tv_clip_info(clip_id: int) -> TVPClip:
    """Get the information of the given clip."""
    result = send_cmd("tv_ClipInfo", clip_id, error_values=[GrgErrorValue.EMPTY])
    clip = tv_parse_dict(result, with_fields=TVPClip)
    clip["id"] = clip_id
    return TVPClip(**clip)


@try_cmd(
    exception_msg="Invalid scene id or clip position or elements have been removed"
)
def tv_clip_enum_id(scene_id: int, clip_position: int) -> int:
    """Get the id of the clip at the given position inside the given scene."""
    return int(
        send_cmd(
            "tv_ClipEnumId",
            scene_id,
            clip_position,
            error_values=[GrgErrorValue.NONE],
        )
    )


def tv_clip_current_id() -> int:
    """Get the id of the current clip."""
    return int(send_cmd("tv_ClipCurrentId"))


def tv_clip_new(name: str) -> None:
    """Create a new clip."""
    send_cmd("tv_ClipNew", name, handle_string=False)


def tv_clip_duplicate(clip_id: int) -> None:
    """Duplicate the given clip."""
    send_cmd("tv_ClipDuplicate", clip_id)


def tv_clip_close(clip_id: int) -> None:
    """Remove the given clip."""
    send_cmd("tv_ClipClose", clip_id)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid clip id",
)
def tv_clip_name_get(clip_id: int) -> str:
    """Get the clip name."""
    return send_cmd("tv_ClipName", clip_id, error_values=[GrgErrorValue.EMPTY])


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid clip id",
)
def tv_clip_name_set(clip_id: int, name: str) -> None:
    """Set the clip name."""
    send_cmd("tv_ClipName", clip_id, name, error_values=[GrgErrorValue.EMPTY])


def tv_clip_move(clip_id: int, scene_id: int, position: int) -> None:
    """Manage clip position."""
    send_cmd("tv_ClipMove", clip_id, scene_id, position)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid clip id",
)
def tv_clip_hidden_get(clip_id: int) -> bool:
    """Get clip hidability."""
    res = send_cmd("tv_ClipHidden", clip_id, error_values=[GrgErrorValue.EMPTY])
    return bool(int(res))


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid clip id",
)
def tv_clip_hidden_set(clip_id: int, new_state: bool) -> None:
    """Set clip hidability."""
    send_cmd(
        "tv_ClipHidden", clip_id, int(new_state), error_values=[GrgErrorValue.EMPTY]
    )


def tv_clip_select(clip_id: int) -> None:
    """Activate/Make current the given clip."""
    send_cmd("tv_ClipSelect", clip_id)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid clip id",
)
def tv_clip_selection_get(clip_id: int) -> bool:
    """Get the given clip selection state."""
    res = send_cmd("tv_ClipSelection", clip_id, error_values=[-1])
    return bool(int(res))


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid clip id",
)
def tv_clip_selection_set(clip_id: int, new_state: bool) -> None:
    """Set the given clip selection state."""
    send_cmd("tv_ClipSelection", clip_id, int(new_state), error_values=[-1])


def tv_first_image() -> int:
    """Get the first image of the clip."""
    return int(send_cmd("tv_FirstImage"))


def tv_last_image() -> int:
    """Get the last image of the clip."""
    return int(send_cmd("tv_LastImage"))


@try_cmd(exception_msg="Invalid format for sequence")
def tv_load_sequence(
    seq_path: Path | str,
    offset_count: tuple[int, int] | None = None,
    field_order: FieldOrder | None = None,
    stretch: bool | None = None,
    time_stretch: bool | None = None,
    preload: bool | None = None,
) -> int:
    """Open a sequence of files in a new layer.

    Args:
        seq_path: the first file of the sequence to load
        offset_count: the start and number of image of sequence to load. Defaults to None.
        field_order: the field order. Defaults to None.
        stretch: Stretch each image to the size of the layer. Defaults to None.
        time_stretch: Once loaded, the layer will have a new number of image corresponding to the project framerate. Defaults to None.
        preload: Load all the images in memory, no more reference on the files. Defaults to None.

    Raises:
        ValueError: if the input file path doesn't exist

    Returns:
        the number of images of the new layer
    """
    seq_path = Path(seq_path)

    if not seq_path.exists():
        raise ValueError(f"File not found at: {seq_path.as_posix()}")

    args: list[int | str | None] = [field_order.value if field_order else None]

    if offset_count is not None:
        offset, count = offset_count
        args.insert(0, count)
        args.insert(0, offset)

    # Filter None inline arguments
    args = [a for a in args if a is not None]

    args += args_dict_to_list(
        {
            "stretch": stretch,
            "timestretch": time_stretch,
            "preload": preload,
        }
    )

    result = send_cmd(
        "tv_LoadSequence",
        seq_path.as_posix(),
        *args,
        error_values=[-1],
    )

    return int(result)


@try_cmd(exception_msg="No bookmark at provided position")
def tv_bookmarks_enum(position: int) -> int:
    """Get the image index (in the clip) corresponding to the bookmark at the given position."""
    return int(
        send_cmd("tv_BookmarksEnum", position, error_values=[GrgErrorValue.NONE])
    )


def tv_bookmark_set(frame: int) -> None:
    """Set a bookmark at the given image index."""
    send_cmd("tv_BookmarkSet", frame)


def tv_bookmark_clear(frame: int) -> None:
    """Remove a bookmark at the given image index."""
    send_cmd("tv_BookmarkClear", frame)


def tv_bookmark_next() -> None:
    """Change the current image to the next bookmarked image."""
    send_cmd("tv_BookmarkNext")


def tv_bookmark_prev() -> None:
    """Change the current image to the previous bookmarked image."""
    send_cmd("tv_BookmarkPrev")


def tv_clip_color_get(clip_id: int) -> int:
    """Get the clip color."""
    return int(send_cmd("tv_ClipColor", clip_id, error_values=[GrgErrorValue.EMPTY]))


def tv_clip_color_set(clip_id: int, color_index: int) -> None:
    """Set the clip color."""
    send_cmd("tv_ClipColor", clip_id, color_index, error_values=[GrgErrorValue.EMPTY])


def tv_clip_action_get(clip_id: int) -> str:
    """Get the action text of the clip."""
    # We explicitly check if the clip exists because the error value is an empty string
    # and we can't determine if the action text is empty or the clip_id is invalid...
    tv_clip_name_get(clip_id)
    return send_cmd("tv_ClipAction", clip_id)


def tv_clip_action_set(clip_id: int, text: str) -> None:
    """Set the action text of the clip."""
    # See tv_clip_action_get above
    tv_clip_name_get(clip_id)
    send_cmd("tv_ClipAction", clip_id, text)


def tv_clip_dialog_get(clip_id: int) -> str:
    """Get the dialog text of the clip."""
    # See tv_clip_action_get above
    tv_clip_name_get(clip_id)
    return send_cmd("tv_ClipDialog", clip_id)


def tv_clip_dialog_set(clip_id: int, dialog: str) -> None:
    """Set the dialog text of the clip."""
    # See tv_clip_action_get above
    tv_clip_name_get(clip_id)
    send_cmd("tv_ClipDialog", clip_id, dialog)


def tv_clip_note_get(clip_id: int) -> str:
    """Get the note text of the clip."""
    # See tv_clip_action_get above
    tv_clip_name_get(clip_id)
    return send_cmd("tv_ClipNote", clip_id)


def tv_clip_note_set(clip_id: int, note: str) -> None:
    """Set the note text of the clip."""
    # See tv_clip_action_get above
    tv_clip_name_get(clip_id)
    send_cmd("tv_ClipNote", clip_id, note)


@try_cmd(exception_msg="Can't create file")
def tv_save_clip(export_path: Path | str) -> None:
    """Save the current clip as .tvp format."""
    export_path = Path(export_path)
    send_cmd("tv_SaveClip", export_path.as_posix())


def tv_save_display(export_path: Path | str) -> None:
    """Save the display."""
    export_path = Path(export_path).resolve()
    send_cmd("tv_SaveDisplay", export_path.as_posix())


@try_cmd(exception_msg="No file found or invalid format")
def tv_save_image(export_path: Path | str) -> None:
    """Save the current image of the current layer."""
    export_path = Path(export_path)
    send_cmd("tv_SaveImage", export_path.as_posix())


@try_cmd(exception_msg="Invalid image format")
def tv_load_image(img_path: Path | str, stretch: bool | None = None) -> None:
    """Load an image in the current image layer."""
    img_path = Path(img_path)

    args: list[Any] = [img_path.as_posix()]
    if stretch is not None:
        args.append("stretch")

    send_cmd("tv_LoadImage", *args)


def tv_clip_save_structure_json(
    export_path: Path | str,
    file_format: SaveFormat,
    fill_background: bool | None = None,
    folder_pattern: str | None = None,
    file_pattern: str | None = None,
    visible_layers_only: bool | None = None,
    all_images: bool | None = None,
    ignore_duplicates: bool | None = None,
    exclude_instance_names: list[str] | None = None,
) -> None:
    """Save the current clip structure in json.

    Args:
        export_path: the JSON export path
        file_format: file format to use for rendering
        fill_background: add a background. Defaults to None.
        folder_pattern: the folder name pattern (%li: layer index, %ln: layer name, %fi: file index (added in 11.0.8)). Defaults to None.
        file_pattern: the file name pattern (%li: layer index, %ln: layer name, %ii: image index, %in: image name, %fi: file index (added in 11.0.8)). Defaults to None.
        visible_layers_only: export only visible layers. Defaults to None.
        all_images: export all images. Defaults to None.
        ignore_duplicates: Ignore duplicates images. Defaults to None.
        exclude_instance_names: the instances names which won't be processed/exported. Defaults to None.

    Raises:
        ValueError: the parent folder doesn't exist
    """
    export_path = Path(export_path).resolve()

    if not export_path.parent.exists():
        raise ValueError(
            "Can't write file because the destination folder doesn't exist"
        )

    args = [export_path.as_posix(), "JSON"]

    dict_args = {
        "fileformat": file_format.value,
        "background": int(fill_background) if fill_background else None,
        "patternfolder": folder_pattern,
        "patternfile": file_pattern,
        "onlyvisiblelayers": visible_layers_only,
        "allimages": int(all_images) if all_images else None,
        "ignoreduplicateimages": ignore_duplicates,
        "excludenames": (
            ";".join(exclude_instance_names) if exclude_instance_names else None
        ),
    }

    args_inline = args_dict_to_list(dict_args)

    send_cmd("tv_ClipSaveStructure", *args, *args_inline, error_values=[-1])


def tv_clip_save_structure_psd(
    export_path: Path | str,
    mode: PSDSaveMode,
    image: int | None = None,
    mark_in: int | None = None,
    mark_out: int | None = None,
) -> None:
    """Save the current clip as a PSD.

    Args:
        export_path: _description_
        mode: all will export all layers to a single PSD
        image: will only export the given image. Defaults to None.
        mark_in: start frame to render. Defaults to None.
        mark_out: end frame to render. Defaults to None.
    """
    export_path = Path(export_path)

    if not export_path.parent.exists():
        raise ValueError(
            "Can't write file because the destination folder doesn't exist"
        )

    args_dict: dict[str, str | int | None]

    if mode == PSDSaveMode.ALL:
        args_dict = {"mode": "all"}
    elif mode == PSDSaveMode.IMAGE:
        if image is None:
            raise ValueError("Image must be defined")
        args_dict = {"image": image}
    else:  # Markin
        if mark_in is None or mark_out is None:
            raise ValueError("mark_in and mark_out must be defined")
        args_dict = {"markin": mark_in, "markout": mark_out}

    args = args_dict_to_list(args_dict)

    send_cmd(
        "tv_ClipSaveStructure",
        export_path.as_posix(),
        "PSD",
        *args,
        error_values=[-1],
    )


def tv_clip_save_structure_csv(
    export_path: Path | str,
    all_images: bool | None = None,
    exposure_label: str | None = None,
) -> None:
    """Save the current clip as a CSV.

    Args:
        export_path: the .csv export path
        all_images: export all images or only instances. Defaults to None.
        exposure_label: give a label when the image is an exposure. Defaults to None.
    """
    export_path = Path(export_path)

    args = args_dict_to_list(
        {
            "allimages": int(bool(all_images)),
            "exposurelabel": exposure_label,
        }
    )

    send_cmd(
        "tv_ClipSaveStructure",
        export_path.as_posix(),
        "CSV",
        *args,
        error_values=[-1],
    )


def tv_clip_save_structure_sprite(
    export_path: Path | str,
    layout: SpriteLayout | None = None,
    space: int | None = None,
) -> None:
    """Save the current clip as sprites in one image.

    Args:
        export_path: the export path of the sprite image
        layout: the sprite layout. Defaults to None.
        space: the space between each sprite in the image. Defaults to None.
    """
    export_path = Path(export_path)

    args = args_dict_to_list(
        {
            "layout": layout.value if layout is not None else None,
            "space": space,
        }
    )

    send_cmd(
        "tv_clipsavestructure",
        export_path.as_posix(),
        "sprite",
        *args,
        error_values=[-1],
    )


def tv_clip_save_structure_flix(
    export_path: Path | str,
    mark_in: int | None = None,
    mark_out: int | None = None,
    parameters_import: str | None = None,
    parameters_file: str | None = None,
    send: bool | None = None,
    original_file: str | Path | None = None,
) -> None:
    """Save the current clip for Flix.

    Args:
        export_path: the .xml export path
        mark_in: the start frame to render. Defaults to None.
        mark_out: the end frame to render. Defaults to None.
        parameters_import: the attribute(s) of the global <flixImport> tag (waitForSource/...). Defaults to None.
        parameters_file: the attribute(s) of each <image> (file) tag (dialogue/...). Defaults to None.
        send: open a browser with the prefilled url. Defaults to None.
        original_file: the original reference tvpp file path. Defaults to None.
    """
    export_path = Path(export_path)

    args_dict = {
        "markin": mark_in,
        "markout": mark_out,
        "parametersimport": parameters_import,
        "parametersfile": parameters_file,
        "send": int(send) if send else None,
        "originalfile": Path(original_file).as_posix() if original_file else None,
    }

    args = args_dict_to_list(args_dict)

    send_cmd(
        "tv_clipsavestructure",
        export_path.as_posix(),
        "Flix",
        *args,
        error_values=[-1],
    )


def tv_sound_clip_info(clip_id: int, track_index: int) -> TVPSound:
    """Get information about a sound track."""
    res = send_cmd("tv_SoundClipInfo", clip_id, track_index, error_values=[-1, -2, -3])
    res_parse = tv_parse_list(res, with_fields=TVPSound)
    return TVPSound(**res_parse)


def tv_sound_clip_new(sound_path: Path | str) -> None:
    """Add a new sound track."""
    path = Path(sound_path)
    if not path.exists():
        raise ValueError(f"Sound file not found at : {path.as_posix()}")
    send_cmd("tv_SoundClipNew", path.as_posix(), error_values=[-1, -2, -3, -4])


def tv_sound_clip_remove(track_index: int) -> None:
    """Remove a sound track."""
    send_cmd("tv_SoundClipRemove", track_index, error_values=[-2])


def tv_sound_clip_reload(clip_id: int, track_index: int) -> None:
    """Reload a sound track from its file.

    TODO: check this: Also you can give any track_index you want and it returns 0

    Args:
        clip_id (int): the clip id
        track_index (int): the sound clip track index

    Warning:
        It doesn't accept a proper clip id and it works with a sound clip id...
    """
    send_cmd("tv_SoundClipReload", clip_id, track_index, error_values=[-1, -2, -3])


def tv_sound_clip_adjust(
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
    """Modify a sound track."""
    optional_args = [
        int(mute) if mute is not None else None,
        volume,
        offset,
        (fade_in_start, fade_in_stop, fade_out_start, fade_out_stop),
        color_index,
    ]

    args = consecutive_optional_args_to_list(optional_args)
    send_cmd("tv_SoundClipAdjust", track_index, *args, error_values=[-2, -3])


def tv_layer_image_get() -> int:
    """Get the current image in the current clip."""
    return int(send_cmd("tv_LayerGetImage"))


def tv_layer_image(frame: int) -> None:
    """Set the current image in the current clip."""
    send_cmd("tv_LayerImage", frame)
