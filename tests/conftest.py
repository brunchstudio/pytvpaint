from __future__ import annotations

import struct
import wave
import zlib
from collections.abc import Generator
from pathlib import Path
from random import randint
from typing import TypeVar

import pytest

from pytvpaint import george
from pytvpaint.clip import Clip
from pytvpaint.george.client import send_cmd
from pytvpaint.guideline import GuidelineLine
from pytvpaint.layer import Layer
from pytvpaint.project import Project
from pytvpaint.scene import Scene
from pytvpaint.sound import ClipSound, ProjectSound

T = TypeVar("T")
FixtureYield = Generator[T, None, None]


IS_NOT_TVP12 = not george.tv_version()[1].startswith("12")


def _fix_tvp_12_selection() -> None:
    if IS_NOT_TVP12:
        return

    # if tvp_version >= 12 and current_layer is Camera, then select first real layer instead:
    current_clip = Project.current_project().current_clip
    current_layer = current_clip.current_layer
    if current_layer.layer_type == george.LayerType.CAMERA:
        # switch to first layer in real/non-camera layers
        first_layer = None
        for layer in current_clip.get_layers():
            if layer.layer_type == george.LayerType.CAMERA:
                continue

            first_layer = layer
            break

        if first_layer:
            first_layer.make_current()


@pytest.fixture(scope="function")
def pen_brush_reset() -> FixtureYield[None]:
    """Resets the pen brush after the test"""
    yield
    george.tv_pen_brush_set(reset=True)


@pytest.fixture
def test_project(tmp_path: Path) -> FixtureYield[george.TVPProject]:
    """
    Fixture to create an empty project and remove it after
    Useful when you want to isolate a test
    """
    project_id = george.tv_project_new(tmp_path / "project.tvpp")
    for p_id in Project.open_projects_ids():
        if p_id == project_id:
            continue
        george.tv_project_close(p_id)

    _fix_tvp_12_selection()

    yield george.tv_project_info(project_id)
    george.tv_project_close(project_id)


@pytest.fixture
def test_project_obj(test_project: george.TVPProject) -> FixtureYield[Project]:
    p = Project(test_project.id)
    yield p


@pytest.fixture
def cleanup_current_project() -> FixtureYield[None]:
    yield
    george.tv_project_close(george.tv_project_current_id())


@pytest.fixture
def test_layer() -> FixtureYield[george.TVPLayer]:
    """Temporary layer for testing"""
    layer = george.tv_layer_create("test")
    yield george.tv_layer_info(layer)
    george.tv_layer_kill(layer)


@pytest.fixture
def test_layer_obj(test_clip_obj: Clip, test_layer: george.TVPLayer) -> FixtureYield[Layer]:
    """Temporary layer object for testing"""
    yield Layer(test_layer.id, test_clip_obj)


@pytest.fixture
def test_anim_layer_obj(test_layer_obj: Layer) -> FixtureYield[Layer]:
    """Temporary anim layer object for testing"""
    test_layer_obj.convert_to_anim_layer()
    yield test_layer_obj


@pytest.fixture
def test_anim_layer(test_layer: george.TVPLayer) -> FixtureYield[george.TVPLayer]:
    """Temporary anim layer for testing"""
    george.tv_layer_anim(test_layer.id)
    yield test_layer


@pytest.fixture
def test_clip() -> FixtureYield[george.TVPClip]:
    """Temporary clip for testing"""
    george.tv_clip_new("test")
    clip = george.tv_clip_current_id()
    yield george.tv_clip_info(clip)
    george.tv_clip_close(clip)


@pytest.fixture
def test_clip_obj(test_project_obj: Project, test_clip: george.TVPClip) -> FixtureYield[Clip]:
    """Temporary clip object for testing"""
    yield Clip(test_clip.id, test_project_obj)


@pytest.fixture
def test_scene() -> FixtureYield[int]:
    """Temporary scene for testing"""
    george.tv_scene_new()
    scene = george.tv_scene_current_id()
    yield scene
    george.tv_scene_close(scene)


@pytest.fixture
def test_scene_obj(test_project_obj: Project, test_scene: int) -> FixtureYield[Scene]:
    """Temporary scene object for testing"""
    yield Scene(test_scene, test_project_obj)


@pytest.fixture(name="guideline_pos")
def test_guideline(test_project: george.TVPProject) -> FixtureYield[int]:
    pos = george.tv_guideline_add_line(x=10, y=10, angle=45)
    yield pos


@pytest.fixture
def test_guideline_obj(test_project_obj: Project) -> FixtureYield[GuidelineLine]:
    guideline_obj = GuidelineLine.new(test_project_obj, x=10, y=10, angle=45)
    yield guideline_obj


