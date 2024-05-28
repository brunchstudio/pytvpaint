"""Layer related George functions and enums."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pytvpaint.george.client import send_cmd, try_cmd
from pytvpaint.george.client.parse import (
    args_dict_to_list,
    tv_cast_to_type,
    tv_parse_list,
)
from pytvpaint.george.exceptions import NoObjectWithIdError
from pytvpaint.george.grg_base import (
    BlendingMode,
    GrgErrorValue,
    RGBColor,
)


class LayerColorAction(Enum):
    """`tv_layercolor` actions.

    Attributes:
        GETCOLOR:
        SETCOLOR:
        GET:
        SET:
        LOCK:
        UNLOCK:
        SHOW:
        HIDE:
        VISIBLE:
        SELECT:
        UNSELECT:
    """

    GETCOLOR = "getcolor"
    SETCOLOR = "setcolor"
    GET = "get"
    SET = "set"
    LOCK = "lock"
    UNLOCK = "unlock"
    SHOW = "show"
    HIDE = "hide"
    VISIBLE = "visible"
    SELECT = "select"
    UNSELECT = "unselect"


class LayerColorDisplayOpt(Enum):
    """`tv_layercolorshow` display options.

    Attributes:
        DISPLAY: Activate the layers to show them in the display
        TIMELINE: Uncollpase layers from maximum collapse (2px height) in the timeline
    """

    DISPLAY = "display"
    TIMELINE = "timeline"


class InstanceNamingMode(Enum):
    """`tv_instancename` naming modes.

    Attributes:
        ALL:
        SMART:
    """

    ALL = "all"
    SMART = "smart"


class InstanceNamingProcess(Enum):
    """`tv_instancename` naming process.

    Attributes:
        EMPTY:
        NUMBER:
        TEXT:
    """

    EMPTY = "empty"
    NUMBER = "number"
    TEXT = "text"


class LayerType(Enum):
    """All the layer types.

    Attributes:
        IMAGE:
        SEQUENCE:
        XSHEET:
        SCRIBBLES:
    """

    IMAGE = "image"
    SEQUENCE = "sequence"
    XSHEET = "xsheet"
    SCRIBBLES = "scribbles"


class StencilMode(Enum):
    """All the stencil modes.

    Attributes:
        ON:
        OFF:
        NORMAL:
        INVERT:
    """

    ON = "on"
    OFF = "off"
    NORMAL = "normal"
    INVERT = "invert"


class LayerBehavior(Enum):
    """Layer behaviors on boundaries.

    Attributes:
        NONE:
        REPEAT:
        PINGPONG:
        HOLD:
    """

    NONE = "none"
    REPEAT = "repeat"
    PINGPONG = "pingpong"
    HOLD = "hold"


class LayerTransparency(Enum):
    """Layer transparency values.

    Attributes:
        ON:
        OFF:
        MINUS_1:
        NONE:
    """

    ON = "on"
    OFF = "off"
    MINUS_1 = "-1"
    NONE = "none"


class InsertDirection(Enum):
    """Instance insert direction.

    Attributes:
        BEFORE:
        AFTER:
    """

    BEFORE = "before"
    AFTER = "after"


@dataclass(frozen=True)
class TVPClipLayerColor:
    """Clip layer color values."""

    clip_id: int
    color_index: int
    color_r: int
    color_g: int
    color_b: int
    name: str


@dataclass(frozen=True)
class TVPLayer:
    """TVPaint layer info values."""

    id: int = field(metadata={"parsed": False})

    visibility: bool
    position: int
    density: int
    name: str
    type: LayerType
    first_frame: int
    last_frame: int
    selected: bool
    editable: bool
    stencil_state: StencilMode


def tv_layer_current_id() -> int:
    """Get the id of the current layer."""
    return int(send_cmd("tv_LayerCurrentId"))


@try_cmd(exception_msg="No layer at provided position")
def tv_layer_get_id(position: int) -> int:
    """Get the id of the layer at the given position.

    Raises:
        GeorgeError: if no layer found at the provided position
    """
    result = send_cmd("tv_LayerGetID", position, error_values=[GrgErrorValue.NONE])
    return int(result)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_get_pos(layer_id: int) -> int:
    """Get the position of the given layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    return int(send_cmd("tv_LayerGetPos", layer_id, error_values=[GrgErrorValue.NONE]))


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_info(layer_id: int) -> TVPLayer:
    """Get information of the given layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    result = send_cmd("tv_LayerInfo", layer_id, error_values=[GrgErrorValue.EMPTY])
    layer = tv_parse_list(result, with_fields=TVPLayer, unused_indices=[7, 8])
    layer["id"] = layer_id
    return TVPLayer(**layer)


@try_cmd(exception_msg="Couldn't move current layer to position")
def tv_layer_move(position: int) -> None:
    """Move the current layer to a new position in the layer stack.

    Raises:
        GeorgeError: if layer could not be moved
    """
    send_cmd("tv_LayerMove", position)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_set(layer_id: int) -> None:
    """Make the given layer the current one.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    send_cmd("tv_LayerSet", layer_id)


