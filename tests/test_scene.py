import pytest
from pytvpaint import george
from pytvpaint import Clip
from pytvpaint.project import Project
from pytvpaint.scene import Scene


def test_scene_init(test_project_obj: Project, test_scene: int) -> None:
    scene = Scene(test_scene, test_project_obj)
    assert scene.id == test_scene
    assert scene.project == test_project_obj
    assert scene.position == 1  # It's the second scene


def test_scene_new_current_project(test_project_obj: Project) -> None:
    scene = Scene.new()
    # The scene's project is the current project
    assert scene.project == test_project_obj


def test_scene_new_other_project(test_project_obj: Project) -> None:
    scene = Scene.new(project=test_project_obj)
    # The scene's project is the given project
    assert scene.project == test_project_obj


def test_scene_current_scene_id_static(test_scene: int) -> None:
    assert Scene.current_scene_id() == test_scene


def test_scene_current_scene_static(test_scene_obj: Scene) -> None:
    assert Scene.current_scene() == test_scene_obj


def test_scene_is_current(test_project_obj: Project, test_scene_obj: Scene) -> None:
    assert test_scene_obj.is_current
    george.tv_scene_new()
    assert not test_scene_obj.is_current


def test_scene_make_current(test_scene_obj: Scene) -> None:
    george.tv_scene_new()

    # Because we created another scene which is current
    assert not test_scene_obj.is_current

    test_scene_obj.make_current()
    assert test_scene_obj.is_current


@pytest.mark.parametrize("pos", range(5))
def test_scene_position_getter(
    test_scene_obj: Scene,
    create_some_scenes: None,
    pos: int,
) -> None:
    george.tv_scene_move(test_scene_obj.id, pos)
    assert pos == test_scene_obj.position


@pytest.mark.parametrize("pos", range(5))
def test_scene_position_setter(
    test_scene_obj: Scene,
    create_some_scenes: None,
    pos: int,
) -> None:
    test_scene_obj.position = pos
    assert test_scene_obj.position == pos


def test_scene_clips(
    test_scene_obj: Scene,
    create_some_clips: list[Clip],
) -> None:
    assert list(Scene.current_scene().clips) == create_some_clips


def test_scene_duplicate(test_scene_obj: Scene) -> None:
    dup = test_scene_obj.duplicate()
    assert test_scene_obj != dup


def test_scene_remove(test_scene_obj: Scene) -> None:
    test_scene_obj.remove()

    with pytest.raises(ValueError, match="has been removed"):
        print(test_scene_obj.id)
