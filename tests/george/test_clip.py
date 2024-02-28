from __future__ import annotations

import itertools
import re
from pathlib import Path
from typing import Any, Iterable, Iterator

import pytest
from pytvpaint.george.base import FieldOrder, SaveFormat, SpriteLayout, tv_save_mode_get
from pytvpaint.george.clip import (
    PSDSaveMode,
    TVPClip,
    tv_bookmark_clear,
    tv_bookmark_next,
    tv_bookmark_prev,
    tv_bookmark_set,
    tv_bookmarks_enum,
    tv_clip_action_get,
    tv_clip_action_set,
    tv_clip_close,
    tv_clip_color_get,
    tv_clip_color_set,
    tv_clip_current_id,
    tv_clip_dialog_get,
    tv_clip_dialog_set,
    tv_clip_duplicate,
    tv_clip_enum_id,
    tv_clip_hidden_get,
    tv_clip_hidden_set,
    tv_clip_info,
    tv_clip_move,
    tv_clip_name_get,
    tv_clip_name_set,
    tv_clip_new,
    tv_clip_note_get,
    tv_clip_note_set,
    tv_clip_save_structure_csv,
    tv_clip_save_structure_flix,
    tv_clip_save_structure_json,
    tv_clip_save_structure_psd,
    tv_clip_save_structure_sprite,
    tv_clip_select,
    tv_clip_selection_get,
    tv_clip_selection_set,
    tv_first_image,
    tv_last_image,
    tv_layer_image,
    tv_layer_image_get,
    tv_load_image,
    tv_load_sequence,
    tv_save_clip,
    tv_save_display,
    tv_save_image,
    tv_sound_clip_adjust,
    tv_sound_clip_info,
    tv_sound_clip_new,
    tv_sound_clip_reload,
    tv_sound_clip_remove,
)
from pytvpaint.george.exceptions import GeorgeError, NoObjectWithIdError
from pytvpaint.george.layer import (
    LayerType,
    TVPLayer,
    tv_instance_get_name,
    tv_layer_current_id,
    tv_layer_display_set,
    tv_layer_get_id,
    tv_layer_info,
    tv_layer_kill,
    tv_layer_rename,
    tv_layer_set,
)
from pytvpaint.george.project import TVPProject, tv_save_project
from pytvpaint.george.scene import tv_scene_current_id, tv_scene_new

from tests.conftest import FixtureYield, test_scene


def test_tv_clip_info(test_clip: TVPClip) -> None:
    assert tv_clip_info(test_clip.id)


def test_tv_clip_info_wrong_id(test_clip: TVPClip) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_clip_info(-2)


def test_tv_clip_enum_id(test_scene: int) -> None:
    clips: list[int] = []

    for i in range(5):
        tv_clip_new(f"clip_{i}")
        clips.append(tv_clip_current_id())

    for i, clip_id in enumerate(clips):
        # We offset 1 because of default clip
        assert tv_clip_enum_id(test_scene, i + 1) == clip_id


def test_tv_clip_enum_id_wrong_scene_id() -> None:
    with pytest.raises(GeorgeError):
        tv_clip_enum_id(-2, 0)


@pytest.mark.parametrize("pos", [-1, 1, 50])
def test_tv_clip_enum_id_wrong_clip_pos(test_scene: int, pos: int) -> None:
    with pytest.raises(GeorgeError):
        tv_clip_enum_id(test_scene, pos)


def test_tv_clip_current_id() -> None:
    assert tv_clip_current_id()


@pytest.mark.parametrize("name", ["", "a", "0", "lfseflj0", "clip with spaces"])
def test_tv_clip_new(test_scene: int, name: str) -> None:
    tv_clip_new(name)
    assert tv_clip_info(tv_clip_current_id()).name == name


def test_tv_clip_duplicate(test_scene: int, test_clip: TVPClip) -> None:
    tv_clip_duplicate(test_clip.id)
    dup_clip = tv_clip_info(tv_clip_current_id())
    assert dup_clip == test_clip