@try_cmd(raise_exc=NoObjectWithIdError, exception_msg="Invalid layer id")
def tv_layer_selection_get(layer_id: int) -> bool:
    """Get the selection state of a layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    res = send_cmd("tv_LayerSelection", layer_id, error_values=[-1])
    return tv_cast_to_type(res, bool)


@try_cmd(raise_exc=NoObjectWithIdError, exception_msg="Invalid layer id")
def tv_layer_selection_set(layer_id: int, new_state: bool) -> None:
    """Set the selection state of a layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    send_cmd("tv_LayerSelection", layer_id, int(new_state), error_values=[-1])


def tv_layer_select(start_frame: int, frame_count: int) -> int:
    """Select frames in the current layer.

    Args:
        start_frame: selection start
        frame_count: number of frames to select

    Returns:
        int: number of frames selected

    Note:
        If the start position is before the beginning of the layer, the selection will only start at the beginning of
        the layer, but its length will be measured from the start position.
        This means that if you ask for a selection of 15 frames starting from position 0 in a layer that actually
        starts at position 5, only the first 10 frames in the layer will be selected.
        If the selection goes beyond the end of the layer, it will only include the frames between the start and end of
        the layer. No frames will be selected if the start position is beyond the end of the layer
    """
    return int(send_cmd("tv_LayerSelect", start_frame, frame_count, error_values=[-1]))


def tv_layer_select_info(full: bool = False) -> tuple[int, int]:
    """Get Selected frames in a layer.

    Args:
        full:  Always get the selection range, even on a non anim/ctg layer

    Returns:
        frame: the start frame of the selection
        count: the number of frames in the selection

    Bug:
        The official documentation states that this functions selects the layer frames, it does not, it simply
        returns the frames selected. This will also return all frames in the layer even if they are not selected if the
        argument `full` is set to True. We advise using `tv_layer_select` to select your frames and only using this
        function to get the selected frames.
    """
    args = ["full"] if full else []
    res = send_cmd("tv_layerSelectInfo", *args)
    frame, count = tuple(map(int, res.split(" ")))
    return frame, count


def tv_layer_create(name: str) -> int:
    """Create a new image layer with the given name."""
    return int(send_cmd("tv_LayerCreate", name, handle_string=False))


def tv_layer_duplicate(name: str) -> int:
    """Duplicate the current layer and make it the current one."""
    return int(send_cmd("tv_LayerDuplicate", name, handle_string=False))


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_rename(layer_id: int, name: str) -> None:
    """Rename a layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    send_cmd("tv_LayerRename", layer_id, name)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_kill(layer_id: int) -> None:
    """Delete the layer with provided id.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    send_cmd("tv_LayerKill", layer_id)


def tv_layer_density_get() -> int:
    """Get the current layer density (opacity)."""
    return int(send_cmd("tv_LayerDensity"))


