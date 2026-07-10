from pathlib import Path

import pytest

from pytvpaint import george, guideline
from pytvpaint.clip import Clip
from pytvpaint.george.grg_project import TVPProject
from pytvpaint.project import Project
from pytvpaint.scene import Scene
from pytvpaint.sound import ProjectSound
from tests.conftest import FixtureYield

IS_TVP12 = george.tv_version()[1].startswith("12")


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
    other_project = george.tv_project_new(tmp_path / "other.tvpp", width=1234, height=567)
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


def test_project_resize(test_project_obj: Project, cleanup_current_project: None) -> None:
    resized = test_project_obj.resize(100, 200)

    # The resized project is a new project
    assert resized != test_project_obj

    assert resized.width == 100
    assert resized.height == 200

    # It closes the project but it still exists on disk
    assert test_project_obj.is_closed


def test_project_resize_overwrite(test_project_obj: Project, cleanup_current_project: None) -> None:
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


@pytest.mark.skipif(IS_TVP12, reason="Field Order options are deprecated in tvpaint 12.")
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


def test_project_end_frame_clip_simple(test_project_obj: Project) -> None:
    test_project_obj.start_frame = 1

    clip = test_project_obj.current_clip
    layer = clip.add_layer("anim")
    layer.convert_to_anim_layer()

    layer.add_instance(10)

    assert test_project_obj.end_frame == 10


def test_project_end_frame_clip_mark_out(test_project_obj: Project) -> None:
    test_project_obj.start_frame = 3

    clip = test_project_obj.current_clip
    clip.mark_in = 4
    clip.mark_out = 8

    layer = clip.add_layer("anim")
    layer.convert_to_anim_layer()

    # The instance exceeds the mark out so it's not taken into account in clip duration
    layer.add_instance(10)

    assert test_project_obj.end_frame == 7


@pytest.mark.parametrize("mark_in", [1, 2, 10, 100])
@pytest.mark.parametrize("current_frame", [0, 1, 5, 50])
@pytest.mark.parametrize("start_frame", [2, 5, 20])
def test_project_current_frame(test_project_obj: Project, mark_in: int, current_frame: int, start_frame: int) -> None:
    test_project_obj.start_frame = start_frame
    test_project_obj.current_clip.mark_in = mark_in
    test_project_obj.current_frame = current_frame

    assert test_project_obj.current_frame == current_frame


def test_project_clear_background(test_project_obj: Project) -> None:
    test_project_obj.clear_background()

    mode, colors = george.tv_background_get()
    assert mode == george.BackgroundMode.NONE
    assert colors is None


@pytest.mark.parametrize(
    "color",
    [
        george.RGBColor(0, 255, 0),
        george.RGBColor(255, 255, 0),
        george.RGBColor(0, 255, 255),
    ],
)
def test_project_set_background_solid_color(test_project_obj: Project, color: george.RGBColor) -> None:
    test_project_obj.background_mode = george.BackgroundMode.COLOR
    test_project_obj.background_colors = color

    mode, colors = george.tv_background_get()
    assert test_project_obj.background_mode == mode
    assert test_project_obj.background_colors == colors


@pytest.mark.parametrize(
    "colors",
    [
        (george.RGBColor(255, 255, 255), george.RGBColor(0, 0, 0)),
        (george.RGBColor(0, 255, 0), george.RGBColor(0, 255, 255)),
    ],
)
def test_project_set_background_checker_colors(
    test_project_obj: Project, colors: tuple[george.RGBColor, george.RGBColor]
) -> None:
    test_project_obj.background_mode = george.BackgroundMode.CHECK
    test_project_obj.background_colors = colors

    mode, actual_colors = george.tv_background_get()
    assert test_project_obj.background_mode == mode
    assert test_project_obj.background_colors == actual_colors


@pytest.mark.parametrize("header", ["", "Hello", "This is a project header", "This is a project \nheader"])
def test_project_header_info(test_project_obj: Project, header: str) -> None:
    test_project_obj.header_info = header
    assert test_project_obj.header_info == header