def test_tv_clip_close(test_clip: TVPClip) -> None:
    tv_clip_close(test_clip.id)
    with pytest.raises(NoObjectWithIdError):
        tv_clip_info(test_clip.id)


def test_tv_clip_name_get(test_clip: TVPClip) -> None:
    assert tv_clip_name_get(test_clip.id) == test_clip.name


def test_tv_clip_name_get_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_clip_name_get(-1)


@pytest.mark.parametrize("name", ["_", "a", "0", "lfseflj0"])
def test_tv_clip_name_set(test_clip: TVPClip, name: str) -> None:
    tv_clip_name_set(test_clip.id, name)
    assert tv_clip_info(test_clip.id).name == name


def test_tv_clip_name_set_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_clip_name_get(-1)


# "Copy" the fixture to use it twice in the above test
# See: https://stackoverflow.com/questions/36100624/pytest-use-same-fixture-twice-in-one-function
destination_scene = test_scene


@pytest.mark.parametrize("new_pos", range(5))
def test_tv_clip_move(
    test_scene: int, test_clip: TVPClip, destination_scene: int, new_pos: int
) -> None:
    for i in range(5):
        tv_clip_new(f"other_clip_{i}")

    tv_clip_move(test_clip.id, destination_scene, new_pos)

    # Ensure that it's not in the first scene
    with pytest.raises(GeorgeError):
        tv_clip_enum_id(test_scene, 1)

    # Ensure that it's at the right position in the other scene
    tv_clip_enum_id(destination_scene, new_pos)


def test_tv_clip_hidden_get(test_clip: TVPClip) -> None:
    assert tv_clip_hidden_get(test_clip.id) == test_clip.is_hidden


def test_tv_clip_hidden_get_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_clip_hidden_get(-1)


@pytest.mark.parametrize("hidden", [True, False])
def test_tv_clip_hidden_set(test_clip: TVPClip, hidden: bool) -> None:
    tv_clip_hidden_set(test_clip.id, hidden)
    assert tv_clip_info(test_clip.id).is_hidden == hidden


@pytest.mark.parametrize("hidden", [True, False])
def test_tv_clip_hidden_set_wrong_id(hidden: bool) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_clip_hidden_set(-1, hidden)


def test_tv_clip_select(test_scene: int, test_clip: TVPClip) -> None:
    first_clip = tv_clip_enum_id(test_scene, 0)
    tv_clip_select(first_clip)

    assert not tv_clip_info(test_clip.id).is_current
    tv_clip_select(test_clip.id)
    assert tv_clip_info(test_clip.id).is_current


def test_tv_clip_select_also_selects_scene(
    test_project: TVPProject,
    test_scene: int,
    test_clip: TVPClip,
) -> None:
    tv_scene_new()
    assert tv_scene_current_id() != test_scene
    tv_clip_select(test_clip.id)
    assert tv_scene_current_id() == test_scene


def test_tv_clip_selection_get(test_clip: TVPClip) -> None:
    assert tv_clip_selection_get(test_clip.id) == test_clip.is_selected


def test_tv_clip_selection_get_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_clip_selection_get(-1)


@pytest.mark.parametrize("select", [True, False])
def test_tv_clip_selection_set(test_clip: TVPClip, select: bool) -> None:
    tv_clip_selection_set(test_clip.id, select)
    assert tv_clip_info(test_clip.id).is_selected == select


@pytest.mark.parametrize("select", [True, False])
def test_tv_clip_selection_set_wrong_id(test_clip: TVPClip, select: bool) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_clip_selection_set(-1, select)


def test_tv_first_image(test_clip: TVPClip) -> None:
    assert tv_first_image() == test_clip.first_frame


def test_tv_last_image(test_clip: TVPClip) -> None:
    assert tv_last_image() == test_clip.last_frame