@pytest.fixture
def count_up_generate(test_clip_obj: Clip) -> None:
    """Create 5 frames with a text in the middle of the screen for each frame. Useful for debugging render tests."""
    text_pos = (
        int(test_clip_obj.project.width / 2),
        int(test_clip_obj.project.height / 2),
    )

    test_clip_obj.current_frame = 1
    test_layer = Layer.new_anim_layer("count_up", test_clip_obj)
    test_layer.make_current()

    for i in range(1, 6):
        if i != 1:
            test_layer.add_instance(i)
        test_clip_obj.current_frame = i

        # write the frame number in the middle of the image
        george.tv_set_a_pen_rgba(george.RGBColor(0, 0, 0), 255)  # set the pen color
        send_cmd("tv_TextTool2", "size", 200)  # set text size
        george.tv_text_brush(str(i))  # set the brush text
        george.tv_set_active_shape(george.TVPShape.FREE_HAND_LINE, size=200)  # set the shape and it's size
        # write a line with the text brush, having the start-end pos being the same will fake a single click
        george.tv_line(text_pos, text_pos)
        # update undo stack otherwise edits to last image are not saved (-_-)"
        george.tv_update_undo()


# 5x7 Bitmap font definition for digits 0-9
FONT_BITMAPS = {
    "0": [" 000 ", "0   0", "0   0", "0   0", "0   0", "0   0", " 000 "],
    "1": ["  1  ", " 11  ", "  1  ", "  1  ", "  1  ", "  1  ", " 111 "],
    "2": [" 222 ", "2   2", "    2", "  22 ", " 2   ", "2    ", "22222"],
    "3": [" 333 ", "3   3", "    3", "  33 ", "    3", "3   3", " 333 "],
    "4": ["   4 ", "  44 ", " 4 4 ", "4  4 ", "44444", "   4 ", "   4 "],
    "5": ["55555", "5    ", "5555 ", "    5", "    5", "5   5", " 555 "],
    "6": [" 666 ", "6    ", "6666 ", "6   6", "6   6", "6   6", " 666 "],
    "7": ["77777", "    7", "   7 ", "  7  ", " 7   ", "7    ", "7    "],
    "8": [" 888 ", "8   8", "8   8", " 888 ", "8   8", "8   8", " 888 "],
    "9": [" 999 ", "9   9", "9   9", " 9999", "    9", "    9", " 999 "],
}


