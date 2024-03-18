from __future__ import annotations

import struct
import wave
from collections.abc import Generator
from pathlib import Path
from random import randint
from typing import TypeVar

import pytest

from pytvpaint.clip import Clip
from pytvpaint.george.grg_base import tv_pen_brush_set
from pytvpaint.george.grg_clip import (
    TVPClip,
    tv_clip_close,
    tv_clip_current_id,
    tv_clip_enum_id,
    tv_clip_info,
    tv_clip_new,
    tv_sound_clip_new,
)
from pytvpaint.george.grg_layer import (
    TVPLayer,
    tv_layer_anim,
    tv_layer_create,
    tv_layer_get_id,
    tv_layer_info,
    tv_layer_kill,
)
from pytvpaint.george.grg_project import (
    TVPProject,
    tv_project_close,
    tv_project_current_id,
    tv_project_enum_id,
    tv_project_info,
    tv_project_new,
    tv_sound_project_new,
)
from pytvpaint.george.grg_scene import (
    tv_scene_close,
    tv_scene_current_id,
    tv_scene_enum_id,
    tv_scene_new,
)
from pytvpaint.layer import Layer
from pytvpaint.project import Project
from pytvpaint.scene import Scene
from pytvpaint.sound import ClipSound, ProjectSound

T = TypeVar("T")
FixtureYield = Generator[T, None, None]


@pytest.fixture(scope="function")
def pen_brush_reset() -> FixtureYield[None]:
    """Resets the pen brush after the test"""
    yield
    tv_pen_brush_set(reset=True)


@pytest.fixture
def test_project(tmp_path: Path) -> FixtureYield[TVPProject]:
    """
    Fixture to create an empty project and remove it after
    Useful when you want to isolate a test
    """
    project_id = tv_project_new(tmp_path / "project.tvpp")
    yield tv_project_info(project_id)
    tv_project_close(project_id)


@pytest.fixture
def test_project_obj(test_project: TVPProject) -> FixtureYield[Project]:
    yield Project(test_project.id)


@pytest.fixture
def cleanup_current_project() -> FixtureYield[None]:
    yield
    tv_project_close(tv_project_current_id())


@pytest.fixture
def test_layer() -> FixtureYield[TVPLayer]:
    """Temporary layer for testing"""
    layer = tv_layer_create("test")
    yield tv_layer_info(layer)
    tv_layer_kill(layer)


@pytest.fixture
def test_layer_obj(test_clip_obj: Clip, test_layer: TVPLayer) -> FixtureYield[Layer]:
    """Temporary layer object for testing"""
    yield Layer(test_layer.id, test_clip_obj)


@pytest.fixture
def test_anim_layer_obj(test_layer_obj: Layer) -> FixtureYield[Layer]:
    """Temporary anim layer object for testing"""
    test_layer_obj.convert_to_anim_layer()
    yield test_layer_obj


@pytest.fixture
def test_anim_layer(test_layer: TVPLayer) -> FixtureYield[TVPLayer]:
    """Temporary anim layer for testing"""
    tv_layer_anim(test_layer.id)
    yield test_layer


@pytest.fixture
def test_clip() -> FixtureYield[TVPClip]:
    """Temporary clip for testing"""
    tv_clip_new("test")
    clip = tv_clip_current_id()
    yield tv_clip_info(clip)
    tv_clip_close(clip)


@pytest.fixture
def test_clip_obj(test_project_obj: Project, test_clip: TVPClip) -> FixtureYield[Clip]:
    """Temporary clip object for testing"""
    yield Clip(test_clip.id, test_project_obj)


@pytest.fixture
def test_scene() -> FixtureYield[int]:
    """Temporary scene for testing"""
    tv_scene_new()
    scene = tv_scene_current_id()
    yield scene
    tv_scene_close(scene)


@pytest.fixture
def test_scene_obj(test_project_obj: Project, test_scene: int) -> FixtureYield[Scene]:
    """Temporary scene object for testing"""
    yield Scene(test_scene, test_project_obj)


def ppm_generate(path: Path, width: int, height: int, levels: int = 255) -> None:
    """
    Generates an ASCII PPM image file with random gray level pixels
    See: https://fr.wikipedia.org/wiki/Portable_pixmap
    """

    with path.open("w") as ppm:
        ppm.writelines(["P2\n", f"{width} {height}\n", f"{levels}\n"])
        for _ in range(height):
            pixels = (randint(0, levels) for _ in range(width))
            row = " ".join(map(str, pixels))
            ppm.write(f"{row}\n")


