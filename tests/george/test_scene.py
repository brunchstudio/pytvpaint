from __future__ import annotations

from typing import Iterator

import pytest
from pytvpaint.george.exceptions import GeorgeError
from pytvpaint.george.project import TVPProject
from pytvpaint.george.scene import (
    tv_scene_close,
    tv_scene_current_id,
    tv_scene_duplicate,
    tv_scene_enum_id,
    tv_scene_move,
    tv_scene_new,
)

from tests.conftest import test_project


def test_tv_scene_enum_id(test_project: TVPProject) -> None:
    assert tv_scene_enum_id(0)


@pytest.mark.parametrize("pos", [-1, 10])
def test_tv_scene_enum_id_wrong_pos(pos: int) -> None:
    with pytest.raises(GeorgeError):
        tv_scene_enum_id(-1)


def test_tv_scene_current_id(test_project: TVPProject) -> None:
    assert tv_scene_current_id()


def create_new_scene() -> int:
    """Creates a new scene and return its id"""
    tv_scene_new()
    return tv_scene_current_id()


@pytest.mark.parametrize("pos", range(5))
def test_tv_scene_move(test_project: TVPProject, test_scene: int, pos: int) -> None:
    for _ in range(5):
        create_new_scene()
    tv_scene_move(test_scene, pos)
    assert tv_scene_enum_id(pos) == test_scene


def test_tv_scene_new(test_project: TVPProject) -> None:
    previous = tv_scene_current_id()
    tv_scene_new()
    assert tv_scene_current_id() != previous


def scenes_iterate() -> Iterator[tuple[int, int]]:
    pos = 0
    while True:
        try:
            yield pos, tv_scene_enum_id(pos)
        except GeorgeError:
            break
        pos += 1


def get_scene_ids() -> Iterator[int]:
    for _, scene_id in scenes_iterate():
        yield scene_id


def get_scene_pos(scene_id: int) -> int:
    for pos, other_id in scenes_iterate():
        if other_id == scene_id:
            return pos
    raise Exception("Scene doesn't exist")


other_project = test_project


def test_tv_scene_duplicate(
    test_project: TVPProject,
    test_scene: int,
) -> None:
    # Create another scene to test the behavior
    tv_scene_new()

    scenes_before = list(get_scene_ids())
    test_scene_pos = get_scene_pos(test_scene)

    # Duplicate the scene
    tv_scene_duplicate(test_scene)
    dup_scene_pos = test_scene_pos + 1
    dup_scene = tv_scene_enum_id(dup_scene_pos)

    # The duplicated scene is inserted after the test scene
    scenes_after = scenes_before
    scenes_after.insert(dup_scene_pos, dup_scene)

    assert list(get_scene_ids()) == scenes_after


def test_tv_scene_close(test_project: TVPProject, test_scene: int) -> None:
    scenes_before = list(get_scene_ids())
    tv_scene_close(test_scene)

    scenes_before.remove(test_scene)
    assert list(get_scene_ids()) == scenes_before