@pytest.mark.parametrize("offset_count", [None, *itertools.product([0, 1], [0, 1])])
@pytest.mark.parametrize("field_order", [None, *FieldOrder])
@pytest.mark.parametrize("stretch", [None, False, True])
@pytest.mark.parametrize("time_stretch", [None, False, True])
@pytest.mark.parametrize("preload", [None, False, True])
def test_tv_load_sequence(
    ppm_sequence: list[Path],
    test_clip: TVPClip,
    offset_count: tuple[int, int] | None,
    field_order: FieldOrder | None,
    stretch: bool | None,
    time_stretch: bool | None,
    preload: bool | None,
) -> None:
    total_images = len(ppm_sequence)
    first_image = ppm_sequence[0]

    images_loaded = tv_load_sequence(
        first_image,
        offset_count,
        field_order,
        stretch,
        time_stretch,
        preload,
    )

    if offset_count:
        offset, count = offset_count
        should_load = total_images if count <= 0 else min(count, total_images - offset)
    else:
        should_load = total_images

    assert should_load == images_loaded

    # Find the extension at the end (including file number)
    ext_match = re.search(r"\d+\.[a-z0-9]+$", str(first_image))
    assert ext_match
    ext_start, _ = ext_match.span()

    layer_name_cut = str(first_image)[:ext_start]

    layer = tv_layer_info(tv_layer_current_id())

    assert layer.name == layer_name_cut
    assert layer.type == LayerType.SEQUENCE
    assert layer.first_frame == 0
    assert layer.last_frame == should_load - 1


def test_tv_load_sequence_sequence_does_not_exist(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="File not found"):
        tv_load_sequence(tmp_path / "file.001.png")


@pytest.fixture
def bookmarks(test_clip: TVPClip) -> FixtureYield[Iterable[int]]:
    n_bookmarks = 5
    for frame in range(n_bookmarks):
        tv_bookmark_set(frame)
    yield range(n_bookmarks)


def test_tv_bookmarks_enum(bookmarks: Iterable[int]) -> None:
    for pos, mark in enumerate(bookmarks):
        assert tv_bookmarks_enum(pos) == mark


@pytest.mark.parametrize("frame", range(5))
def test_tv_bookmark_set(test_clip: TVPClip, frame: int) -> None:
    tv_bookmark_set(frame)
    assert tv_bookmarks_enum(0) == frame


@pytest.mark.parametrize("frame", range(5))
def test_tv_bookmark_clear(test_clip: TVPClip, frame: int) -> None:
    tv_bookmark_set(frame)
    assert tv_bookmarks_enum(0) == frame

    tv_bookmark_clear(frame)

    with pytest.raises(GeorgeError, match="No bookmark"):
        tv_bookmarks_enum(0)


@pytest.mark.parametrize("frame", range(5))
def test_tv_bookmark_next(test_clip: TVPClip, frame: int) -> None:
    tv_bookmark_set(frame)
    tv_bookmark_next()
    assert tv_layer_image_get() == frame


@pytest.mark.parametrize("frame", range(5))
def test_tv_bookmark_prev(test_clip: TVPClip, frame: int) -> None:
    # Set the current image far away
    tv_layer_image(50)

    tv_bookmark_set(frame)
    tv_bookmark_prev()

    assert tv_layer_image_get() == frame


def test_tv_clip_color_get(test_clip: TVPClip) -> None:
    assert tv_clip_color_get(test_clip.id) in range(27)


@pytest.mark.parametrize("color_index", range(27))
def test_tv_clip_color_set(test_clip: TVPClip, color_index: int) -> None:
    tv_clip_color_set(test_clip.id, color_index)
    assert tv_clip_color_get(test_clip.id) == color_index


def test_tv_clip_action_get(test_clip: TVPClip) -> None:
    assert tv_clip_action_get(test_clip.id) == ""


def test_tv_clip_action_get_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_clip_action_get(-3)


TEST_TEXTS = ["", "l", "0", "ab", "a0l", "ap*", "a\nb"]


@pytest.mark.parametrize("text", TEST_TEXTS)
def test_tv_clip_action_set(test_clip: TVPClip, text: str) -> None:
    tv_clip_action_set(test_clip.id, text)
    assert tv_clip_action_get(test_clip.id) == text


def test_tv_clip_action_set_wrong_id() -> None:
    with pytest.raises(GeorgeError):
        tv_clip_action_set(-2, "test")