@pytest.fixture(scope="session")
def ppm_sequence(tmp_path_factory: pytest.TempPathFactory) -> FixtureYield[list[Path]]:
    """
    Session scoped fixture to get a sequence of generated PPM images
    """
    images_dir = tmp_path_factory.mktemp("images")
    images: list[Path] = []

    for i in range(5):
        ppm = images_dir / f"image.{str(i + 1).zfill(3)}.ppm"
        ppm_generate(ppm, 200, 200)
        images.append(ppm)

    yield images


@pytest.fixture(scope="session")
def wav_file(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a test WAV sound file with random data"""
    sounds_dir = tmp_path_factory.mktemp("sounds")
    import uuid

    wav_path = sounds_dir / f"{uuid.uuid4()}.wav"

    framerate = 44100  # Hertz
    duration = 5  # seconds
    amp_width = 2
    n_frames = framerate * duration
    max_amp = 2 ** (amp_width * 8 - 1) - 1

    wav = wave.open(str(wav_path), "wb")
    wav.setnchannels(1)
    wav.setsampwidth(amp_width)
    wav.setframerate(framerate)

    for _ in range(n_frames):
        value = randint(-max_amp, max_amp)
        data = struct.pack("<h", value)
        wav.writeframesraw(data)

    wav.close()

    return wav_path


@pytest.fixture
def create_some_projects(tmp_path: Path) -> FixtureYield[list[Project]]:
    """Create some projects in a test project and yields them"""
    projects: list[Project] = []

    for i in range(5):
        p_id = tv_project_new(tmp_path / f"project_{i}.tvpp")
        projects.append(Project(p_id))

    # Remove the default project
    tv_project_close(tv_project_enum_id(0))

    yield projects

    for project in projects:
        if not project.is_closed:
            tv_project_close(project.id)


@pytest.fixture
def create_some_scenes(test_project_obj: Project) -> FixtureYield[list[Scene]]:
    """Create some scenes in a test project and yields them"""
    scenes: list[Scene] = []

    for i in range(5):
        tv_scene_new()
        scene_id = tv_scene_enum_id(i + 1)
        scenes.append(Scene(scene_id, test_project_obj))

    # Remove the default scene
    tv_scene_close(tv_scene_enum_id(0))

    yield scenes


@pytest.fixture
def create_some_clips(
    test_project_obj: Project,
) -> FixtureYield[list[Clip]]:
    """Create some clips in a test project/scene and yields them"""
    scene = test_project_obj.current_scene
    clips: list[Clip] = []

    for i in range(5):
        tv_clip_new(f"clip_{i}")
        clip_id = tv_clip_enum_id(scene.id, i + 1)
        clips.append(Clip(clip_id, test_project_obj))

    # Remove the default clip
    tv_clip_close(tv_clip_enum_id(scene.id, 0))

    yield clips


@pytest.fixture
def create_some_layers(
    test_project_obj: Project,
    test_clip_obj: Clip,
) -> FixtureYield[list[Layer]]:
    """Create some layers in a test project/scene and yields them"""
    layers: list[Layer] = []

    for i in range(5):
        tv_layer_create(f"layer_{i}")
        layer_id = tv_layer_get_id(i + 1)
        layers.append(Layer(layer_id, test_clip_obj))

    # Remove the default clip
    tv_layer_kill(tv_layer_get_id(0))

    yield layers


@pytest.fixture
def test_project_sound(
    test_project_obj: Project, wav_file: Path
) -> FixtureYield[ProjectSound]:
    tv_sound_project_new(wav_file)
    yield ProjectSound(0, test_project_obj)


@pytest.fixture
def test_clip_sound(test_clip_obj: Clip, wav_file: Path) -> FixtureYield[ClipSound]:
    tv_sound_clip_new(wav_file)
    yield ClipSound(0, test_clip_obj)


@pytest.fixture
def create_some_project_sounds(
    test_project_obj: Project, wav_file: Path
) -> FixtureYield[list[ProjectSound]]:
    sounds: list[ProjectSound] = []

    for i in range(5):
        tv_sound_project_new(wav_file)
        sounds.append(ProjectSound(i, test_project_obj))

    yield sounds


@pytest.fixture
def with_loaded_sequence(
    test_clip_obj: Clip, ppm_sequence: list[Path]
) -> FixtureYield[Layer]:
    yield test_clip_obj.load_media(
        ppm_sequence[0],
        with_name="images",
        stretch=False,
        pre_load=True,
    )
