from __future__ import annotations

from collections.abc import Iterator

import pytest

from pytvpaint import george
from tests.conftest import test_project

IS_TVP12 = george.tv_version()[1].startswith("12")


def test_tv_scene_enum_id(test_project: george.TVPProject) -> None:
    assert george.tv_scene_enum_id(0)


@pytest.mark.parametrize("pos", [-1, 10])
def test_tv_scene_enum_id_wrong_pos(pos: int) -> None:
    with pytest.raises(george.GeorgeError):
        george.tv_scene_enum_id(-1)


def test_tv_scene_current_id(test_project: george.TVPProject) -> None:
    assert george.tv_scene_current_id()


def create_new_scene() -> int:
    """Creates a new scene and return its id"""
    george.tv_scene_new()
    return george.tv_scene_current_id()


# @pytest.mark.skipif(IS_TVP12, reason="Skip since new scene ops crash tvpaint if a project is closed afterwards.")
@pytest.mark.parametrize("pos", range(5))
def test_tv_scene_move(test_project: george.TVPProject, test_scene: int, pos: int) -> None:
    for _ in range(5):
        create_new_scene()
    george.tv_scene_move(test_scene, pos)
    assert george.tv_scene_enum_id(pos) == test_scene


# @pytest.mark.skipif(IS_TVP12, reason="Skip since new scene ops crash tvpaint if a project is closed afterwards.")
def test_tv_scene_new(test_project: george.TVPProject) -> None:
    previous = george.tv_scene_current_id()
    george.tv_scene_new()
    assert george.tv_scene_current_id() != previous


def scenes_iterate() -> Iterator[tuple[int, int]]:
    pos = 0
    while True:
        try:
            yield pos, george.tv_scene_enum_id(pos)
        except george.GeorgeError:
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


@pytest.mark.skipif(IS_TVP12, reason="Skip since new scene ops crash tvpaint if a project is closed afterwards.")
def test_tv_scene_duplicate(
    test_project: george.TVPProject,
    test_scene: int,
) -> None:
    # Create another scene to test the behavior
    george.tv_scene_new()

    scenes_before = list(get_scene_ids())
    test_scene_pos = get_scene_pos(test_scene)

    # Duplicate the scene
    george.tv_scene_duplicate(test_scene)
    dup_scene_pos = test_scene_pos + 1
    dup_scene = george.tv_scene_enum_id(dup_scene_pos)

    # The duplicated scene is inserted after the test scene
    scenes_after = scenes_before
    scenes_after.insert(dup_scene_pos, dup_scene)

    assert list(get_scene_ids()) == scenes_after


def test_tv_scene_close(test_project: george.TVPProject, test_scene: int) -> None:
    scenes_before = list(get_scene_ids())
    george.tv_scene_close(test_scene)

    scenes_before.remove(test_scene)
    assert list(get_scene_ids()) == scenes_before