def test_tv_clip_dialog_get(test_clip: TVPClip) -> None:
    assert tv_clip_dialog_get(test_clip.id) == ""


def test_tv_clip_dialog_get_wrong_id() -> None:
    with pytest.raises(GeorgeError):
        tv_clip_dialog_get(-2)


@pytest.mark.parametrize("text", TEST_TEXTS)
def test_tv_clip_dialog_set(test_clip: TVPClip, text: str) -> None:
    tv_clip_dialog_set(test_clip.id, text)
    assert tv_clip_dialog_get(test_clip.id) == text


def test_tv_clip_dialog_set_wrong_id() -> None:
    with pytest.raises(GeorgeError):
        tv_clip_dialog_set(-2, "test")


def test_tv_clip_note_get(test_clip: TVPClip) -> None:
    assert tv_clip_note_get(test_clip.id) == ""


def test_tv_clip_note_get_wrong_id() -> None:
    with pytest.raises(GeorgeError):
        tv_clip_dialog_get(-2)


@pytest.mark.parametrize("text", TEST_TEXTS)
def test_tv_clip_note_set(test_clip: TVPClip, text: str) -> None:
    tv_clip_note_set(test_clip.id, text)
    assert tv_clip_note_get(test_clip.id) == text


def test_tv_clip_note_set_wrong_id() -> None:
    with pytest.raises(GeorgeError):
        tv_clip_note_set(-2, "test")


def test_tv_save_clip(tmp_path: Path) -> None:
    clip_tvp = tmp_path / "clip.tvp"
    tv_save_clip(clip_tvp)
    assert clip_tvp.exists()


@pytest.mark.skip("Will block the UI")
def test_tv_save_clip_folder_does_not_exist(tmp_path: Path) -> None:
    with pytest.raises(GeorgeError, match="Can't create file"):
        tv_save_clip(tmp_path / "folder" / "out.tvpx")


def test_tv_save_display(tmp_path: Path) -> None:
    save_ext, _ = tv_save_mode_get()
    ext = "jpg" if save_ext == SaveFormat.JPG else save_ext.value
    out_display = (tmp_path / "out").with_suffix("." + ext)
    tv_save_display(out_display)
    assert out_display.exists()


def test_tv_save_image(tmp_path: Path) -> None:
    save_ext, _ = tv_save_mode_get()
    ext = "jpg" if save_ext == SaveFormat.JPG else save_ext.value
    out_img = (tmp_path / "out").with_suffix("." + ext)
    tv_save_image(out_img)
    assert out_img.exists()


@pytest.mark.parametrize("stretch", [False, True])
def test_tv_load_image(
    test_clip: TVPClip,
    test_layer: TVPLayer,
    ppm_sequence: list[Path],
    stretch: bool | None,
) -> None:
    tv_load_image(ppm_sequence[0], stretch)
    # Verify that there's an instance frame
    assert tv_instance_get_name(test_layer.id, 0) == ""


@pytest.mark.skip("Will block the UI")
def test_tv_load_image_file_does_not_exist(tmp_path: Path) -> None:
    with pytest.raises(GeorgeError):
        tv_load_image(tmp_path / "file.png")


def current_clip_layers() -> Iterator[TVPLayer]:
    """Iterates through the current clip layers"""
    pos = 0
    while True:
        try:
            lid = tv_layer_get_id(pos)
            yield tv_layer_info(lid)
        except GeorgeError:
            break
        pos += 1


def get_instance_frames() -> Iterator[tuple[int, str]]:
    """Iterates through the instances of the current layer"""
    layer = tv_layer_current_id()
    frame = 0
    while True:
        try:
            name = tv_instance_get_name(layer, frame)
            yield frame, name
        except NoObjectWithIdError:
            break
        frame += 1


def apply_folder_pattern(initial_pattern: str | None, layer: TVPLayer) -> str:
    # This is the default folder pattern
    if initial_pattern is None:
        return f"[{str(layer.position).zfill(3)}] {layer.name}"

    patterns = {
        r"%li": str(layer.position),
        r"%ln": layer.name,
        r"%fi": r"%fi",  # Couldn't make it work
    }

    for pattern, rep in patterns.items():
        initial_pattern = initial_pattern.replace(pattern, rep)

    return initial_pattern


