"""Scene related George functions."""

from __future__ import annotations

from pytvpaint.george.client import send_cmd, try_cmd
from pytvpaint.george.client.parse import tv_cast_to_type
from pytvpaint.george.grg_base import GrgErrorValue, min_version_compatible


@try_cmd(exception_msg="No scene at provided position")
def tv_scene_enum_id(position: int) -> int:
    """Get the id of the scene at the given position in the current project.

    Raises:
        GeorgeError: if no scene found at the provided position
    """
    return int(send_cmd("tv_SceneEnumId", position, error_values=[GrgErrorValue.NONE]))


def tv_scene_current_id() -> int:
    """Get the id of the current scene."""
    return int(send_cmd("tv_SceneCurrentId"))


def tv_scene_move(scene_id: int, position: int) -> None:
    """Move a scene to another position."""
    send_cmd("tv_SceneMove", scene_id, position)


def tv_scene_new() -> None:
    """Create a new scene (with a new clip) after the current scene."""
    send_cmd("tv_SceneNew")


def tv_scene_duplicate(scene_id: int) -> None:
    """Duplicate the given scene."""
    send_cmd("tv_SceneDuplicate", scene_id)


def tv_scene_close(scene_id: int) -> None:
    """Remove the given scene."""
    send_cmd("tv_SceneClose", scene_id)


@min_version_compatible(min_version="12")
def tv_scene_create(clips: list[str]) -> int:
    """Create a new scene (with a list of new clips provided) after the current scene.

    Args:
        clips: list of clip names to create alongside new scene

    Returns:
        scene_id: new scene id

    """
    return int(send_cmd("tv_SceneCreate", *clips))


@min_version_compatible(min_version="12")
def tv_scene_split(scene_id: int) -> list[int]:
    """Splits each clips in the scene into its own scene.

    Args:
        scene_id: scene if

    Returns:
        clip_ids: list of clip ids in the split scene

    """
    return tv_cast_to_type(send_cmd("tv_SceneSplit", scene_id), list[int])