def png_generate_with_index(path: Path, width: int, height: int, index: int) -> None:
    """
    Generates a valid grayscale PNG image file using pure Python.
    Renders the numeric index in the center of the image.
    """
    signature = b"\x89PNG\r\n\x1a\n"

    def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
        length = struct.pack(">I", len(data))
        crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
        return length + chunk_type + data + crc

    # IHDR: Bit depth 8, Color Type 0 (Grayscale)
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    ihdr = make_chunk(b"IHDR", ihdr_data)

    # Initialize canvas with a dark gray background
    row_size = width + 1
    raw_data = bytearray()
    for _ in range(height):
        raw_data.append(0)  # Filter type 0
        raw_data.extend([40] * width)

    # Geometric calculation for text centering
    index_str = str(index)
    scale = 8  # Magnification multiplier for the 5x7 font
    char_w, char_h = 5, 7
    spacing = 1

    total_w = (len(index_str) * char_w + (len(index_str) - 1) * spacing) * scale
    total_h = char_h * scale

    start_x = max(0, (width - total_w) // 2)
    start_y = max(0, (height - total_h) // 2)

    # Rasterize font onto the 1D buffer
    current_x = start_x
    for char in index_str:
        bitmap = FONT_BITMAPS.get(char, FONT_BITMAPS["0"])
        for row_idx, row in enumerate(bitmap):
            for col_idx, pixel in enumerate(row):
                if pixel != " ":
                    # Apply magnification scaling
                    for sy in range(scale):
                        for sx in range(scale):
                            px = current_x + col_idx * scale + sx
                            py = start_y + row_idx * scale + sy

                            # Boundary condition check
                            if 0 <= px < width and 0 <= py < height:
                                # 1D Array Mapping: y * row_width + 1 (filter offset) + x
                                buf_idx = py * row_size + 1 + px
                                raw_data[buf_idx] = 255  # White pixel

        current_x += (char_w + spacing) * scale

    idat_data = zlib.compress(raw_data)
    idat = make_chunk(b"IDAT", idat_data)
    iend = make_chunk(b"IEND", b"")

    with path.open("wb") as f:
        f.write(signature)
        f.write(ihdr)
        f.write(idat)
        f.write(iend)


@pytest.fixture(scope="session")
def png_sequence(tmp_path_factory: pytest.TempPathFactory) -> Generator[list[Path], None, None]:
    """
    Session scoped fixture to get a sequence of generated PNG images.
    """
    images_dir = tmp_path_factory.mktemp("images")
    images: list[Path] = []

    for i in range(5):
        idx = i + 1
        png_path = images_dir / f"image.{idx:03d}.png"
        png_generate_with_index(png_path, 512, 512, idx)
        images.append(png_path)

    yield images


@pytest.fixture(scope="session")
def wav_file(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a test WAV sound file with random data"""
    sounds_dir = Path(tmp_path_factory.mktemp("sounds"))
    import uuid

    wav_path = sounds_dir / f"{uuid.uuid4()}.wav"

    framerate = 44100  # Hertz
    duration = 5  # seconds
    amp_width = 2
    n_frames = framerate * duration
    max_amp = 2 ** (amp_width * 8 - 1) - 1

    with wave.open(str(wav_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(amp_width)
        wav.setframerate(framerate)

        for _ in range(n_frames):
            value = randint(-max_amp, max_amp)
            data = struct.pack("<h", value)
            wav.writeframesraw(data)

    return wav_path


@pytest.fixture
def create_some_projects(tmp_path: Path) -> FixtureYield[list[Project]]:
    """Create some projects in a test project and yields them"""
    Project.close_all()

    projects: list[Project] = []

    for i in range(5):
        p_id = george.tv_project_new(tmp_path / f"project_{i}.tvpp")
        projects.append(Project(p_id))

    # Remove the default project
    george.tv_project_close(george.tv_project_enum_id(0))

    yield projects

    for project in projects:
        if not project.is_closed:
            george.tv_project_close(project.id)


@pytest.fixture
def create_some_scenes(test_project_obj: Project) -> FixtureYield[list[Scene]]:
    """Create some scenes in a test project and yields them"""
    scenes: list[Scene] = []

    for i in range(5):
        george.tv_scene_new()
        scene_id = george.tv_scene_enum_id(i + 1)
        scenes.append(Scene(scene_id, test_project_obj))

    # Remove the default scene
    george.tv_scene_close(george.tv_scene_enum_id(0))

    yield scenes


@pytest.fixture
def create_some_clips(
    test_project_obj: Project,
) -> FixtureYield[list[Clip]]:
    """Create some clips in a test project/scene and yields them"""
    scene = test_project_obj.current_scene
    clips: list[Clip] = []

    for i in range(5):
        george.tv_clip_new(f"clip_{i}")
        clip_id = george.tv_clip_enum_id(scene.id, i + 1)
        clips.append(Clip(clip_id, test_project_obj))

    # Remove the default clip
    george.tv_clip_close(george.tv_clip_enum_id(scene.id, 0))

    yield clips


@pytest.fixture
def create_some_layers(
    test_project_obj: Project,
    test_clip_obj: Clip,
) -> FixtureYield[list[Layer]]:
    """Create some layers in a test project/scene and yields them"""
    layers: list[Layer] = []

    for i in range(5):
        george.tv_layer_create(f"layer_{i}")
        layer_id = george.tv_layer_get_id(i + 1)
        layers.append(Layer(layer_id, test_clip_obj))

    # Remove the default layer
    george.tv_layer_kill(george.tv_layer_get_id(0))

    yield layers


@pytest.fixture
def create_some_layer_folders(
    test_project_obj: Project,
    test_clip_obj: Clip,
) -> FixtureYield[list[Layer]]:
    """Create some layers in a test project/scene and yields them"""
    layers: list[Layer] = []

    for i in range(5):
        george.tv_layer_create(f"layer_{i}", layer_type=0)
        layer_id = george.tv_layer_get_id(i + 1)
        layers.append(Layer(layer_id, test_clip_obj))

    # Remove the default layer
    george.tv_layer_kill(george.tv_layer_get_id(0))

    yield layers


@pytest.fixture
def test_project_sound(test_project_obj: Project, wav_file: Path) -> FixtureYield[ProjectSound]:
    george.tv_sound_project_new(wav_file)
    yield ProjectSound(0, test_project_obj)


@pytest.fixture
def test_clip_sound(test_clip_obj: Clip, wav_file: Path) -> FixtureYield[ClipSound]:
    george.tv_sound_clip_new(wav_file)
    yield ClipSound(0, test_clip_obj)


@pytest.fixture
def create_some_project_sounds(test_project_obj: Project, wav_file: Path) -> FixtureYield[list[ProjectSound]]:
    sounds: list[ProjectSound] = []

    for i in range(5):
        george.tv_sound_project_new(wav_file)
        sounds.append(ProjectSound(i, test_project_obj))

    yield sounds


@pytest.fixture
def with_loaded_sequence(test_clip_obj: Clip, png_sequence: list[Path]) -> FixtureYield[Layer]:
    yield test_clip_obj.load_media(
        png_sequence[0],
        with_name="images",
        stretch=False,
        preload=True,
    )


@pytest.fixture(scope="function", autouse=True)
def fix_tvp_12_selection() -> None:
    _fix_tvp_12_selection()


def load_sequence_with_name(first_frame: Path, name: str, count: int) -> int:
    """Load an image sequence and rename the layer"""
    george.tv_load_sequence(first_frame, offset_count=(0, count))
    layer_id = george.tv_layer_current_id()
    george.tv_layer_rename(layer_id, name)
    return layer_id
