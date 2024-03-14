"""Scene related George functions."""

from __future__ import annotations

from pytvpaint.george.client import send_cmd, try_cmd
from pytvpaint.george.grg_base import GrgErrorValue


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
