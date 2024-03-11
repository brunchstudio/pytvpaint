from pathlib import Path

import pytest

from pytvpaint import george
from pytvpaint.clip import Clip
from pytvpaint.george.grg_project import TVPProject
from pytvpaint.project import Project
from pytvpaint.scene import Scene
from pytvpaint.sound import ProjectSound
from tests.conftest import FixtureYield


def test_project_init(test_project: TVPProject) -> None:
    project = Project(test_project.id)
    assert project.id == test_project.id


def test_project_refresh(test_project_obj: Project) -> None:
    test_project_obj.refresh()


def test_project_position(test_project_obj: Project) -> None:
    pos = test_project_obj.position
    assert george.tv_project_enum_id(pos) == test_project_obj.id


def test_project_closed(test_project_obj: Project) -> None:
    assert not test_project_obj.is_closed
    george.tv_project_close(test_project_obj.id)
    assert test_project_obj.is_closed


def test_project_exists_on_disk(test_project_obj: Project) -> None:
    assert not test_project_obj.exists
    george.tv_save_project(test_project_obj.path)
    assert test_project_obj.exists


@pytest.fixture()
def other_project(tmp_path: Path) -> FixtureYield[None]:
    other_project = george.tv_project_new(
        tmp_path / "other.tvpp", width=1234, height=567
    )
    yield
    george.tv_project_close(other_project)


def test_project_is_current(test_project_obj: Project, other_project: None) -> None:
    assert not test_project_obj.is_current
    george.tv_project_select(test_project_obj.id)
    assert test_project_obj.is_current


def test_project_make_current(test_project_obj: Project, other_project: None) -> None:
    test_project_obj.make_current()
    assert test_project_obj.is_current


def test_project_path(test_project_obj: Project, tmp_path: Path) -> None:
    new_path = tmp_path / "new_location.tvpp"
    george.tv_save_project(new_path)
    assert test_project_obj.path == new_path


def test_project_name(test_project_obj: Project, tmp_path: Path) -> None:
    new_path = tmp_path / "new_location.tvpp"
    george.tv_save_project(new_path)
    assert test_project_obj.name == new_path.stem


def test_project_width_height(test_project_obj: Project, other_project: None) -> None:
    assert test_project_obj.width == 1920
    assert test_project_obj.height == 1080


def test_project_resize_same_width_and_height(test_project_obj: Project) -> None:
    resized = test_project_obj.resize(test_project_obj.width, test_project_obj.height)
    assert resized == test_project_obj


def test_project_resize(
    test_project_obj: Project, cleanup_current_project: None
) -> None:
    resized = test_project_obj.resize(100, 200)

    # The resized project is a new project
    assert resized != test_project_obj

    assert resized.width == 100
    assert resized.height == 200

    # It closes the project but it still exists on disk
    assert test_project_obj.is_closed


def test_project_resize_overwrite(
    test_project_obj: Project, cleanup_current_project: None
) -> None:
    origin_path = test_project_obj.path

    resized = test_project_obj.resize(100, 200, overwrite=True)
    resized.close()

    # Verify that the original file is overwritten
    resized_load = Project.load(origin_path)
    assert resized == resized_load
    assert resized.width == resized_load.width
    assert resized.height == resized_load.height


def test_project_fps(test_project_obj: Project) -> None:
    test_project_obj.set_fps(54)
    assert test_project_obj.fps == 54


def test_project_fps_preview(test_project_obj: Project) -> None:
    test_project_obj.set_fps(54, preview=True)
    assert test_project_obj.playback_fps == 54


@pytest.mark.parametrize("field_order", george.FieldOrder)
def test_project_field_order(
    tmp_path: Path,
    field_order: george.FieldOrder,
    cleanup_current_project: None,
) -> None:
    proj = Project.new(tmp_path, field_order=field_order)
    assert proj.field_order == field_order