def apply_file_pattern(
    initial_pattern: str | None,
    layer: TVPLayer,
    image_index: int,
    image_name: str,
    file_index: int,
) -> str:
    # This is the default file pattern
    if initial_pattern is None:
        return f"[{str(image_index).zfill(3)}] {layer.name}"

    # When the instance name is empty it takes the image index
    if image_name == "":
        image_name = str(image_index)

    patterns = {
        r"%li": str(layer.position),
        r"%ln": layer.name,
        r"%ii": str(image_index),
        r"%in": image_name,
        r"%fi": str(file_index),
    }

    for pattern, rep in patterns.items():
        initial_pattern = initial_pattern.replace(pattern, rep)

    return initial_pattern


def load_sequence_with_name(first_frame: Path, name: str, count: int) -> int:
    """Load an image sequence and rename the layer"""
    tv_load_sequence(first_frame, offset_count=(0, count))
    layer = tv_layer_current_id()
    tv_layer_rename(layer, name)
    return layer


@pytest.mark.parametrize(
    "file_format",
    [
        SaveFormat.PNG,
        # SaveFormat.JPG,
        # SaveFormat.BMP,
        # SaveFormat.TGA,
        # SaveFormat.TIFF,
    ],
)
@pytest.mark.parametrize("fill_background", [False, True])
@pytest.mark.parametrize("folder_pattern", [r"folder_%li_%ln_%fi"])
@pytest.mark.parametrize("file_pattern", [r"file_%li_%ln_%ii_%in_%fi"])
@pytest.mark.parametrize("visible_layers_only", [False, True])
@pytest.mark.parametrize("all_images", [False, True])
def test_tv_clip_save_structure_json(
    test_project: TVPProject,
    ppm_sequence: list[Path],
    tmp_path: Path,
    file_format: SaveFormat,
    fill_background: bool | None,
    folder_pattern: str | None,
    file_pattern: str | None,
    visible_layers_only: bool | None,
    all_images: bool | None,
) -> None:
    # Import some frames
    load_sequence_with_name(ppm_sequence[0], name="sequence_1", count=5)
    load_sequence_with_name(ppm_sequence[0], name="sequence_2", count=3)

    # Hide that layer
    seq_3 = load_sequence_with_name(ppm_sequence[0], name="sequence_3", count=3)
    tv_layer_display_set(seq_3, False)

    # Remove the first layer (which is in the last position)
    last_layer = list(current_clip_layers())[-1]
    tv_layer_kill(last_layer.id)

    out_json_path = tmp_path / "clip.json"
    tv_clip_save_structure_json(
        out_json_path,
        file_format,
        fill_background,
        folder_pattern,
        file_pattern,
        visible_layers_only,
        all_images,
    )
    assert out_json_path.exists()

    for layer in current_clip_layers():
        if visible_layers_only and not layer.visibility:
            continue

        # Check that the layer folders exist
        layer_folder_name = apply_folder_pattern(folder_pattern, layer)
        layer_folder = tmp_path / layer_folder_name
        assert layer_folder.exists()

        tv_layer_set(layer.id)
        for i, instance in enumerate(get_instance_frames()):
            frame, name = instance

            image_name = apply_file_pattern(
                file_pattern,
                layer,
                image_index=frame + 1,
                image_name=name,
                file_index=i,
            )

            # Check that the images exist
            ext = "." + file_format.value
            image_path = (layer_folder / image_name).with_suffix(ext)
            assert image_path.exists()


def test_tv_clip_save_structure_json_file_doesnt_exist(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="destination folder doesn't exist"):
        tv_clip_save_structure_json(tmp_path / "folder" / "out.json", SaveFormat.PNG)


