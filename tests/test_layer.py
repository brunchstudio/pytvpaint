from __future__ import annotations

from pathlib import Path

import pytest

from pytvpaint import george
from pytvpaint.clip import Clip
from pytvpaint.george import BlendingMode, StencilMode
from pytvpaint.george.grg_layer import (
    LayerBehavior,
    LayerTransparency,
    LayerType,
    TVPLayer,
)
from pytvpaint.layer import Layer, LayerColor, LayerInstance
from pytvpaint.project import Project
from pytvpaint.scene import Scene
from tests.conftest import FixtureYield


def test_layer_init(test_layer_obj: Layer) -> None:
    assert Layer(test_layer_obj.id) == test_layer_obj


def test_layer_refresh(test_layer_obj: Layer) -> None:
    test_layer_obj.refresh()


def test_layer_attributes(
    test_project_obj: Project,
    test_scene_obj: Scene,
    test_clip_obj: Clip,
    test_layer_obj: Layer,
) -> None:
    assert test_layer_obj.id

    assert test_layer_obj.project == test_project_obj
    assert test_layer_obj.scene == test_scene_obj
    assert test_layer_obj.clip == test_clip_obj

    assert test_layer_obj.layer_type


@pytest.mark.parametrize("position", range(5))
def test_layer_position(
    test_layer_obj: Layer,
    create_some_layers: None,
    position: int,
) -> None:
    test_layer_obj.position = position
    assert test_layer_obj.position == position


@pytest.mark.parametrize("name", ["l", "a n", "a0", "8 _d"])
def test_layer_name(test_layer_obj: Layer, name: str) -> None:
    test_layer_obj.name = name
    assert test_layer_obj.name == name


@pytest.mark.parametrize("opacity", [1, 50, 24, 100])
def test_layer_opacity(test_layer_obj: Layer, opacity: int) -> None:
    test_layer_obj.opacity = opacity
    assert test_layer_obj.opacity == opacity


def test_layer_start(test_layer_obj: Layer) -> None:
    test_layer_obj.start


def test_layer_end(test_layer_obj: Layer) -> None:
    test_layer_obj.end


@pytest.mark.parametrize("color_index", range(1, 26, 4))
def test_layer_color(test_layer_obj: Layer, color_index: int) -> None:
    color = LayerColor(color_index)
    test_layer_obj.color = color
    assert test_layer_obj.color == color


def test_layer_is_current(
    test_layer_obj: Layer,
    create_some_layers: list[Layer],
) -> None:
    assert not test_layer_obj.is_current

    test_layer_obj.make_current()
    assert test_layer_obj.is_current


def test_layer_is_selected(test_layer_obj: Layer) -> None:
    assert not test_layer_obj.is_selected

    test_layer_obj.is_selected = True
    assert test_layer_obj.is_selected

    test_layer_obj.is_selected = False
    assert not test_layer_obj.is_selected


def test_layer_is_visible(test_layer_obj: Layer) -> None:
    assert test_layer_obj.is_visible

    test_layer_obj.is_visible = False
    assert not test_layer_obj.is_visible

    test_layer_obj.is_visible = True
    assert test_layer_obj.is_visible


def test_layer_is_locked(test_layer_obj: Layer) -> None:
    assert not test_layer_obj.is_locked

    test_layer_obj.is_locked = True
    assert test_layer_obj.is_locked

    test_layer_obj.is_locked = False
    assert not test_layer_obj.is_locked


def test_layer_is_collapsed(test_layer_obj: Layer) -> None:
    assert not test_layer_obj.is_collapsed

    test_layer_obj.is_collapsed = True
    assert test_layer_obj.is_collapsed

    test_layer_obj.is_collapsed = False
    assert not test_layer_obj.is_collapsed


@pytest.mark.parametrize("blending_mode", BlendingMode)
def test_layer_blending_mode(
    test_layer_obj: Layer,
    blending_mode: BlendingMode,
) -> None:
    test_layer_obj.blending_mode = blending_mode
    assert test_layer_obj.blending_mode == blending_mode