@pytest.mark.parametrize("author", ["a", "Hello", "This is a project author", "This is a project \nauthor"])
def test_project_author(test_project_obj: Project, author: str) -> None:
    test_project_obj.author = author
    assert test_project_obj.author == author


@pytest.mark.parametrize("notes", ["a", "Hello", "This is a project note", "This is a project \nnote"])
def test_project_notes(test_project_obj: Project, notes: str) -> None:
    test_project_obj.notes = notes
    assert test_project_obj.notes == notes


def test_project_get_project(test_project_obj: Project) -> None:
    assert Project.get_project(by_id=test_project_obj.id) == test_project_obj
    assert Project.get_project(by_name=test_project_obj.name) == test_project_obj


def test_project_get_project_wrong_id(test_project_obj: Project) -> None:
    res = Project.get_project(by_id="unknown")
    assert res is None


def test_project_get_project_wrong_name(test_project_obj: Project) -> None:
    res = Project.get_project(by_name="name")
    assert res is None


def test_project_current_scene_ids(
    test_project_obj: Project,
    create_some_scenes: list[Scene],
) -> None:
    ids = list(test_project_obj.current_scene_ids())
    assert ids == [s.id for s in create_some_scenes]


def test_project_current_scene(test_project_obj: Project, test_scene_obj: Scene) -> None:
    assert test_project_obj.current_scene == test_scene_obj


def test_project_scenes(
    test_project_obj: Project,
    create_some_scenes: list[Scene],
) -> None:
    assert list(test_project_obj.scenes) == create_some_scenes


def test_project_get_scene(test_project_obj: Project, test_scene_obj: Scene) -> None:
    test_project_obj.get_scene(scene_id=test_scene_obj.id)


def test_project_add_scene(test_project_obj: Project) -> None:
    scene = test_project_obj.add_scene()
    assert test_project_obj.current_scene == scene


@pytest.mark.parametrize("index", range(5))
def test_project_current_clip(test_project_obj: Project, create_some_clips: list[Clip], index: int) -> None:
    clip = create_some_clips[index]
    clip.make_current()
    assert test_project_obj.current_clip == clip


def test_project_clips(test_project_obj: Project, create_some_clips: list[Clip]) -> None:
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
def test_project_add_clip(test_project_obj: Project, test_scene_obj: Scene, name: str) -> None:
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


def test_project_add_guideline_line(test_project_obj: Project) -> None:
    guideline_line = test_project_obj.add_guideline_line(x=10, y=20, angle=45)
    assert isinstance(guideline_line, guideline.GuidelineLine)
    assert guideline_line.x == 10
    assert guideline_line.y == 20
    assert guideline_line.angle == 45


def test_project_add_guideline_segment(test_project_obj: Project) -> None:
    guideline_segment = test_project_obj.add_guideline_segment(x1=0, y1=0, x2=100, y2=100)
    assert isinstance(guideline_segment, guideline.GuidelineSegment)
    assert guideline_segment.x1 == 0
    assert guideline_segment.y1 == 0
    assert guideline_segment.x2 == 100
    assert guideline_segment.y2 == 100


def test_project_add_guideline_circle(test_project_obj: Project) -> None:
    guideline_circle = test_project_obj.add_guideline_circle(x=50, y=50, radius=25)
    assert isinstance(guideline_circle, guideline.GuidelineCircle)
    assert guideline_circle.x == 50
    assert guideline_circle.y == 50
    assert guideline_circle.radius == 25


def test_project_add_guideline_ellipse(test_project_obj: Project) -> None:
    guideline_ellipse = test_project_obj.add_guideline_ellipse(x=10, y=10, radius_a=20, radius_b=10)
    assert isinstance(guideline_ellipse, guideline.GuidelineEllipse)
    assert guideline_ellipse.x == 10
    assert guideline_ellipse.y == 10
    assert guideline_ellipse.radius_a == 20
    assert guideline_ellipse.radius_b == 10


