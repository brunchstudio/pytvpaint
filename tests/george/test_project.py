from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any

import pytest
from pytvpaint.george import (
    FieldOrder,
    ResizeOption,
    RGBColor,
    SaveFormat,
    tv_save_mode_get,
    tv_save_mode_set,
)
from pytvpaint.george import tv_camera_insert_point
from pytvpaint.george.clip import (
    tv_clip_current_id,
    tv_clip_info,
    tv_load_sequence,
)
from pytvpaint.george import GeorgeError, NoObjectWithIdError
from pytvpaint.george import (
    BackgroundMode,
    TVPProject,
    tv_background_get,
    tv_background_set,
    tv_frame_rate_get,
    tv_frame_rate_set,
    tv_get_field,
    tv_get_height,
    tv_get_width,
    tv_load_palette,
    tv_load_project,
    tv_project_close,
    tv_project_current_frame_get,
    tv_project_current_frame_set,
    tv_project_current_id,
    tv_project_duplicate,
    tv_project_enum_id,
    tv_project_header_author_get,
    tv_project_header_author_set,
    tv_project_header_info_get,
    tv_project_header_info_set,
    tv_project_header_notes_get,
    tv_project_header_notes_set,
    tv_project_info,
    tv_project_new,
    tv_project_render_camera,
    tv_project_save_audio_dependencies,
    tv_project_save_sequence,
    tv_project_save_video_dependencies,
    tv_project_select,
    tv_ratio,
    tv_resize_page,
    tv_resize_project,
    tv_save_palette,
    tv_save_project,
    tv_save_sequence,
    tv_sound_project_adjust,
    tv_sound_project_info,
    tv_sound_project_new,
    tv_sound_project_reload,
    tv_sound_project_remove,
    tv_start_frame_get,
    tv_start_frame_set,
)

from tests.conftest import FixtureYield


def test_tv_background_get() -> None:
    tv_background_get()


COLORS = [RGBColor(255, 0, 0), RGBColor(0, 255, 0), RGBColor(0, 0, 255)]


@pytest.mark.parametrize(
    "test",
    [
        *[(BackgroundMode.COLOR, [c]) for c in COLORS],
        *[(BackgroundMode.CHECK, [*cs]) for cs in itertools.combinations(COLORS, 2)],
        (BackgroundMode.NONE, []),
    ],
)
def test_tv_background_set(test: tuple[BackgroundMode, list[RGBColor]]) -> None:
    mode, args = test
    tv_background_set(mode, *args)

    current_color = tv_background_get()

    if mode == BackgroundMode.NONE:
        assert current_color is None
    elif type(current_color) == tuple:
        assert list(current_color) == args
    else:
        assert current_color == args[0]


@pytest.mark.parametrize("width", [500, 1920])
@pytest.mark.parametrize("height", [500, 1080])
@pytest.mark.parametrize("pixel_aspect_ratio", [1.0, 2.0, 10.0])
@pytest.mark.parametrize("frame_rate", [24.0, 12.0])
@pytest.mark.parametrize("field_order", FieldOrder)
@pytest.mark.parametrize("start_frame", [1, 50])
def test_tv_project_new(
    tmp_path: Path,
    cleanup_current_project: None,
    width: int,
    height: int,
    pixel_aspect_ratio: float,
    frame_rate: float,
    field_order: FieldOrder,
    start_frame: int,
) -> None:
    project_path = tmp_path / "project.tvpp"
    tv_project_new(
        project_path,
        width,
        height,
        pixel_aspect_ratio,
        frame_rate,
        field_order,
        start_frame,
    )

    project = tv_project_info(tv_project_current_id())
    assert Path(project.path) == project_path
    assert project.width == width
    assert project.height == height
    assert project.field_order == field_order
    assert project.start_frame == start_frame


@pytest.fixture
def other_saved_project(tmp_path: Path) -> FixtureYield[TVPProject]:
    other_project_path = tmp_path / "other.tvpp"
    other_project_id = tv_project_new(other_project_path, width=200, height=200)
    other_project = tv_project_info(other_project_id)

    tv_save_project(other_project.path)
    tv_project_close(other_project.id)

    yield other_project


def test_tv_load_project(
    other_saved_project: TVPProject, cleanup_current_project: None
) -> None:
    # Load the project
    pid = tv_load_project(other_saved_project.path)
    assert tv_project_info(pid) == other_saved_project


def test_tv_load_project_wrong_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        tv_load_project(tmp_path / "folder" / "project.tvpp")