def tv_layer_density_set(new_density: int) -> None:
    """Set the current layer density (opacity ranging from 0 to 100)."""
    send_cmd("tv_LayerDensity", new_density)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_display_get(layer_id: int) -> bool:
    """Get the visibility of the given layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    res = send_cmd("tv_LayerDisplay", layer_id, error_values=[0])
    return tv_cast_to_type(res.lower(), bool)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_display_set(
    layer_id: int, new_state: bool, light_table: bool = False
) -> None:
    """Set the visibility of the given layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    args: list[Any] = [layer_id, int(new_state)]
    if light_table:
        args.insert(1, "lighttable")
    send_cmd("tv_LayerDisplay", *args, error_values=[0])


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_lock_get(layer_id: int) -> bool:
    """Get the lock state of the given layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    res = send_cmd("tv_LayerLock", layer_id, error_values=[GrgErrorValue.ERROR])
    return tv_cast_to_type(res.lower(), bool)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_lock_set(layer_id: int, new_state: bool) -> None:
    """Set the lock state of the given layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    send_cmd(
        "tv_LayerLock",
        layer_id,
        int(new_state),
        error_values=[GrgErrorValue.ERROR],
    )


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_collapse_get(layer_id: int) -> bool:
    """Get the collapse mode of the given layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    return bool(int(send_cmd("tv_LayerCollapse", layer_id, error_values=[-2])))


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_collapse_set(layer_id: int, new_state: bool) -> None:
    """Set the collapse mode of the given layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    send_cmd("tv_LayerCollapse", layer_id, int(new_state), error_values=[-2])


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_blending_mode_get(layer_id: int) -> BlendingMode:
    """Get the blending mode of the given layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    res = send_cmd("tv_LayerBlendingMode", layer_id)
    return tv_cast_to_type(res.lower(), BlendingMode)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_blending_mode_set(layer_id: int, mode: BlendingMode) -> None:
    """Set the blending mode of the given layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    send_cmd("tv_LayerBlendingMode", layer_id, mode.value)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_stencil_get(layer_id: int) -> StencilMode:
    """Get the stencil state and mode of the given layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    res = send_cmd("tv_LayerStencil", layer_id)
    _, state, mode = res.split(" ")

    if state == "off":
        return StencilMode.OFF

    return tv_cast_to_type(mode, StencilMode)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_stencil_set(layer_id: int, mode: StencilMode) -> None:
    """Set the stencil state and mode of the given layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    if mode == StencilMode.OFF:
        args = ["off"]
    elif mode == StencilMode.ON:
        args = ["on"]
    else:
        args = ["on", mode.value]

    send_cmd("tv_LayerStencil", layer_id, *args)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_show_thumbnails_get(
    layer_id: int,
) -> bool:
    """Get the show thumbnails state for a layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    res = send_cmd(
        "tv_LayerShowThumbnails", layer_id, error_values=[GrgErrorValue.ERROR]
    )
    return res == "1"


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_show_thumbnails_set(
    layer_id: int,
    state: bool,
) -> None:
    """Set the show thumbnail state for a layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    send_cmd(
        "tv_LayerShowThumbnails",
        layer_id,
        int(state),
        error_values=[GrgErrorValue.ERROR],
    )


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_auto_break_instance_get(layer_id: int) -> bool:
    """Get the layer auto break instance value for a layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    res = send_cmd("tv_LayerAutoBreakInstance", layer_id, error_values=[-1, -2, -3])
    return res == "1"


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_auto_break_instance_set(
    layer_id: int,
    state: bool,
) -> None:
    """Set the layer auto break instance value for a layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    send_cmd(
        "tv_LayerAutoBreakInstance",
        layer_id,
        int(state),
        error_values=[-1, -2, -3],
    )


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_auto_create_instance_get(
    layer_id: int,
) -> bool:
    """Get the layer auto create instance value for a layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    res = send_cmd("tv_LayerAutoCreateInstance", layer_id, error_values=[-1, -2, -3])
    return res == "1"


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_auto_create_instance_set(
    layer_id: int,
    state: bool,
) -> None:
    """Set the layer auto create instance value for a layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    send_cmd(
        "tv_LayerAutoCreateInstance", layer_id, int(state), error_values=[-1, -2, -3]
    )


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_pre_behavior_get(layer_id: int) -> LayerBehavior:
    """Get the pre-behavior value for a layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    res = send_cmd("tv_LayerPreBehavior", layer_id)
    return tv_cast_to_type(res, LayerBehavior)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_pre_behavior_set(layer_id: int, behavior: LayerBehavior) -> None:
    """Set the pre-behavior value for a layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    send_cmd("tv_LayerPreBehavior", layer_id, behavior.value)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_post_behavior_get(layer_id: int) -> LayerBehavior:
    """Get the post-behavior value for a layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    res = send_cmd("tv_LayerPostBehavior", layer_id)
    return tv_cast_to_type(res, LayerBehavior)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_post_behavior_set(layer_id: int, behavior: LayerBehavior) -> None:
    """Set the post-behavior value for a layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    send_cmd("tv_LayerPostBehavior", layer_id, behavior.value)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_lock_position_get(layer_id: int) -> bool:
    """Get the lock position state of a layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    res = send_cmd("tv_LayerLockPosition", layer_id)
    return tv_cast_to_type(res, bool)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_lock_position_set(layer_id: int, state: bool) -> None:
    """Set the lock position state of a layer.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    send_cmd("tv_LayerLockPosition", layer_id, int(state))