@pytest.mark.parametrize("stencil", StencilMode)
def test_layer_stencil(
    test_layer_obj: Layer,
    stencil: StencilMode,
) -> None:
    test_layer_obj.stencil = stencil

    current = test_layer_obj.stencil
    if stencil == StencilMode.ON:
        assert current == StencilMode.NORMAL
    else:
        assert current == stencil


@pytest.mark.parametrize("visible", [False, True])
def test_layer_thumbnails_visible(test_layer_obj: Layer, visible: bool) -> None:
    test_layer_obj.thumbnails_visible = visible
    assert test_layer_obj.thumbnails_visible == visible


@pytest.mark.parametrize("value", [False, True])
def test_layer_auto_break_instance(test_anim_layer_obj: Layer, value: bool) -> None:
    test_anim_layer_obj.auto_break_instance = value
    assert test_anim_layer_obj.auto_break_instance == value


def test_layer_auto_break_instance_not_anim_layer(test_layer_obj: Layer) -> None:
    with pytest.raises(Exception, match="it's not an animation layer"):
        test_layer_obj.auto_break_instance = True


@pytest.mark.parametrize("value", [False, True])
def test_layer_auto_create_instance(test_layer_obj: Layer, value: bool) -> None:
    test_layer_obj.auto_create_instance = value
    assert test_layer_obj.auto_create_instance == value


@pytest.mark.parametrize("behavior", LayerBehavior)
def test_layer_pre_behavior(test_layer_obj: Layer, behavior: LayerBehavior) -> None:
    test_layer_obj.pre_behavior = behavior
    assert test_layer_obj.pre_behavior == behavior


@pytest.mark.parametrize("behavior", LayerBehavior)
def test_layer_post_behavior(test_layer_obj: Layer, behavior: LayerBehavior) -> None:
    test_layer_obj.post_behavior = behavior
    assert test_layer_obj.post_behavior == behavior


@pytest.mark.parametrize("value", [False, True])
def test_layer_is_position_locked(test_layer_obj: Layer, value: bool) -> None:
    test_layer_obj.is_position_locked = value
    assert test_layer_obj.is_position_locked == value


@pytest.mark.parametrize("transparency", LayerTransparency)
def test_layer_preserve_transparency(
    test_layer_obj: Layer, transparency: LayerTransparency
) -> None:
    test_layer_obj.preserve_transparency = transparency

    transparency_map = {
        LayerTransparency.MINUS_1: LayerTransparency.ON,
        LayerTransparency.NONE: LayerTransparency.OFF,
    }

    current = test_layer_obj.preserve_transparency
    assert transparency_map.get(transparency, transparency) == current


def test_layer_convert_to_anim_layer(test_layer_obj: Layer) -> None:
    test_layer_obj.convert_to_anim_layer()
    assert test_layer_obj.layer_type == LayerType.SEQUENCE


def test_layer_load_dependencies(test_layer_obj: Layer) -> None:
    test_layer_obj.load_dependencies()


def test_layer_current_layer_id(test_layer_obj: Layer) -> None:
    assert Layer.current_layer_id() == test_layer_obj.id


def test_layer_current_layer(test_layer_obj: Layer) -> None:
    assert Layer.current_layer() == test_layer_obj


@pytest.mark.parametrize("start", [0, 5, 10])
def test_layer_shift(test_layer_obj: Layer, start: int) -> None:
    test_layer_obj.shift(start)


@pytest.mark.parametrize("name", ["l", "loid", "K4", "k 1"])
@pytest.mark.parametrize("color_index", [None, 5])
def test_layer_new(
    test_clip_obj: Clip,
    name: str,
    color_index: int | None,
) -> None:
    color = LayerColor(color_index) if color_index else None
    layer = Layer.new(name, color=color)
    assert layer.name == name

    if color_index:
        assert layer.color == LayerColor(color_index)


