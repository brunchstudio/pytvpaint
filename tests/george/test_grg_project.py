from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any

import pytest

from pytvpaint import george
from tests.conftest import FixtureYield


IS_TVP12 = george.tv_version()[1].startswith("12")
COLORS = [george.RGBColor(255, 0, 0), george.RGBColor(0, 255, 0), george.RGBColor(0, 0, 255)]


@pytest.mark.parametrize(
    "mode, colors",
    [
        *[(george.BackgroundMode.COLOR, c) for c in COLORS],
        *[(george.BackgroundMode.CHECK, cs) for cs in itertools.combinations(COLORS, 2)],
        (george.BackgroundMode.NONE, None),
    ],
)
def test_tv_background(
    mode: george.BackgroundMode, colors: tuple[george.RGBColor, george.RGBColor] | george.RGBColor | None
) -> None:
    george.tv_background_set(mode, colors)

    current_mode, current_colors = george.tv_background_get()

    assert mode == current_mode
    assert current_colors == colors

    # reset color
    george.tv_background_set(george.BackgroundMode.COLOR, george.RGBColor(255, 255, 255))


@pytest.mark.parametrize("width", [500, 1920])
@pytest.mark.parametrize("height", [500, 1080])
@pytest.mark.parametrize("pixel_aspect_ratio", [1.0, 2.0, 10.0])
@pytest.mark.parametrize("frame_rate", [24.0, 12.0])
@pytest.mark.parametrize("field_order", (list(george.FieldOrder) if not IS_TVP12 else [george.FieldOrder.NONE]))
@pytest.mark.parametrize("start_frame", [1, 50])
def test_tv_project_new(
    tmp_path: Path,
    cleanup_current_project: None,
    width: int,
    height: int,
    pixel_aspect_ratio: float,
    frame_rate: float,
    field_order: george.FieldOrder,
    start_frame: int,
) -> None:
    project_path = tmp_path / "project.tvpp"
    george.tv_project_new(
        project_path,
        width,
        height,
        pixel_aspect_ratio,
        frame_rate,
        field_order,
        start_frame,
    )

    project = george.tv_project_info(george.tv_project_current_id())
    assert Path(project.path) == project_path
    assert project.width == width
    assert project.height == height
    assert project.field_order == field_order
    assert project.start_frame == start_frame


@pytest.fixture
def other_saved_project(tmp_path: Path) -> FixtureYield[george.TVPProject]:
    other_project_path = tmp_path / "other.tvpp"
    other_project_id = george.tv_project_new(other_project_path, width=200, height=200)
    other_project = george.tv_project_info(other_project_id)

    george.tv_save_project(other_project.path)
    george.tv_project_close(other_project.id)

    yield other_project


def test_tv_load_project(other_saved_project: george.TVPProject, cleanup_current_project: None) -> None:
    # Load the project
    pid = george.tv_load_project(other_saved_project.path)
    assert george.tv_project_info(pid) == other_saved_project


def test_tv_load_project_wrong_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        george.tv_load_project(tmp_path / "folder" / "project.tvpp")


@pytest.mark.parametrize("ext", [".tvpp", ".abc", ".tvpx"])
def test_tv_save_project(test_project: george.TVPProject, tmp_path: Path, ext: str) -> None:
    project_path = (tmp_path / "save").with_suffix(ext)
    george.tv_save_project(project_path)
    assert project_path.with_suffix(".tvpp").exists()