@pytest.mark.parametrize(
    "test_case",
    [
        (PSDSaveMode.ALL, {}),
        (PSDSaveMode.IMAGE, {"image": 0}),
        (PSDSaveMode.MARKIN, {"mark_in": 0, "mark_out": 5}),
    ],
)
def test_tv_clip_save_structure_psd(
    test_project: TVPProject,
    ppm_sequence: list[Path],
    tmp_path: Path,
    test_case: tuple[PSDSaveMode, dict[str, Any]],
) -> None:
    out_psd = tmp_path / "out.psd"

    load_sequence_with_name(ppm_sequence[0], name="sequence_1", count=5)
    load_sequence_with_name(ppm_sequence[0], name="sequence_2", count=2)

    mode, args = test_case
    tv_clip_save_structure_psd(out_psd, mode, **args)

    if mode == PSDSaveMode.MARKIN:
        # It's a sequence of numbered PSD files
        for i, _ in enumerate(get_instance_frames()):
            out_psd_frame = out_psd.with_name(
                out_psd.stem + str(i).zfill(5) + out_psd.suffix
            )
            assert out_psd_frame.exists()
    else:
        # It's a single PSD file
        assert out_psd.exists()


def test_tv_tv_clip_save_structure_psd_file_does_not_exist(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="destination folder doesn't exist"):
        tv_clip_save_structure_psd(tmp_path / "folder" / "out.psd", PSDSaveMode.ALL)


@pytest.mark.parametrize("all_images", [None, False, True])
@pytest.mark.parametrize("exposure_label", [None, "", "expo", "ex po"])
def test_tv_clip_save_structure_csv(
    test_project: TVPProject,
    ppm_sequence: list[Path],
    tmp_path: Path,
    all_images: bool | None,
    exposure_label: str | None,
) -> None:
    out_csv = tmp_path / "out.csv"

    load_sequence_with_name(ppm_sequence[0], name="sequence_1", count=5)
    load_sequence_with_name(ppm_sequence[0], name="sequence_2", count=2)

    # Remove the first layer (which is in the last position)
    last_layer = list(current_clip_layers())[-1]
    tv_layer_kill(last_layer.id)

    tv_clip_save_structure_csv(out_csv, all_images, exposure_label)

    assert out_csv.exists()

    out_layers_folder = out_csv.with_suffix(".layers")
    assert out_layers_folder.exists()

    for i, layer in enumerate(current_clip_layers()):
        layer_index = str(i + 1).zfill(3)
        layer_folder_name = f"[{layer_index}] {layer.name}"
        layer_folder = out_layers_folder / layer_folder_name
        assert layer_folder.exists()

        tv_layer_set(layer.id)
        for i, _ in enumerate(get_instance_frames()):
            image_name = f"[{layer_index}][{str(i + 1).zfill(5)}] {layer.name}.png"
            assert (layer_folder / image_name).exists()


@pytest.mark.parametrize("layout", [None, *SpriteLayout])
@pytest.mark.parametrize("space", [None, 0, 5, 50])
def test_tv_clip_save_structure_sprite(
    test_project: TVPProject,
    ppm_sequence: list[Path],
    tmp_path: Path,
    layout: SpriteLayout | None,
    space: int | None,
) -> None:
    load_sequence_with_name(ppm_sequence[0], name="sequence_1", count=5)

    out_sprite = tmp_path / "out.png"
    tv_clip_save_structure_sprite(out_sprite, layout, space)

    assert out_sprite.exists()


@pytest.mark.parametrize("mark_in_out", [None, (0, 0), (0, 5), (2, 5)])
@pytest.mark.parametrize("send", [None, False, True])
def test_tv_clip_save_structure_flix(
    test_project: TVPProject,
    ppm_sequence: list[Path],
    tmp_path: Path,
    mark_in_out: tuple[int, int] | None,
    send: bool | None,
) -> None:
    load_sequence_with_name(ppm_sequence[0], name="sequence_1", count=5)
    load_sequence_with_name(ppm_sequence[0], name="sequence_2", count=3)

    # Export to flix needs to save the project first
    tv_save_project(test_project.path)

    mark_in: int | None
    mark_out: int | None

    if mark_in_out:
        mark_in, mark_out = mark_in_out
    else:
        mark_in = mark_out = None

    out_flix = tmp_path / "out.xml"

    tv_clip_save_structure_flix(out_flix, mark_in, mark_out, send=send)
    assert out_flix.exists()