@pytest.mark.parametrize("aspect_ratio", [0.5, 1, 4])
def test_project_pixel_aspect_ratio(
    tmp_path: Path,
    aspect_ratio: float,
    cleanup_current_project: None,
) -> None:
    proj = Project.new(tmp_path, pixel_aspect_ratio=aspect_ratio)
    assert proj.pixel_aspect_ratio == aspect_ratio


@pytest.mark.parametrize("start_frame", [1, 2, 10, 100])
def test_project_start_frame(test_project_obj: Project, start_frame: int) -> None:
    test_project_obj.start_frame = start_frame
    assert test_project_obj.start_frame == start_frame


@pytest.mark.parametrize("mark_in", [1, 2, 10, 100])
@pytest.mark.parametrize("current_frame", [0, 1, 5, 50])
@pytest.mark.parametrize("start_frame", [2, 5, 20])
def test_project_current_frame(
    test_project_obj: Project, mark_in: int, current_frame: int, start_frame: int
) -> None:
    test_project_obj.start_frame = start_frame
    test_project_obj.current_clip.mark_in = mark_in
    test_project_obj.current_frame = current_frame

    assert test_project_obj.current_frame == current_frame


@pytest.mark.parametrize("header", ["", "Hello", "THis is a project header"])
def test_project_header_info(test_project_obj: Project, header: str) -> None:
    test_project_obj.header_info = header
    assert test_project_obj.header_info == header


@pytest.mark.parametrize("author", ["a", "Hello", "THis is a project author"])
def test_project_author(test_project_obj: Project, author: str) -> None:
    test_project_obj.author = author
    assert test_project_obj.author == author


@pytest.mark.parametrize("notes", ["a", "Hello", "THis is a project notes"])
def test_project_notes(test_project_obj: Project, notes: str) -> None:
    test_project_obj.notes = notes
    assert test_project_obj.notes == notes


def test_project_get_project(test_project_obj: Project) -> None:
    assert Project.get_project(by_id=test_project_obj.id) == test_project_obj
    assert Project.get_project(by_name=test_project_obj.name) == test_project_obj


def test_project_get_project_wrong_id(test_project_obj: Project) -> None:
    with pytest.raises(ValueError, match="Can't find a project"):
        Project.get_project(by_id="unknown")


def test_project_get_project_wrong_name(test_project_obj: Project) -> None:
    with pytest.raises(ValueError, match="Can't find a project"):
        Project.get_project(by_name="name")


def test_project_current_scene_ids(
    test_project_obj: Project,
    create_some_scenes: list[Scene],
) -> None:
    ids = list(test_project_obj.current_scene_ids())
    assert ids == [s.id for s in create_some_scenes]


def test_project_current_scene(
    test_project_obj: Project, test_scene_obj: Scene
) -> None:
    assert test_project_obj.current_scene == test_scene_obj


def test_project_scenes(
    test_project_obj: Project,
    create_some_scenes: list[Scene],
) -> None:
    assert list(test_project_obj.scenes) == create_some_scenes


def test_project_get_scene(test_project_obj: Project, test_scene_obj: Scene) -> None:
    test_project_obj.get_scene(by_id=test_scene_obj.id)


def test_project_add_scene(test_project_obj: Project) -> None:
    scene = test_project_obj.add_scene()
    assert test_project_obj.current_scene == scene


@pytest.mark.parametrize("index", range(5))
def test_project_current_clip(
    test_project_obj: Project, create_some_clips: list[Clip], index: int
) -> None:
    clip = create_some_clips[index]
    clip.make_current()
    assert test_project_obj.current_clip == clip


def test_project_clips(
    test_project_obj: Project, create_some_clips: list[Clip]
) -> None:
    clips = [clip for scene in test_project_obj.scenes for clip in scene.clips]
    assert list(test_project_obj.clips) == clips


def test_project_get_clip_by_id(test_project_obj: Project, test_clip_obj: Clip) -> None:
    assert test_project_obj.get_clip(by_id=test_clip_obj.id) == test_clip_obj


