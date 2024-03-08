from __future__ import annotations

import random
from pathlib import Path

import pytest
from pytvpaint import george
from pytvpaint import Clip
from pytvpaint.george import RGBColor
from pytvpaint.layer import Layer
from pytvpaint.project import Project
from pytvpaint.scene import Scene

from tests.conftest import FixtureYield
from tests.george.test_grg_clip import TEST_TEXTS


def test_clip_init(test_project_obj: Project, test_clip_obj: Clip) -> None:
    assert Clip(test_clip_obj.id, test_project_obj) == test_clip_obj


def test_clip_refresh(test_clip_obj: Clip) -> None:
    test_clip_obj.refresh()

    test_clip_obj.remove()

    with pytest.raises(ValueError):
        test_clip_obj.refresh()


def test_clip_is_current(test_clip_obj: Clip, create_some_clips: list[Clip]) -> None:
    assert not test_clip_obj.is_current
    test_clip_obj.make_current()
    assert test_clip_obj.is_current


def test_clip_scene(test_scene_obj: Scene, test_clip_obj: Clip) -> None:
    assert test_clip_obj.scene == test_scene_obj


def test_clip_scene_set(create_some_scenes: list[Scene], test_clip_obj: Clip) -> None:
    for scene in create_some_scenes:
        test_clip_obj.scene = scene
        assert test_clip_obj.scene == scene


def test_clip_camera(test_clip_obj: Clip) -> None:
    assert test_clip_obj.camera


def test_clip_position(create_some_clips: list[Clip]) -> None:
    clip = Clip.current_clip()

    for i in range(5):
        clip.position = i
        assert clip.position == i


@pytest.mark.parametrize("name", ["l", "0o", "hello world", "_dP-"])
def test_clip_name(test_clip_obj: Clip, name: str) -> None:
    test_clip_obj.name = name
    assert test_clip_obj.name == name


def test_clip_start(test_project_obj: Project, test_clip_obj: Clip) -> None:
    test_project_obj.start_frame = 5
    assert test_clip_obj.start == 0 + test_project_obj.start_frame


def test_clip_end(test_project_obj: Project, test_clip_obj: Clip) -> None:
    start_frame = 5
    end_frame = 12
    test_project_obj.start_frame = start_frame

    george.tv_layer_copy()
    george.tv_project_current_frame_set(end_frame - start_frame + 1)
    george.tv_layer_paste()

    assert test_clip_obj.end == end_frame


def test_clip_frame_count(test_clip_obj: Clip) -> None:
    assert test_clip_obj.frame_count == 1
    george.tv_layer_insert_image(25, george.InsertDirection.AFTER)
    assert test_clip_obj.frame_count == 26


@pytest.mark.parametrize("index", range(5))
def test_clip_is_selected(create_some_clips: list[Clip], index: int) -> None:
    clip = create_some_clips[index]
    clip.is_selected = True

    assert clip.is_selected
    assert all(not c.is_selected for c in create_some_clips if c != clip)


@pytest.mark.parametrize("index", range(5))
def test_clip_is_visible(create_some_clips: list[Clip], index: int) -> None:
    clip = create_some_clips[index]
    clip.is_visible = False

    assert not clip.is_visible
    assert all(c.is_visible for c in create_some_clips if c != clip)


def test_clip_clear_background(test_clip_obj: Clip) -> None:
    test_clip_obj.clear_background()
    assert test_clip_obj.background is None


@pytest.mark.parametrize(
    "color",
    [
        RGBColor(0, 255, 0),
        RGBColor(255, 255, 0),
        RGBColor(0, 255, 255),
    ],
)
def test_clip_set_background_solid_color(test_clip_obj: Clip, color: RGBColor) -> None:
    test_clip_obj.set_background_solid_color(color)
    assert test_clip_obj.background == color


@pytest.mark.parametrize(
    "colors",
    [
        (RGBColor(255, 255, 255), RGBColor(0, 0, 0)),
        (RGBColor(0, 255, 0), RGBColor(0, 255, 255)),
    ],
)
def test_clip_set_background_checker_colors(
    test_clip_obj: Clip, colors: tuple[RGBColor, RGBColor]
) -> None:
    test_clip_obj.set_background_checker_colors(*colors)
    assert test_clip_obj.background == colors


@pytest.mark.parametrize("index", range(26))
def test_clip_color_index(test_clip_obj: Clip, index: int) -> None:
    test_clip_obj.color_index = index
    assert test_clip_obj.color_index == index


@pytest.mark.parametrize("text", [TEST_TEXTS[-1]])
def test_clip_action_text(test_clip_obj: Clip, text: str) -> None:
    test_clip_obj.action_text = text
    assert test_clip_obj.action_text == text