def test_tv_sound_clip_info(test_clip: TVPClip, wav_file: Path) -> None:
    tv_sound_clip_new(wav_file)
    sound = tv_sound_clip_info(test_clip.id, 0)

    assert sound.sound_in == 0
    assert Path(sound.path) == wav_file


def test_tv_sound_clip_info_wrong_clip_id() -> None:
    with pytest.raises(GeorgeError):
        tv_sound_clip_info(-2, 0)


def test_tv_sound_clip_info_wrong_sound_track_pos(test_clip: TVPClip) -> None:
    with pytest.raises(GeorgeError):
        tv_sound_clip_info(test_clip.id, 1)


def test_tv_sound_clip_new(
    test_project: TVPProject,
    test_clip: TVPClip,
    wav_file: Path,
) -> None:
    for i in range(5):
        tv_sound_clip_new(wav_file)
        assert tv_sound_clip_info(test_clip.id, i)


def test_tv_sound_clip_new_wrong_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        tv_sound_clip_new(tmp_path / "unknown.wav")


def test_tv_sound_clip_remove(test_clip: TVPClip, wav_file: Path) -> None:
    tv_sound_clip_new(wav_file)
    assert tv_sound_clip_info(test_clip.id, 0)
    tv_sound_clip_remove(0)

    with pytest.raises(GeorgeError):
        tv_sound_clip_info(test_clip.id, 0)


def test_tv_sound_clip_remove_wrong_pos() -> None:
    with pytest.raises(GeorgeError):
        tv_sound_clip_remove(1)


@pytest.mark.skip("Super weird because it doesn't accept the clip_id")
def test_tv_sound_clip_reload(test_clip: TVPClip, wav_file: Path) -> None:
    tv_sound_clip_new(wav_file)
    tv_sound_clip_reload(test_clip.id, 0)


def test_tv_sound_clip_reload_wrong_sound_clip_id() -> None:
    with pytest.raises(GeorgeError):
        tv_sound_clip_reload(6, 0)


@pytest.mark.skip("It doesn't behave correctly, see above")
def test_tv_sound_clip_reload_wrong_track_index(test_clip: TVPClip) -> None:
    with pytest.raises(GeorgeError):
        tv_sound_clip_reload(test_clip.id, 5)


def args_optional_combine(args: list[list[Any]]) -> list[list[Any]]:
    return [
        list(prod)
        for n in range(len(args) + 1)
        for prod in itertools.product(*args[:n])
    ]


# TODO: might do that later, fade_ arguments are in block
@pytest.mark.skip("Too difficult to test")
@pytest.mark.parametrize(
    "args",
    args_optional_combine(
        [
            [False, True],  # mute
            [0.0, 1.0, 5.0],  # volume
            [0, 1.0],  # offset
            [5.0],  # fade_in_start
        ]
    ),
)
def test_tv_sound_clip_adjust(
    test_clip: TVPClip, wav_file: Path, args: list[Any]
) -> None:
    tv_sound_clip_new(wav_file)
    track_index = 0

    tv_sound_clip_adjust(track_index, *args)

    sound_clip = tv_sound_clip_info(test_clip.id, track_index)

    real_values = [
        sound_clip.mute,
        sound_clip.volume,
        sound_clip.offset,
        sound_clip.fade_in_start,
        sound_clip.fade_in_stop,
        sound_clip.fade_out_start,
        sound_clip.fade_out_stop,
        sound_clip.color_index,
    ]

    for real, expected in zip(real_values, args):
        assert real == expected


def test_tv_layer_image_get(test_project: TVPLayer) -> None:
    assert tv_layer_image_get() == 0


@pytest.mark.parametrize("frame", range(10))
def test_tv_layer_image(frame: int) -> None:
    tv_layer_image(frame)
    assert tv_layer_image_get() == frame