def test_project_add_guideline_grid(test_project_obj: Project) -> None:
    guideline_grid = test_project_obj.add_guideline_grid(x=0, y=0, width=1920, height=1080)
    assert isinstance(guideline_grid, guideline.GuidelineGrid)
    assert guideline_grid.x == 0
    assert guideline_grid.y == 0
    assert guideline_grid.width == 1920
    assert guideline_grid.height == 1080


def test_project_add_guideline_marks(test_project_obj: Project) -> None:
    guideline_marks = test_project_obj.add_guideline_marks(count_x=4, count_y=3)
    assert isinstance(guideline_marks, guideline.GuidelineMarks)
    assert guideline_marks.count_x == 4
    assert guideline_marks.count_y == 3


def test_project_add_guideline_field_chart(test_project_obj: Project) -> None:
    guideline_field = test_project_obj.add_guideline_field_chart()
    assert isinstance(guideline_field, guideline.GuidelineFieldChart)
    # (No internal metrics to assert on creation for field charts)


def test_project_add_guideline_animator_field(test_project_obj: Project) -> None:
    guideline_anim = test_project_obj.add_guideline_animator_field()
    assert isinstance(guideline_anim, guideline.GuidelineAnimatorField)
    # (No internal metrics to assert on creation for animator fields)


def test_project_add_guideline_safe_area(test_project_obj: Project) -> None:
    guideline_safe = test_project_obj.add_guideline_safe_area(sf_out=10, sf_in=20)
    assert isinstance(guideline_safe, guideline.GuidelineSafeArea)
    assert guideline_safe.sf_out == 10
    assert guideline_safe.sf_in == 20


def test_project_add_guideline_vanishing_point1(test_project_obj: Project) -> None:
    guideline_vp1 = test_project_obj.add_guideline_vanishing_point1(x=100, y=100, grid=True)
    assert isinstance(guideline_vp1, guideline.GuidelineVanishPoint1)
    assert guideline_vp1.x == 100
    assert guideline_vp1.y == 100
    assert guideline_vp1.grid is True


def test_project_add_guideline_vanishing_point2(test_project_obj: Project) -> None:
    guideline_vp2 = test_project_obj.add_guideline_vanishing_point2(x1=10, y1=10, x2=100, y2=100)
    assert isinstance(guideline_vp2, guideline.GuidelineVanishPoint2)
    assert guideline_vp2.x1 == 10
    assert guideline_vp2.y1 == 10
    assert guideline_vp2.x2 == 100
    assert guideline_vp2.y2 == 100


def test_project_add_guideline_vanishing_point3(test_project_obj: Project) -> None:
    guideline_vp3 = test_project_obj.add_guideline_vanishing_point3(x1=10, y1=10, x2=100, y2=100, x3=50, y3=50)
    assert isinstance(guideline_vp3, guideline.GuidelineVanishPoint3)
    assert guideline_vp3.x1 == 10
    assert guideline_vp3.y1 == 10
    assert guideline_vp3.x2 == 100
    assert guideline_vp3.y2 == 100
    assert guideline_vp3.x3 == 50
    assert guideline_vp3.y3 == 50


def test_project_new(tmp_path: Path, cleanup_current_project: None) -> None:
    proj = Project.new(tmp_path / "project.tvpp")
    assert Project.current_project() == proj


def test_project_new_from_camera(test_project_obj: Project) -> None:
    george.tv_camera_insert_point(0, 0, 0, 0, 1)
    george.tv_camera_insert_point(5, 100, 150, 45, 1)

    test_project_obj.new_from_camera()


def test_project_duplicate(
    test_project_obj: Project,
) -> None:
    dup = test_project_obj.duplicate()
    assert dup != test_project_obj
    dup.close()


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


def test_project_save_destination_does_not_exist(test_project_obj: Project, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="folder does not exist"):
        test_project_obj.save(tmp_path / "lo" / "save.tvpp")