def test_tv_save_project_wrong_path(test_project: george.TVPProject, tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        george.tv_save_project(tmp_path / "folder" / "project.tvpp")


def projects_equal(p1: george.TVPProject, p2: george.TVPProject) -> bool:
    """Compares two project omitting 'id' and 'path' attributes"""
    from dataclasses import asdict

    p1_dict = asdict(p1)
    p2_dict = asdict(p2)

    for attr in ["id", "path"]:
        del p1_dict[attr]
        del p2_dict[attr]

    return p1_dict == p2_dict


def test_tv_project_duplicate(
    test_project: george.TVPProject,
    cleanup_current_project: None,
) -> None:
    george.tv_project_duplicate()
    dup_project = george.tv_project_info(george.tv_project_current_id())
    assert projects_equal(test_project, dup_project)


def test_tv_project_enum_id() -> None:
    assert george.tv_project_enum_id(0) == george.tv_project_current_id()


@pytest.mark.parametrize("pos", [-1, 100, 58])
def test_tv_project_enum_id_wrong_pos(pos: int) -> None:
    with pytest.raises(george.GeorgeError):
        george.tv_project_enum_id(pos)


def test_tv_project_current_id(test_project: george.TVPProject) -> None:
    assert george.tv_project_current_id() == test_project.id


def test_tv_project_info(test_project: george.TVPProject) -> None:
    assert george.tv_project_info(test_project.id) == test_project


@pytest.mark.skip("Doesn't return an empty string")
def test_tv_project_info_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_project_info("unknown")


def test_tv_project_select(test_project: george.TVPProject, tmp_path: Path) -> None:
    other = george.tv_project_new(tmp_path / "other.tvpp")
    assert george.tv_project_current_id() == other

    george.tv_project_select(test_project.id)
    assert george.tv_project_current_id() == test_project.id
    george.tv_project_close(other)


def test_tv_project_close(tmp_path: Path) -> None:
    pid = george.tv_project_new(tmp_path / "close.tvpp")
    george.tv_project_close(pid)

    with pytest.raises(george.NoObjectWithIdError):
        george.tv_project_info(pid)


def get_project_pos(pid: str) -> int:
    """Return the given project position"""
    pos = 0
    while True:
        try:
            if george.tv_project_enum_id(pos) == pid:
                return pos
        except george.GeorgeError as err:
            raise ValueError("Project does not exist") from err
        pos += 1


@pytest.mark.parametrize(
    "res",
    [(200, 200), (1000, 100), (0, 500)],
)
def test_tv_resize_project(
    test_project: george.TVPProject,
    res: tuple[int, int],
    cleanup_current_project: None,
) -> None:
    if IS_TVP12 and 0 in res:
        return

    current_pos = get_project_pos(test_project.id)

    width, height = res
    george.tv_resize_project(width, height)

    resized_project_id = george.tv_project_enum_id(current_pos)
    resized_project = george.tv_project_info(resized_project_id)

    assert resized_project.width == width
    assert resized_project.height == height


@pytest.mark.parametrize(
    "res",
    [(200, 200), (1000, 100)],
)
@pytest.mark.parametrize("resize", george.ResizeOption)
def test_tv_resize_page(
    test_project: george.TVPProject,
    res: tuple[int, int],
    resize: george.ResizeOption,
    cleanup_current_project: None,
) -> None:
    if IS_TVP12 and 0 in res:
        return

    current_pos = get_project_pos(test_project.id)

    width, height = res
    george.tv_resize_page(width, height, resize)

    resized_id = george.tv_project_enum_id(current_pos)
    resized = george.tv_project_info(resized_id)

    assert resized.width == width
    assert resized.height == height


def test_tv_get_width(test_project: george.TVPProject) -> None:
    assert george.tv_get_width() == test_project.width


def test_tv_get_height(test_project: george.TVPProject) -> None:
    assert george.tv_get_height() == test_project.height


@pytest.mark.skip("Does not work, returns empty string")
def test_tv_ratio(test_project: george.TVPProject) -> None:
    assert george.tv_ratio() == test_project.pixel_aspect_ratio


@pytest.mark.skipif(IS_TVP12, reason="Skip since this is now deprecated in TVPaint 12.")
def test_tv_get_field(test_project: george.TVPProject) -> None:
    assert george.tv_get_field() == test_project.field_order


@pytest.mark.parametrize("use_camera", [False, True])
@pytest.mark.parametrize("start, end", [(None, None), (0, 5), (0, 0), (0, 1), (2, 5)])
def test_tv_project_save_sequence(
    test_project: george.TVPProject,
    tmp_path: Path,
    png_sequence: list[Path],
    use_camera: bool,
    start: int | None,
    end: int | None,
) -> None:
    george.tv_load_sequence(png_sequence[0])

    if use_camera:
        george.tv_camera_insert_point(0, 50, 50, 0, 1)

    out_sequence = tmp_path / "out"
    george.tv_project_save_sequence(out_sequence, use_camera, start, end)

    clip = george.tv_clip_info(george.tv_clip_current_id())
    save_ext, _ = george.tv_save_mode_get()
    start_end = (start, end) if (start is not None and end is not None) else (clip.first_frame, clip.last_frame)

    george.tv_save_mode_set(george.SaveFormat.JPG)

    for i in range(start_end[1] - start_end[0]):
        image_name = f"{out_sequence.name}{i:05d}"
        image_ext = "." + ("jpg" if save_ext == george.SaveFormat.JPG else save_ext.value)
        image_path = out_sequence.with_name(f"{image_name}{image_ext}")
        assert image_path.exists()


def test_tv_project_render_camera(
    test_project: george.TVPProject,
    png_sequence: list[Path],
    cleanup_current_project: None,
) -> None:
    george.tv_load_sequence(png_sequence[0])

    george.tv_camera_insert_point(0, 50, 50, 0, 1)
    george.tv_camera_insert_point(1, 100, 50, 0, 0.5)

    new_project_id = george.tv_project_render_camera(test_project.id)
    assert projects_equal(george.tv_project_info(new_project_id), test_project)


def test_tv_frame_rate_get(test_project: george.TVPProject) -> None:
    project_frame_rate, playback_frame_rate = george.tv_frame_rate_get()
    assert test_project.frame_rate == playback_frame_rate
    assert test_project.frame_rate == project_frame_rate


@pytest.mark.parametrize("frame_rate", [1, 25, 50, 100])
def test_tv_frame_rate_set_project(test_project: george.TVPProject, frame_rate: float) -> None:
    george.tv_frame_rate_set(frame_rate)
    project_frame_rate, _ = george.tv_frame_rate_get()
    assert project_frame_rate == frame_rate


@pytest.mark.parametrize("frame_rate", [1, 25, 50, 100])
def test_tv_frame_rate_set_preview(test_project: george.TVPProject, frame_rate: float) -> None:
    george.tv_frame_rate_set(frame_rate, preview=True)
    _, preview_frame_rate = george.tv_frame_rate_get()
    assert preview_frame_rate == frame_rate


def test_tv_project_current_frame_get(test_project: george.TVPProject) -> None:
    assert george.tv_project_current_frame_get() == 0


@pytest.mark.parametrize("frame", [1, 25, 50, 100])
def test_tv_project_current_frame_set(test_project: george.TVPProject, frame: int) -> None:
    george.tv_project_current_frame_set(frame)
    assert george.tv_project_current_frame_get() == frame


def test_tv_load_palette(tmp_path: Path) -> None:
    palette_path = tmp_path / "palette.tvpx"
    george.tv_save_palette(palette_path)
    george.tv_load_palette(palette_path)


def test_tv_load_palette_wrong_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        george.tv_load_palette(tmp_path / "palette.tvpx")


def test_tv_save_palette_wrong_path(tmp_path: Path) -> None:
    with pytest.raises(NotADirectoryError):
        george.tv_save_palette(tmp_path / "out" / "palette.tvpx")


def test_tv_project_save_video_dependencies(test_project: george.TVPProject) -> None:
    with pytest.raises(george.GeorgeError):
        george.tv_project_save_video_dependencies("")

    assert george.tv_project_save_video_dependencies(test_project.id) == 0
    assert george.tv_project_save_video_dependencies(test_project.id, True, False) == 1
    assert george.tv_project_save_video_dependencies(test_project.id, True, True) == 1
    assert george.tv_project_save_video_dependencies(test_project.id, False, True) == 1


def test_tv_project_save_audio_dependencies(test_project: george.TVPProject) -> None:
    with pytest.raises(george.GeorgeError):
        george.tv_project_save_audio_dependencies("")

    assert george.tv_project_save_audio_dependencies(test_project.id) == 0
    assert george.tv_project_save_audio_dependencies(test_project.id, True) == 1
    assert george.tv_project_save_audio_dependencies(test_project.id, False) == 1


def test_tv_sound_project_info(test_project: george.TVPProject, wav_file: Path) -> None:
    george.tv_sound_project_new(wav_file)
    george.tv_sound_project_info(test_project.id, 0)


def test_tv_sound_project_info_wrong_project_id() -> None:
    with pytest.raises(george.GeorgeError):
        george.tv_sound_project_info("lo", 0)


def test_tv_sound_project_info_wrong_track_index(test_project: george.TVPProject) -> None:
    with pytest.raises(george.GeorgeError):
        george.tv_sound_project_info(test_project.id, 0)


def test_tv_sound_project_new_wrong_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        george.tv_sound_project_new(tmp_path / "sound.wav")


def test_tv_sound_project_remove(test_project: george.TVPProject, wav_file: Path) -> None:
    george.tv_sound_project_new(wav_file)
    george.tv_sound_project_info(test_project.id, 0)
    george.tv_sound_project_remove(0)

    with pytest.raises(george.GeorgeError):
        george.tv_sound_project_info(test_project.id, 0)


def test_tv_sound_project_remove_wrong_track_index(test_project: george.TVPProject) -> None:
    with pytest.raises(george.GeorgeError):
        george.tv_sound_project_remove(0)


def test_tv_sound_project_reload(test_project: george.TVPProject, wav_file: Path) -> None:
    george.tv_sound_project_new(wav_file)
    george.tv_sound_project_reload(test_project.id, 0)


def test_tv_sound_project_reload_wrong_project_id() -> None:
    with pytest.raises(george.GeorgeError):
        george.tv_sound_project_reload("lo", 0)


def test_tv_sound_project_reload_wrong_track_index(test_project: george.TVPProject) -> None:
    with pytest.raises(george.GeorgeError):
        george.tv_sound_project_reload(test_project.id, 0)


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
    test_project: george.TVPProject,
    wav_file: Path,
    args: tuple[Any, ...],
) -> None:
    george.tv_sound_project_new(wav_file)
    george.tv_sound_project_adjust(0, *args)

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

    sound = george.tv_sound_project_info(test_project.id, 0)
    for attr, arg in zip(attrs_check, args):
        current = getattr(sound, attr)
        err_msg = f"Error checking {attr} (expected: {arg}, current: {current})"
        assert current == arg, err_msg