@pytest.mark.parametrize("ext", [".tvpp", ".abc", ".tvpx"])
def test_tv_save_project(test_project: TVPProject, tmp_path: Path, ext: str) -> None:
    project_path = (tmp_path / "save").with_suffix(ext)
    tv_save_project(project_path)
    assert project_path.with_suffix(".tvpp").exists()


def test_tv_save_project_wrong_path(test_project: TVPProject, tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        tv_save_project(tmp_path / "folder" / "project.tvpp")


def projects_equal(p1: TVPProject, p2: TVPProject) -> bool:
    """Compares two project omitting 'id' and 'path' attributes"""
    from dataclasses import asdict

    p1_dict = asdict(p1)
    p2_dict = asdict(p2)

    del p1_dict["id"]
    del p1_dict["path"]
    del p2_dict["id"]
    del p2_dict["path"]

    return p1_dict == p2_dict


def test_tv_project_duplicate(
    test_project: TVPProject, cleanup_current_project: None
) -> None:
    tv_project_duplicate()
    dup_project = tv_project_info(tv_project_current_id())
    assert projects_equal(test_project, dup_project)


def test_tv_project_enum_id() -> None:
    assert tv_project_enum_id(0) == tv_project_current_id()


@pytest.mark.parametrize("pos", [-1, 100, 58])
def test_tv_project_enum_id_wrong_pos(pos: int) -> None:
    with pytest.raises(GeorgeError):
        tv_project_enum_id(pos)


def test_tv_project_current_id(test_project: TVPProject) -> None:
    assert tv_project_current_id() == test_project.id


def test_tv_project_info(test_project: TVPProject) -> None:
    assert tv_project_info(test_project.id) == test_project


@pytest.mark.skip("Doesn't return an empty string")
def test_tv_project_info_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_project_info("unknown")


def test_tv_project_select(test_project: TVPProject, tmp_path: Path) -> None:
    other = tv_project_new(tmp_path / "other.tvpp")
    assert tv_project_current_id() == other

    tv_project_select(test_project.id)
    assert tv_project_current_id() == test_project.id
    tv_project_close(other)


def test_tv_project_close(tmp_path: Path) -> None:
    pid = tv_project_new(tmp_path / "close.tvpp")
    tv_project_close(pid)

    with pytest.raises(NoObjectWithIdError):
        tv_project_info(pid)


def get_project_pos(pid: str) -> int:
    """Return the given project position"""
    pos = 0
    while True:
        try:
            if tv_project_enum_id(pos) == pid:
                return pos
        except GeorgeError as err:
            raise ValueError("Project does not exist") from err
        pos += 1


@pytest.mark.parametrize(
    "res",
    [(200, 200), (1000, 100), (0, 500)],
)
def test_tv_resize_project(
    test_project: TVPProject,
    res: tuple[int, int],
    cleanup_current_project: None,
) -> None:
    current_pos = get_project_pos(test_project.id)

    width, height = res
    tv_resize_project(width, height)

    resized_project_id = tv_project_enum_id(current_pos)
    resized_project = tv_project_info(resized_project_id)

    assert resized_project.width == width
    assert resized_project.height == height


@pytest.mark.parametrize(
    "res",
    [(200, 200), (1000, 100), (0, 500)],
)
@pytest.mark.parametrize("resize", ResizeOption)
def test_tv_resize_page(
    test_project: TVPProject,
    res: tuple[int, int],
    resize: ResizeOption,
    cleanup_current_project: None,
) -> None:
    current_pos = get_project_pos(test_project.id)

    width, height = res
    tv_resize_page(width, height, resize)

    resized_id = tv_project_enum_id(current_pos)
    resized = tv_project_info(resized_id)

    assert resized.width == width
    assert resized.height == height


def test_tv_get_width(test_project: TVPProject) -> None:
    assert tv_get_width() == test_project.width


def test_tv_get_height(test_project: TVPProject) -> None:
    assert tv_get_height() == test_project.height


@pytest.mark.skip("Does not work, returns empty string")
def test_tv_ratio(test_project: TVPProject) -> None:
    assert tv_ratio() == test_project.pixel_aspect_ratio


def test_tv_get_field(test_project: TVPProject) -> None:
    assert tv_get_field() == test_project.field_order


@pytest.mark.parametrize("mark_in_out", [None, (0, 5), (0, 0), (0, 1), (2, 5)])
def test_tv_save_sequence(
    test_project: TVPProject,
    tmp_path: Path,
    ppm_sequence: list[Path],
    mark_in_out: tuple[int, int] | None,
) -> None:
    tv_load_sequence(ppm_sequence[0])

    save_ext, _ = tv_save_mode_get()
    out_sequence = tmp_path / "out"
    tv_save_sequence(out_sequence, mark_in_out)

    clip = tv_clip_info(tv_clip_current_id())
    start_end = mark_in_out or (clip.first_frame, clip.last_frame)

    for i in range(start_end[1] - start_end[0]):
        image_name = out_sequence.name + str(i).zfill(5)
        image_ext = "." + ("jpg" if save_ext == SaveFormat.JPG else save_ext.value)
        image_path = out_sequence.with_name(image_name).with_suffix(image_ext)
        assert image_path.exists()


def test_tv_save_sequence_wrong_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        tv_save_sequence(tmp_path / "folder" / "out")


@pytest.mark.parametrize("use_camera", [None, False, True])
@pytest.mark.parametrize("start_end_frame", [None, (0, 5), (0, 0), (0, 1), (2, 5)])
def test_tv_project_save_sequence(
    test_project: TVPProject,
    tmp_path: Path,
    ppm_sequence: list[Path],
    use_camera: bool | None,
    start_end_frame: tuple[int, int] | None,
) -> None:
    tv_load_sequence(ppm_sequence[0])

    if use_camera:
        tv_camera_insert_point(0, 50, 50, 0, 1)

    out_sequence = tmp_path / "out"
    tv_project_save_sequence(out_sequence, use_camera, start_end_frame)

    clip = tv_clip_info(tv_clip_current_id())
    save_ext, _ = tv_save_mode_get()
    start_end = start_end_frame or (clip.first_frame, clip.last_frame)

    tv_save_mode_set(SaveFormat.JPG)

    for i in range(start_end[1] - start_end[0]):
        image_name = out_sequence.name + str(i).zfill(5)
        image_ext = "." + ("jpg" if save_ext == SaveFormat.JPG else save_ext.value)
        image_path = out_sequence.with_name(image_name).with_suffix(image_ext)
        assert image_path.exists()


def test_tv_project_render_camera(
    test_project: TVPProject,
    ppm_sequence: list[Path],
    cleanup_current_project: None,
) -> None:
    tv_load_sequence(ppm_sequence[0])

    tv_camera_insert_point(0, 50, 50, 0, 1)
    tv_camera_insert_point(1, 100, 50, 0, 0.5)

    new_project_id = tv_project_render_camera(test_project.id)
    assert projects_equal(tv_project_info(new_project_id), test_project)


def test_tv_frame_rate_get(test_project: TVPProject) -> None:
    project_frame_rate, playback_frame_rate = tv_frame_rate_get()
    assert test_project.frame_rate == playback_frame_rate
    assert test_project.frame_rate == project_frame_rate


@pytest.mark.parametrize("frame_rate", [1, 25, 50, 100])
def test_tv_frame_rate_set_project(test_project: TVPProject, frame_rate: float) -> None:
    tv_frame_rate_set(frame_rate)
    project_frame_rate, _ = tv_frame_rate_get()
    assert project_frame_rate == frame_rate


@pytest.mark.parametrize("frame_rate", [1, 25, 50, 100])
def test_tv_frame_rate_set_preview(test_project: TVPProject, frame_rate: float) -> None:
    tv_frame_rate_set(frame_rate, preview=True)
    _, preview_frame_rate = tv_frame_rate_get()
    assert preview_frame_rate == frame_rate


def test_tv_project_current_frame_get(test_project: TVPProject) -> None:
    assert tv_project_current_frame_get() == 0


@pytest.mark.parametrize("frame", [1, 25, 50, 100])
def test_tv_project_current_frame_set(test_project: TVPProject, frame: int) -> None:
    tv_project_current_frame_set(frame)
    assert tv_project_current_frame_get() == frame


def test_tv_load_palette(tmp_path: Path) -> None:
    palette_path = tmp_path / "palette.tvpx"
    tv_save_palette(palette_path)
    tv_load_palette(palette_path)


def test_tv_load_palette_wrong_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        tv_load_palette(tmp_path / "palette.tvpx")


def test_tv_save_palette_wrong_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        tv_save_palette(tmp_path / "out" / "palette.tvpx")


def test_tv_project_save_video_dependencies() -> None:
    tv_project_save_video_dependencies()


def test_tv_project_save_audio_dependencies() -> None:
    tv_project_save_audio_dependencies()


def test_tv_sound_project_info(test_project: TVPProject, wav_file: Path) -> None:
    tv_sound_project_new(wav_file)
    tv_sound_project_info(test_project.id, 0)


def test_tv_sound_project_info_wrong_project_id() -> None:
    with pytest.raises(GeorgeError):
        tv_sound_project_info("lo", 0)


def test_tv_sound_project_info_wrong_track_index(test_project: TVPProject) -> None:
    with pytest.raises(GeorgeError):
        tv_sound_project_info(test_project.id, 0)


def test_tv_sound_project_new_wrong_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        tv_sound_project_new(tmp_path / "sound.wav")


def test_tv_sound_project_remove(test_project: TVPProject, wav_file: Path) -> None:
    tv_sound_project_new(wav_file)
    tv_sound_project_info(test_project.id, 0)
    tv_sound_project_remove(0)

    with pytest.raises(GeorgeError):
        tv_sound_project_info(test_project.id, 0)


def test_tv_sound_project_remove_wrong_track_index(test_project: TVPProject) -> None:
    with pytest.raises(GeorgeError):
        tv_sound_project_remove(0)


def test_tv_sound_project_reload(test_project: TVPProject, wav_file: Path) -> None:
    tv_sound_project_new(wav_file)
    tv_sound_project_reload(test_project.id, 0)


def test_tv_sound_project_reload_wrong_project_id() -> None:
    with pytest.raises(GeorgeError):
        tv_sound_project_reload("lo", 0)


def test_tv_sound_project_reload_wrong_track_index(test_project: TVPProject) -> None:
    with pytest.raises(GeorgeError):
        tv_sound_project_reload(test_project.id, 0)


@pytest.mark.parametrize(
    "args",
    [
        (True, 5),
        (False, 10),
        (True,),
        (True, 2, 5),
        (False, 1.5, 0, 1, 4, 4, 4),
    ],
)
def test_tv_sound_project_adjust(
    test_project: TVPProject,
    wav_file: Path,
    args: tuple[Any, ...],
) -> None:
    tv_sound_project_new(wav_file)
    tv_sound_project_adjust(0, *args)

    attrs_check = [
        "mute",
        "volume",
        "offset",
        "fade_in_start",
        "fade_in_stop",
        "fade_out_start",
        "fade_out_stop",
        "color_index",
    ]

    sound = tv_sound_project_info(test_project.id, 0)
    for attr, arg in zip(attrs_check, args):
        current = getattr(sound, attr)
        err_msg = f"Error checking {attr} (expected: {arg}, current: {current})"
        assert current == arg, err_msg


def test_tv_project_header_info_get(test_project: TVPProject) -> None:
    assert tv_project_header_info_get(test_project.id) == ""


def test_tv_project_header_info_get_wrong_id(test_project: TVPProject) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_project_header_info_get("ll")


@pytest.mark.parametrize("header", ["", "Hello", "THis is a project header"])
def test_tv_project_header_info_set(test_project: TVPProject, header: str) -> None:
    tv_project_header_info_set(test_project.id, header)
    assert tv_project_header_info_get(test_project.id) == header


def test_tv_project_header_info_set_wrong_id(test_project: TVPProject) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_project_header_info_set("ll", "header")


def test_tv_project_header_author_get(test_project: TVPProject) -> None:
    import getpass

    assert tv_project_header_author_get(test_project.id) == getpass.getuser()


def test_tv_project_header_author_get_wrong_id(test_project: TVPProject) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_project_header_author_get("ll")


@pytest.mark.parametrize("author", ["l", "Hello", "THis is a project author"])
def test_tv_project_header_author_set(test_project: TVPProject, author: str) -> None:
    tv_project_header_author_set(test_project.id, author)
    assert tv_project_header_author_get(test_project.id) == author


def test_tv_project_header_author_set_wrong_id(test_project: TVPProject) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_project_header_author_set("ll", "header")


def test_tv_project_header_notes_get(test_project: TVPProject) -> None:
    assert tv_project_header_notes_get(test_project.id) == ""


def test_tv_project_header_notes_get_wrong_id(test_project: TVPProject) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_project_header_notes_get("ll")


@pytest.mark.parametrize("notes", ["l", "Hello", "THis is a project notes"])
def test_tv_project_header_notes_set(test_project: TVPProject, notes: str) -> None:
    tv_project_header_notes_set(test_project.id, notes)
    assert tv_project_header_notes_get(test_project.id) == notes


def test_tv_project_header_notes_set_wrong_id(test_project: TVPProject) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_project_header_notes_set("ll", "header")


def test_tv_start_frame_get(test_project: TVPProject) -> None:
    tv_start_frame_set(12)
    assert tv_start_frame_get() == 12


@pytest.mark.parametrize("start", [0, 1, 50, 100])
def test_tv_start_frame_set(test_project: TVPProject, start: int) -> None:
    tv_start_frame_set(start)
    assert tv_start_frame_get() == start