@pytest.mark.parametrize("text", TEST_TEXTS)
def test_clip_dialog_text(test_clip_obj: Clip, text: str) -> None:
    test_clip_obj.dialog_text = text
    assert test_clip_obj.dialog_text == text


@pytest.mark.parametrize("text", TEST_TEXTS)
def test_clip_note_text(test_clip_obj: Clip, text: str) -> None:
    test_clip_obj.note_text = text
    assert test_clip_obj.note_text == text


def test_clip_current_id(test_clip_obj: Clip) -> None:
    assert Clip.current_clip_id() == test_clip_obj.id


def test_clip_current_clip(test_clip_obj: Clip) -> None:
    assert Clip.current_clip() == test_clip_obj


@pytest.mark.parametrize("frame", range(0, 10, 2))
def test_clip_current_frame(test_clip_obj: Clip, frame: int) -> None:
    test_clip_obj.project.start_frame = 5
    test_clip_obj.current_frame = frame
    assert test_clip_obj.current_frame == frame


@pytest.mark.parametrize("name", ["d", "un clip", "tset0"])
def test_clip_new(test_project_obj: Project, name: str) -> None:
    clip = Clip.new(name)
    assert clip.name == name


def test_clip_new_unique_name(test_project_obj: Project) -> None:
    Clip.new("test")
    assert Clip.new("test").name == "test2"


def test_clip_new_other_scene(test_project_obj: Project) -> None:
    first_scene = test_project_obj.current_scene
    other_scene = test_project_obj.add_scene()

    first_scene.make_current()

    new_clip = Clip.new("hello", scene=other_scene)
    assert new_clip.scene == other_scene


def test_clip_duplicate(test_project_obj: Project) -> None:
    clip = Clip.new("test")
    dup = clip.duplicate()
    assert dup.name == "test2"


def test_clip_remove(test_project_obj: Project) -> None:
    clip = Clip.new("cl")
    clip.remove()

    with pytest.raises(ValueError, match="Clip has been removed"):
        clip.name = "other"


def test_clip_layer_ids(test_clip_obj: Clip, create_some_layers: list[Layer]) -> None:
    assert list(test_clip_obj.layer_ids) == [layer.id for layer in create_some_layers]


def test_clip_layers(test_clip_obj: Clip, create_some_layers: list[Layer]) -> None:
    assert list(test_clip_obj.layers) == create_some_layers


def test_clip_current_layer(test_clip_obj: Clip, test_layer_obj: Layer) -> None:
    assert test_clip_obj.current_layer == test_layer_obj


def test_clip_add_layer(test_clip_obj: Clip) -> None:
    layer = test_clip_obj.add_layer("test")
    assert test_clip_obj.current_layer == layer


def test_clip_selected_layers(
    test_clip_obj: Clip, create_some_layers: list[Layer]
) -> None:
    layer = create_some_layers[0]
    layer.is_selected = True
    assert list(test_clip_obj.selected_layers) == [layer]


def test_clip_visible_layers(
    test_clip_obj: Clip, create_some_layers: list[Layer]
) -> None:
    layer = create_some_layers[0]
    layer.is_visible = False
    assert list(test_clip_obj.visible_layers) == create_some_layers[1:]


def test_clip_load_media(test_clip_obj: Clip, ppm_sequence: list[Path]) -> None:
    layer = test_clip_obj.load_media(ppm_sequence[0], with_name="images")
    assert layer.name == "images"


def test_clip_render(
    test_clip_obj: Clip,
    with_loaded_sequence: Layer,
    tmp_path: Path,
) -> None:
    test_clip_obj.render(tmp_path / "render.png", start=1, end=1)


@pytest.mark.parametrize(
    "args",
    [
        ("render.#.png", None, None),
        ("render.1-5#.png", None, None),
        ("render.1-5#.png", 2, 7),
    ],
)
def test_clip_render_sequence(
    test_clip_obj: Clip,
    with_loaded_sequence: Layer,
    tmp_path: Path,
    args: tuple[str, int | None, int | None],
) -> None:
    out, start, end = args
    test_clip_obj.render(tmp_path / out, start, end)


def test_clip_render_mp4(
    test_clip_obj: Clip,
    with_loaded_sequence: Layer,
    tmp_path: Path,
) -> None:
    test_clip_obj.render(tmp_path / "render.001.mp4")


def test_export_tvp(
    test_project_obj: Project,
    test_clip_obj: Clip,
    with_loaded_sequence: Layer,
    tmp_path: Path,
) -> None:
    out_tvp = tmp_path / "out.tvp"
    test_clip_obj.export_tvp(out_tvp)

    assert out_tvp.exists()

    loaded = test_project_obj.load(out_tvp)
    loaded.close()