def test_tv_project_header_info_get(test_project: george.TVPProject) -> None:
    assert george.tv_project_header_info_get(test_project.id) == ""


def test_tv_project_header_info_get_wrong_id(test_project: george.TVPProject) -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_project_header_info_get("ll")


@pytest.mark.parametrize("header", ["", "Hello", "This is a project header", "This is a project \nheader"])
def test_tv_project_header_info_set(test_project: george.TVPProject, header: str) -> None:
    george.tv_project_header_info_set(test_project.id, header)
    assert george.tv_project_header_info_get(test_project.id) == header


def test_tv_project_header_info_set_wrong_id(test_project: george.TVPProject) -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_project_header_info_set("ll", "header")


def test_tv_project_header_author_get(test_project: george.TVPProject) -> None:
    import getpass

    assert george.tv_project_header_author_get(test_project.id) == getpass.getuser()


def test_tv_project_header_author_get_wrong_id(test_project: george.TVPProject) -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_project_header_author_get("ll")


@pytest.mark.parametrize("author", ["l", "Hello", "This is a project author", "This is a project \nauthor"])
def test_tv_project_header_author_set(test_project: george.TVPProject, author: str) -> None:
    george.tv_project_header_author_set(test_project.id, author)
    assert george.tv_project_header_author_get(test_project.id) == author


def test_tv_project_header_author_set_wrong_id(test_project: george.TVPProject) -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_project_header_author_set("ll", "header")


def test_tv_project_header_notes_get(test_project: george.TVPProject) -> None:
    assert george.tv_project_header_notes_get(test_project.id) == ""


def test_tv_project_header_notes_get_wrong_id(test_project: george.TVPProject) -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_project_header_notes_get("ll")


@pytest.mark.parametrize("notes", ["l", "Hello", "This is a project note", r"This is a project \nnote"])
def test_tv_project_header_notes_set(test_project: george.TVPProject, notes: str) -> None:
    george.tv_project_header_notes_set(test_project.id, notes)
    assert george.tv_project_header_notes_get(test_project.id) == notes


def test_tv_project_header_notes_set_wrong_id(test_project: george.TVPProject) -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_project_header_notes_set("ll", "header")


def test_tv_start_frame_get(test_project: george.TVPProject) -> None:
    george.tv_start_frame_set(12)
    assert george.tv_start_frame_get() == 12


@pytest.mark.parametrize("start", [0, 1, 50, 100])
def test_tv_start_frame_set(test_project: george.TVPProject, start: int) -> None:
    george.tv_start_frame_set(start)
    assert george.tv_start_frame_get() == start