def tv_preserve_get() -> LayerTransparency:
    """Get the preserve transparency state of the current layer."""
    res = send_cmd("tv_Preserve")
    _, state = res.split(" ")
    return tv_cast_to_type(state, LayerTransparency)


def tv_preserve_set(state: LayerTransparency) -> None:
    """Set the preserve transparency state of the current layer."""
    send_cmd("tv_Preserve", "alpha", state.value)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_mark_get(layer_id: int, frame: int) -> int:
    """Get the mark color of a layer at a frame.

    Args:
        layer_id: the layer id
        frame: the frame with a mark

    Raises:
        NoObjectWithIdError: if given an invalid layer id

    Returns:
        int: the mark color index
    """
    return int(send_cmd("tv_LayerMarkGet", layer_id, frame))


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_mark_set(layer_id: int, frame: int, color_index: int) -> None:
    """Set the mark of the layer's frame.

    Args:
        layer_id: the layer id
        frame: the frame to set the mark (use 0 to remove it).
        color_index: the mark color

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    send_cmd("tv_LayerMarkSet", layer_id, frame, color_index)


def tv_layer_anim(layer_id: int) -> None:
    """Convert the layer to an anim layer."""
    send_cmd("tv_LayerAnim", *([layer_id] if layer_id else []))


def tv_layer_copy() -> None:
    """Copy the current image or the selected ones."""
    send_cmd("tv_LayerCopy")


def tv_layer_cut() -> None:
    """Cut the current image or the selected ones."""
    send_cmd("tv_LayerCut")


def tv_layer_paste() -> None:
    """Paste the previously copied/cut images to the current layer."""
    send_cmd("tv_LayerPaste")


def tv_layer_insert_image(
    count: int = 1,
    direction: InsertDirection | None = None,
    duplicate: bool | None = None,
) -> None:
    """Add new image(s) before/after the current one and make it current."""
    if duplicate:
        args = [0]
    else:
        args_dict = {
            "count": count,
            "direction": direction.value if direction is not None else None,
        }
        args = args_dict_to_list(args_dict)

    send_cmd("tv_LayerInsertImage", *args)


def tv_layer_merge(
    layer_id: int,
    blending_mode: BlendingMode,
    stamp: bool = False,
    erase: bool = False,
    keep_color_grp: bool = True,
    keep_img_mark: bool = True,
    keep_instance_name: bool = True,
) -> None:
    """Merge the given layer with the current one.

    Args:
        layer_id: the layer id
        blending_mode: the blending mode to use
        stamp: Use stamp mode
        erase: Remove the source layer
        keep_color_grp: Keep the color group
        keep_img_mark: Keep the image mark
        keep_instance_name: Keep the instance name
    """
    args = [
        layer_id,
        blending_mode.value,
    ]

    if stamp:
        args.append("stamp")
    if erase:
        args.append("erase")

    args_dict = {
        "keepcolorgroup": int(keep_color_grp),
        "keepimagemark": int(keep_img_mark),
        "keepinstancename": int(keep_instance_name),
    }
    args.extend(args_dict_to_list(args_dict))

    send_cmd("tv_LayerMerge", layer_id, *args)


def tv_layer_merge_all(
    keep_color_grp: bool = True,
    keep_img_mark: bool = True,
    keep_instance_name: bool = True,
) -> None:
    """Merge all layers.

    Args:
        keep_color_grp: Keep the color group
        keep_img_mark: Keep the image mark
        keep_instance_name: Keep the instance name
    """
    args_dict = {
        "keepcolorgroup": int(keep_color_grp),
        "keepimagemark": int(keep_img_mark),
        "keepinstancename": int(keep_instance_name),
    }
    send_cmd("tv_LayerMergeAll", *args_dict_to_list(args_dict))


def tv_layer_shift(layer_id: int, start: int) -> None:
    """Move the layer to a new frame.

    Args:
        layer_id: layer id
        start: frame to shift layer to
    """
    send_cmd("tv_LayerShift", layer_id, start)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_load_dependencies(layer_id: int) -> None:
    """Load all dependencies of the given layer in memory.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    send_cmd("tv_LayerLoadDependencies", layer_id)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_color_get_color(clip_id: int, color_index: int) -> TVPClipLayerColor:
    """Get a specific colors information in the clips color list.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    result = send_cmd(
        "tv_LayerColor",
        LayerColorAction.GETCOLOR.value,
        clip_id,
        color_index,
        error_values=[GrgErrorValue.ERROR],
    )
    parsed = tv_parse_list(result, with_fields=TVPClipLayerColor)
    return TVPClipLayerColor(**parsed)


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_color_set_color(
    clip_id: int,
    color_index: int,
    color: RGBColor,
    name: str | None = None,
) -> None:
    """Set a specific colors information in the clips color list.

    Raises:
        NoObjectWithIdError: if given an invalid layer id

    Note:
        The color with index 0 is the "Default" color, and it can't be changed
    """
    args: list[Any] = [
        LayerColorAction.SETCOLOR.value,
        clip_id,
        color_index,
        color.r,
        color.g,
        color.b,
    ]

    if name:
        args.append(name)

    send_cmd("tv_LayerColor", *args, error_values=[GrgErrorValue.ERROR])


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_color_get(layer_id: int) -> int:
    """Get the layer's color index from the clips color list.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    res = send_cmd(
        "tv_LayerColor",
        LayerColorAction.GET.value,
        layer_id,
        error_values=[-1],
    )
    return int(res)