def test_clip_export_json(
    test_clip_obj: Clip, tmp_path: Path, with_loaded_sequence: Layer
) -> None:
    out_json = tmp_path / "out.json"

    test_clip_obj.export_json(
        out_json,
        george.SaveFormat.PNG,
        alpha_mode=george.AlphaSaveMode.NO_ALPHA,
    )

    assert out_json.exists()


def test_clip_export_psd(
    test_clip_obj: Clip,
    tmp_path: Path,
    with_loaded_sequence: Layer,
) -> None:
    out_psd = tmp_path / "out.psd"
    test_clip_obj.export_psd(out_psd, mode=george.PSDSaveMode.ALL)
    assert out_psd.exists()


def test_clip_export_csv(
    test_clip_obj: Clip,
    tmp_path: Path,
    with_loaded_sequence: Layer,
) -> None:
    out_csv = tmp_path / "out.csv"
    test_clip_obj.export_csv(out_csv, george.SaveFormat.JPG)
    assert out_csv.exists()


def test_clip_export_sprites(
    test_clip_obj: Clip,
    tmp_path: Path,
    with_loaded_sequence: Layer,
) -> None:
    out_sprite = tmp_path / "out.png"
    test_clip_obj.export_sprites(out_sprite)
    assert out_sprite.exists()


def test_clip_export_flix(
    test_clip_obj: Clip,
    tmp_path: Path,
    with_loaded_sequence: Layer,
) -> None:
    out_flix = tmp_path / "out.xml"
    test_clip_obj.export_flix(out_flix)
    assert out_flix.exists()


@pytest.mark.parametrize("mark_in", [None, 1, 10, 50, 100])
def test_clip_mark_in(test_clip_obj: Clip, mark_in: int | None) -> None:
    test_clip_obj.mark_in = mark_in
    assert test_clip_obj.mark_in == mark_in


@pytest.mark.parametrize("mark_out", [None, 5, 10, 50, 100])
def test_clip_mark_out(
    test_project_obj: Project, test_clip_obj: Clip, mark_out: int | None
) -> None:
    test_project_obj.start_frame = 5

    test_clip_obj.mark_out = mark_out
    assert test_clip_obj.mark_out == mark_out


def test_clip_layer_colors(test_clip_obj: Clip) -> None:
    assert list(test_clip_obj.layer_colors)


@pytest.fixture
def random_color() -> RGBColor:
    return RGBColor(
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
    )


@pytest.mark.parametrize("index", range(1, 26))
def test_clip_set_layer_color(
    test_clip_obj: Clip, index: int, random_color: RGBColor
) -> None:
    test_clip_obj.set_layer_color(index, random_color, "test")
    result = test_clip_obj.get_layer_color(by_index=index)
    assert result.name == "test"
    assert result.color == random_color


@pytest.fixture
def create_some_bookmarks(test_clip_obj: Clip) -> FixtureYield[list[int]]:
    bookmarks = [1, 50, 20, 34]
    for mark in bookmarks:
        test_clip_obj.add_bookmark(mark)
    yield sorted(bookmarks)


def test_clip_bookmarks(test_clip_obj: Clip, create_some_bookmarks: list[int]) -> None:
    assert list(test_clip_obj.bookmarks) == create_some_bookmarks


@pytest.mark.parametrize("mark", [1, 20, 50])
def test_clip_add_bookmark(test_clip_obj: Clip, mark: int) -> None:
    test_clip_obj.add_bookmark(mark)
    assert list(test_clip_obj.bookmarks) == [mark]


@pytest.mark.parametrize("mark", [1, 20, 50])
def test_clip_remove_bookmark(test_clip_obj: Clip, mark: int) -> None:
    test_clip_obj.add_bookmark(mark)
    test_clip_obj.remove_bookmark(mark)
    assert list(test_clip_obj.bookmarks) == []


def test_clip_clear_bookmarks(
    test_clip_obj: Clip, create_some_bookmarks: list[int]
) -> None:
    test_clip_obj.clear_bookmarks()
    assert list(test_clip_obj.bookmarks) == []


def test_clip_go_to_previous_bookmark(
    test_clip_obj: Clip, create_some_bookmarks: list[int]
) -> None:
    for mark in reversed(create_some_bookmarks):
        test_clip_obj.go_to_previous_bookmark()
        assert test_clip_obj.current_frame == mark


def test_clip_go_to_next_bookmark(
    test_clip_obj: Clip, create_some_bookmarks: list[int]
) -> None:
    test_clip_obj.current_frame = 0

    for mark in create_some_bookmarks:
        test_clip_obj.go_to_next_bookmark()
        assert test_clip_obj.current_frame == mark


def test_clip_sounds(test_clip_obj: Clip, wav_file: Path) -> None:
    sound = test_clip_obj.add_sound(wav_file)
    assert list(test_clip_obj.sounds) == [sound]