def test_project_get_clip_by_name(
    test_project_obj: Project,
    test_clip_obj: Clip,
) -> None:
    assert test_project_obj.get_clip(by_name=test_clip_obj.name) == test_clip_obj


def test_project_get_clip_by_id_scene_id(
    test_project_obj: Project,
    test_scene_obj: Scene,
    test_clip_obj: Clip,
) -> None:
    clip = test_project_obj.get_clip(
        by_id=test_clip_obj.id,
        scene_id=test_scene_obj.id,
    )
    assert clip == test_clip_obj


@pytest.mark.parametrize("name", ["l", "hello", "this is my clip"])
def test_project_add_clip(
    test_project_obj: Project, test_scene_obj: Scene, name: str
) -> None:
    clip = test_project_obj.add_clip(name, test_scene_obj)
    assert clip.scene == test_scene_obj
    assert clip.name == name


@pytest.mark.parametrize("name", ["l", "hello", "this is my clip"])
def test_project_add_clip_current_scene(test_project_obj: Project, name: str) -> None:
    clip = test_project_obj.add_clip(name, scene=None)
    assert clip.scene == test_project_obj.current_scene
    assert clip.name == name


def test_project_sounds(
    test_project_obj: Project,
    create_some_project_sounds: list[ProjectSound],
) -> None:
    assert list(test_project_obj.sounds) == create_some_project_sounds


def test_project_add_sound(test_project_obj: Project, wav_file: Path) -> None:
    test_project_obj.add_sound(wav_file)


def test_project_current_project_id(test_project_obj: Project) -> None:
    assert Project.current_project_id() == test_project_obj.id


def test_project_current_project(test_project_obj: Project) -> None:
    assert Project.current_project() == test_project_obj


def test_project_opened_project_ids(create_some_projects: list[Project]) -> None:
    expected_ids = [p.id for p in create_some_projects]
    assert expected_ids == list(Project.open_projects_ids())


def test_project_opened_projects(create_some_projects: list[Project]) -> None:
    assert create_some_projects == list(Project.open_projects())


@pytest.mark.parametrize("mark_in", [1, 2, 10, 100])
def test_project_mark_in(test_project_obj: Project, mark_in: int) -> None:
    test_project_obj.mark_in = mark_in
    assert test_project_obj.mark_in == mark_in


@pytest.mark.parametrize("mark_out", [1, 2, 10, 100])
def test_project_mark_out(test_project_obj: Project, mark_out: int) -> None:
    test_project_obj.mark_in = mark_out
    assert test_project_obj.mark_in == mark_out


def test_project_new(tmp_path: Path, cleanup_current_project: None) -> None:
    proj = Project.new(tmp_path / "project.tvpp")
    assert Project.current_project() == proj


def test_project_new_from_camera(test_project_obj: Project) -> None:
    george.tv_camera_insert_point(0, 0, 0, 0, 1)
    george.tv_camera_insert_point(5, 100, 150, 45, 1)

    test_project_obj.new_from_camera()


def test_project_duplicate(
    test_project_obj: Project,
    cleanup_current_project: None,
) -> None:
    assert test_project_obj.duplicate() != test_project_obj


def test_project_close(test_project_obj: Project) -> None:
    test_project_obj.close()
    assert test_project_obj.is_closed

    # The project can't be refreshed
    with pytest.raises(ValueError):
        test_project_obj.refresh()


def test_project_close_all(create_some_projects: list[Project]) -> None:
    Project.close_all()
    assert all(p.is_closed for p in create_some_projects)


def test_project_load(test_project_obj: Project) -> None:
    test_project_obj.save()
    assert Project.load(test_project_obj.path) == test_project_obj


def test_project_save(test_project_obj: Project, tmp_path: Path) -> None:
    test_project_obj.save(tmp_path / "save.tvpp")


def test_project_save_destination_does_not_exist(
    test_project_obj: Project, tmp_path: Path
) -> None:
    with pytest.raises(ValueError, match="folder does not exist"):
        test_project_obj.save(tmp_path / "lo" / "save.tvpp")