@try_cmd(raise_exc=NoObjectWithIdError)
def tv_layer_color_set(layer_id: int, color_index: int) -> None:
    """Set the layer's color index from the clips color list.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    send_cmd(
        "tv_LayerColor",
        LayerColorAction.SET.value,
        layer_id,
        color_index,
        error_values=[-1],
    )


def tv_layer_color_lock(color_index: int) -> int:
    """Lock all layers that use the given color index.

    Args:
        color_index: the layer color index

    Returns:
        the number of layers locked
    """
    return int(send_cmd("tv_LayerColor", LayerColorAction.LOCK.value, color_index))


def tv_layer_color_unlock(color_index: int) -> int:
    """Unlock all layers that use the given color index.

    Args:
        color_index: the layer color index

    Returns:
        the number of unlocked layers
    """
    return int(send_cmd("tv_LayerColor", LayerColorAction.UNLOCK.value, color_index))


def tv_layer_color_show(mode: LayerColorDisplayOpt, color_index: int) -> int:
    """Show all layers that use the given color index.

    Args:
        mode: the display mode
        color_index: the layer color index

    Returns:
        the number of unlocked layers
    """
    res = send_cmd(
        "tv_LayerColor",
        LayerColorAction.SHOW.value,
        mode.value,
        color_index,
        error_values=[GrgErrorValue.ERROR],
    )
    return int(res)


def tv_layer_color_hide(mode: LayerColorDisplayOpt, color_index: int) -> int:
    """Hide all layers that use the given color index.

    Args:
        mode: the display mode
        color_index: the layer color index

    Returns:
        the number of unlocked layers
    """
    return int(
        send_cmd(
            "tv_LayerColor",
            LayerColorAction.HIDE.value,
            mode.value,
            color_index,
            error_values=[GrgErrorValue.ERROR],
        )
    )


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id",
)
def tv_layer_color_visible(color_index: int) -> bool:
    """Get the visibility of the color index (2px height) in the timeline.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    return bool(
        send_cmd(
            "tv_LayerColor",
            LayerColorAction.VISIBLE.value,
            color_index,
            error_values=[-1],
        )
    )


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid color index",
)
def tv_layer_color_select(color_index: int) -> int:
    """Select all layers that use the given color index.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    return int(send_cmd("tv_LayerColor", LayerColorAction.SELECT.value, color_index))


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid color index",
)
def tv_layer_color_unselect(color_index: int) -> int:
    """Unselect all layers that use the given color index.

    Raises:
        NoObjectWithIdError: if given an invalid layer id
    """
    return int(send_cmd("tv_LayerColor", LayerColorAction.UNSELECT.value, color_index))


def tv_instance_name(
    layer_id: int,
    mode: InstanceNamingMode,
    prefix: str | None = None,
    suffix: str | None = None,
    process: InstanceNamingProcess | None = None,
) -> None:
    """Rename all instances.

    Note:
        The suffix can only be added when using mode InstanceNamingMode.SMART

    Bug:
        Using a wrong layer_id causes a crash

    Args:
        layer_id: the layer id
        mode: the instance renaming mode
        prefix: the prefix to add to each name
        suffix: the suffix to add to each name
        process: the instance naming process
    """
    args_dict: dict[str, Any] = {
        "mode": mode.value,
        "prefix": prefix,
    }

    if mode == InstanceNamingMode.SMART:
        args_dict["suffix"] = suffix
        args_dict["process"] = process.value if process else None

    args = args_dict_to_list(args_dict)
    send_cmd("tv_InstanceName", layer_id, *args, error_values=[-1, -2])


@try_cmd(
    raise_exc=NoObjectWithIdError,
    exception_msg="Invalid layer id or the frame doesn't have an instance",
)
def tv_instance_get_name(layer_id: int, frame: int) -> str:
    """Get the name of an instance.

    Args:
        layer_id: the layer id
        frame: the frame of the instance

    Raises:
        NoObjectWithIdError: if given an invalid layer id or an invalid instance frame

    Returns:
        the instance name
    """
    return send_cmd("tv_InstanceGetName", layer_id, frame).strip('"')


@try_cmd(exception_msg="Invalid layer id or no instance at given frame")
def tv_instance_set_name(layer_id: int, frame: int, name: str) -> str:
    """Set the name of an instance.

    Raises:
        GeorgeError: if an invalid layer id was provided or no instance was found at the given frame
    """
    return send_cmd("tv_InstanceSetName", layer_id, frame, name)


def tv_exposure_next() -> int:
    """Go to the next layer instance head.

    Returns:
        The next instances start frame
    """
    return int(send_cmd("tv_ExposureNext"))


def tv_exposure_break(frame: int) -> None:
    """Break a layer instance/exposure at the given frame.

    Args:
        frame: the split frame
    """
    send_cmd("tv_ExposureBreak", frame)


def tv_exposure_add(frame: int, count: int) -> None:
    """Add new frames to an existing layer instance/exposure.

    Args:
        frame: the split frame
        count: the number of frames to add
    """
    send_cmd("tv_ExposureAdd", frame, count)


def tv_exposure_set(frame: int, count: int) -> None:
    """Set the number frames of an existing layer instance/exposure.

    Args:
        frame: the split frame
        count: the number of frames to add
    """
    send_cmd("tv_ExposureSet", frame, count)


def tv_exposure_prev() -> int:
    """Go to the previous layer instance head (*before* the current instance).

    Returns:
        The previous instances start frame
    """
    return int(send_cmd("tv_ExposurePrev"))


@try_cmd(exception_msg="No file found or invalid format")
def tv_save_image(export_path: Path | str) -> None:
    """Save the current image of the current layer.

    Raises:
        GeorgeError: if the file couldn't be saved or an invalid format was provided
    """
    export_path = Path(export_path)
    send_cmd("tv_SaveImage", export_path.as_posix())


@try_cmd(exception_msg="Invalid image format")
def tv_load_image(img_path: Path | str, stretch: bool = False) -> None:
    """Load an image in the current image layer.

    Raises:
        FileNotFoundError: if the input file doesn't exist
        GeorgeError: if the provided file is in an invalid format
    """
    img_path = Path(img_path)

    if not img_path.exists():
        raise FileNotFoundError(f"File not found at: {img_path.as_posix()}")

    args: list[Any] = [img_path.as_posix()]
    if stretch:
        args.append("stretch")

    send_cmd("tv_LoadImage", *args)


def tv_clear(fill_b_pen: bool = False) -> None:
    """Clear (or fill with BPen) the current image (selection) of the current layer."""
    send_cmd("tv_Clear", int(fill_b_pen))