def test_layer_new_anim_layer(test_clip_obj: Clip) -> None:
    layer = Layer.new_anim_layer("anim_layer")
    assert layer.layer_type == LayerType.SEQUENCE
    assert layer.thumbnails_visible


def test_layer_new_background_layer(test_clip_obj: Clip) -> None:
    layer = Layer.new_background_layer("background_layer")
    assert layer.layer_type == LayerType.IMAGE
    assert layer.thumbnails_visible
    assert layer.pre_behavior == LayerBehavior.HOLD
    assert layer.post_behavior == LayerBehavior.HOLD


@pytest.mark.parametrize("name", ["l", "loid", "K4", "k 1"])
def test_layer_duplicate(test_layer_obj: Layer, name: str) -> None:
    dup = test_layer_obj.duplicate(name)
    assert dup.name == name


def test_layer_remove(test_clip_obj: Clip) -> None:
    layer = Layer.new("remove")
    layer.remove()

    with pytest.raises(ValueError, match="Layer has been removed"):
        layer.name = "other"


def test_layer_render_frame(with_loaded_sequence: Layer, tmp_path: Path) -> None:
    with_loaded_sequence.render_frame(tmp_path / "out.jpg", frame=3)


def test_layer_add_mark_not_anim_layer(test_layer_obj: Layer) -> None:
    with pytest.raises(Exception, match="not an animation layer"):
        test_layer_obj.add_mark(0, LayerColor(1))


def test_layer_get_mark_color(test_anim_layer_obj: Layer) -> None:
    test_anim_layer_obj.add_mark(1, LayerColor(6))
    assert test_anim_layer_obj.get_mark_color(1) == LayerColor(color_index=6)


def test_layer_remove_mark(test_anim_layer_obj: Layer) -> None:
    test_anim_layer_obj.add_mark(1, LayerColor(6))
    test_anim_layer_obj.remove_mark(6)
    assert test_anim_layer_obj.get_mark_color(6) is None


Mark = tuple[int, LayerColor]


@pytest.fixture
def with_images(test_layer: TVPLayer) -> FixtureYield[int]:
    images = 5
    george.tv_layer_insert_image(count=images)
    yield images + 1


@pytest.fixture
def add_marks(test_anim_layer_obj: Layer, with_images: int) -> FixtureYield[list[Mark]]:
    marks = [(frame, LayerColor(frame)) for frame in range(1, 7)]

    for frame, color in marks:
        test_anim_layer_obj.add_mark(frame, color)

    yield marks


def test_layer_marks(test_anim_layer_obj: Layer, add_marks: list[Mark]) -> None:
    assert list(test_anim_layer_obj.marks) == add_marks


def test_layer_clear_marks(test_anim_layer_obj: Layer, add_marks: list[Mark]) -> None:
    assert len(list(test_anim_layer_obj.marks)) != 0
    test_anim_layer_obj.clear_marks()
    assert len(list(test_anim_layer_obj.marks)) == 0


def test_layer_select_frames(test_layer_obj: Layer, with_images: int) -> None:
    clip_start = test_layer_obj.clip.start
    test_layer_obj.select_frames(1, with_images)
    assert test_layer_obj.selected_frames == list(
        range(clip_start, with_images + clip_start)
    )


def test_layer_instances(
    test_project_obj: Project, test_anim_layer_obj: Layer, with_images: int
) -> None:
    start_frame = test_project_obj.start_frame
    end_frame = start_frame + with_images
    instances = [
        LayerInstance(test_anim_layer_obj, frame)
        for frame in range(start_frame, end_frame)
    ]

    assert list(test_anim_layer_obj.instances) == instances


def test_layer_rename_instances(test_anim_layer_obj: Layer, with_images: int) -> None:
    test_anim_layer_obj.rename_instances(george.InstanceNamingMode.ALL, prefix="hello_")
    print(list(test_anim_layer_obj.instances))
