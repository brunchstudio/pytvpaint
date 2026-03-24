from __future__ import annotations

from pathlib import Path

import pytest

from pytvpaint import george
from pytvpaint.layer import Layer
from tests.conftest import FixtureYield

IS_NOT_TVP12 = not george.tv_version()[1].startswith("12")


def _first_layer_id() -> int:
    # fix for tvpaint 12 having the first/current layer in a new project always be the new camera layer
    first_layer_id = george.tv_layer_get_id(0)
    if george.tv_layer_info(first_layer_id).type == george.LayerType.CAMERA:
        first_layer_id = george.tv_layer_get_id(1)

    return first_layer_id


def test_tv_layer_current_id(test_project: george.TVPProject) -> None:
    assert (
        george.tv_layer_current_id()
        and george.tv_layer_info(george.tv_layer_current_id()).type != george.LayerType.CAMERA
    )


def test_tv_layer_get_id(test_project: george.TVPProject) -> None:
    assert _first_layer_id() == george.tv_layer_current_id()


def test_tv_layer_get_id_neg_pos_error(test_project: george.TVPProject) -> None:
    with pytest.raises(george.GeorgeError, match="No layer at provided position"):
        george.tv_layer_get_id(-1)


def test_tv_layer_get_pos(test_project: george.TVPProject) -> None:
    assert george.tv_layer_get_pos(george.tv_layer_current_id()) == george.tv_layer_get_pos(_first_layer_id())


def test_tv_layer_get_pos_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_get_pos(56)


def test_tv_layer_info() -> None:
    info = george.tv_layer_info(george.tv_layer_current_id())
    assert info.id


def test_tv_layer_info_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_info(-4)


def test_tv_layer_move(test_project: george.TVPProject) -> None:
    current_layer = george.tv_layer_current_id()
    total_layers = 10

    for i in range(total_layers):
        george.tv_layer_create(f"layer_{i}")

    # Make the current layer the original one
    george.tv_layer_set(current_layer)
    current_pos = george.tv_layer_get_pos(current_layer)

    for i in range(total_layers):
        new_pos = current_pos + i + 1
        george.tv_layer_move(new_pos)
        layer_info = george.tv_layer_info(current_layer)
        assert (layer_info.position + 1) == new_pos


@pytest.mark.skipif(not IS_NOT_TVP12, reason="`tv_layer_move` no longer returns -1 when given a bad position.")
@pytest.mark.parametrize("pos", [-1, 3, 100, 1000])
def test_tv_layer_move_wrong_pos(test_project: george.TVPProject, pos: int) -> None:
    with pytest.raises(
        george.GeorgeError,
        match="Couldn't move current layer to position",
    ):
        george.tv_layer_move(pos)


def test_tv_layer_set(test_project: george.TVPProject) -> None:
    layers = [george.tv_layer_create(f"layer_{i}") for i in range(5)]

    for layer in layers:
        george.tv_layer_set(layer)
        assert george.tv_layer_current_id() == layer


@pytest.mark.skipif(not IS_NOT_TVP12, reason="`tv_layer_set` no longer returns -1 when given a bad layer id.")
def test_tv_layer_set_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_set(-16)


def test_tv_layer_selection_get(test_layer: george.TVPLayer) -> None:
    assert not george.tv_layer_selection_get(test_layer.id)


@pytest.mark.skipif(not IS_NOT_TVP12, reason="`tv_LayerSelection` no longer returns -1 when given a bad layer id.")
def test_tv_layer_selection_get_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_selection_get(-1)


@pytest.mark.parametrize("selected", [True, False])
def test_tv_layer_selection_set(test_project: george.TVPProject, selected: bool) -> None:
    layers = [george.tv_layer_create(f"layer_{i}") for i in range(5)]

    for layer in layers:
        george.tv_layer_selection_set(layer, new_state=selected)
        assert george.tv_layer_info(layer).selected == selected


@pytest.mark.skipif(not IS_NOT_TVP12, reason="`tv_LayerSelection` no longer returns -1 when given a bad layer id.")
@pytest.mark.parametrize("selected", [True, False])
def test_tv_layer_selection_set_wrong_id(selected: bool) -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_selection_set(-1, selected)


@pytest.mark.skipif(not IS_NOT_TVP12, reason="`tv_LayerSelection` no longer returns -1 when given a bad layer id.")
def test_tv_layer_selection_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_selection_set(-16, True)


def test_tv_layer_select_n(test_project: george.TVPProject, test_anim_layer: george.TVPLayer) -> None:
    end_frame = 10

    # Draw something in order to select frames
    george.tv_layer_copy()
    george.tv_layer_image(end_frame)
    george.tv_layer_paste()
    george.tv_rect(0, 0, 200, 200)

    selected_frames = george.tv_layer_select(0, end_frame)
    assert selected_frames == end_frame


LAYER_NAMES_TO_TEST = ["new_layer", "0", "new layer", ""]
if not IS_NOT_TVP12:
    LAYER_NAMES_TO_TEST = LAYER_NAMES_TO_TEST[:-1]


@pytest.mark.parametrize("name", LAYER_NAMES_TO_TEST)
def test_tv_layer_create(test_project: george.TVPProject, name: str) -> None:
    new_layer = george.tv_layer_create(name)
    assert george.tv_layer_info(new_layer).name == name


@pytest.mark.skipif(IS_NOT_TVP12, reason="Requires TVP12 or higher")
@pytest.mark.parametrize("name", LAYER_NAMES_TO_TEST)
def test_tv_layer_folder_create(test_project: george.TVPProject, name: str) -> None:
    new_layer = george.tv_layer_create(name, layer_type=0)
    assert george.tv_layer_info(new_layer).type == george.LayerType.FOLDER
    assert george.tv_layer_info(new_layer).name == name


@pytest.mark.parametrize("new_name", LAYER_NAMES_TO_TEST)
def test_tv_layer_duplicate(test_project: george.TVPProject, new_name: str) -> None:
    dup_layer_id = george.tv_layer_duplicate(new_name)
    assert george.tv_layer_current_id() == dup_layer_id
    assert george.tv_layer_info(george.tv_layer_current_id()).name == new_name


@pytest.mark.skipif(not IS_NOT_TVP12, reason="This function no longer works in TVP12")
@pytest.mark.parametrize("new_name", LAYER_NAMES_TO_TEST)
def test_tv_layer_rename(test_layer: george.TVPLayer, new_name: str) -> None:
    cur_layer_id = george.tv_layer_current_id()
    george.tv_layer_rename(cur_layer_id, new_name)
    assert george.tv_layer_info(cur_layer_id).name == new_name


def test_tv_layer_rename_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_rename(-1, "test")


def test_tv_layer_kill(test_project: george.TVPProject) -> None:
    new_layer = george.tv_layer_create("destroy")
    george.tv_layer_kill(new_layer)

    # Layer shouldn't exist anymore
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_get_pos(new_layer)


@pytest.mark.skipif(not IS_NOT_TVP12, reason="`tv_layer_kill` no longer returns -1 when given a bad folder id.")
def test_tv_layer_kill_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_kill(-5)


@pytest.mark.skipif(IS_NOT_TVP12, reason="Requires TVP12 or higher")
@pytest.mark.parametrize("remove_children", (True, False))
def test_tv_layer_folder_delete(test_project: george.TVPProject, remove_children: bool) -> None:
    new_layer = george.tv_layer_create("destroy", layer_type=0)
    george.tv_layer_folder_delete(new_layer, remove_children=remove_children)


@pytest.mark.skipif(not IS_NOT_TVP12, reason="`tv_layer_folder_delete` does not return -1 when given a bad folder id.")
@pytest.mark.skipif(IS_NOT_TVP12, reason="Requires TVP12 or higher")
def test_tv_layer_folder_delete_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_folder_delete(-5, True)


def test_tv_layer_density_get() -> None:
    assert 0 <= george.tv_layer_density_get() <= 100


@pytest.mark.parametrize("density", [0, 50, 100, 25, 150, -50])
def test_tv_layer_density_set(density: int) -> None:
    george.tv_layer_density_set(density)
    assert george.tv_layer_density_get() == min(max(0, density), 100)


def test_tv_layer_display_get(test_layer: george.TVPLayer) -> None:
    current_layer = george.tv_layer_info(george.tv_layer_current_id())
    assert current_layer.visibility == george.tv_layer_display_get(current_layer.id)


def test_tv_layer_display_get_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_display_get(-1)


@pytest.mark.parametrize("new_state", [True, False])
def test_tv_layer_display_set(test_layer: george.TVPLayer, new_state: bool) -> None:
    current_layer = george.tv_layer_info(george.tv_layer_current_id())
    george.tv_layer_display_set(current_layer.id, new_state)
    assert george.tv_layer_info(current_layer.id).visibility == new_state


def test_tv_layer_lock_get(test_layer: george.TVPLayer) -> None:
    george.tv_layer_lock_get(george.tv_layer_current_id())


def test_tv_layer_lock_get_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_lock_get(-1)


@pytest.mark.parametrize("lock", [True, False])
def test_tv_layer_lock_set(test_layer: george.TVPLayer, lock: bool) -> None:
    current_layer = george.tv_layer_current_id()
    george.tv_layer_lock_set(current_layer, lock)
    assert george.tv_layer_lock_get(current_layer) == lock


@pytest.mark.parametrize("lock", [True, False])
def test_tv_layer_lock_set_wrong_id(lock: bool) -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_lock_set(-1, lock)


def test_tv_layer_collapse_get() -> None:
    george.tv_layer_collapse_get(george.tv_layer_current_id())


def test_tv_layer_collapse_get_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_collapse_get(-1)


@pytest.mark.parametrize("collapse", [True, False])
def test_tv_layer_collapse_set(test_layer: george.TVPLayer, collapse: bool) -> None:
    current_layer = george.tv_layer_current_id()
    george.tv_layer_collapse_set(current_layer, collapse)
    assert george.tv_layer_collapse_get(current_layer) == collapse


@pytest.mark.parametrize("collapse", [True, False])
def test_tv_layer_collapse_set_wrong_id(collapse: bool) -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_collapse_set(-1, collapse)


def test_tv_layer_blending_mode_get() -> None:
    assert george.tv_layer_blending_mode_get(george.tv_layer_current_id()) in list(george.BlendingMode)


@pytest.mark.skipif(not IS_NOT_TVP12, reason="`tv_LayerBlendingMode` does not return -1 when given a bad layer id.")
def test_tv_layer_blending_mode_get_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_blending_mode_get(-1)


@pytest.mark.parametrize("mode", george.BlendingMode)
def test_tv_layer_blending_mode_set(test_layer: george.TVPLayer, mode: george.BlendingMode) -> None:
    current_layer = george.tv_layer_current_id()
    george.tv_layer_blending_mode_set(current_layer, mode)
    assert george.tv_layer_blending_mode_get(current_layer) == mode


@pytest.mark.skipif(not IS_NOT_TVP12, reason="`tv_LayerBlendingMode` does not return -1 when given a bad layer id.")
def test_tv_layer_blending_mode_set_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_blending_mode_set(-1, george.BlendingMode.ADD)


def test_tv_layer_stencil_get() -> None:
    george.tv_layer_stencil_get(george.tv_layer_current_id())


@pytest.mark.skipif(not IS_NOT_TVP12, reason="`tv_LayerStencil` does not return -1 when given a bad layer id.")
def test_tv_layer_stencil_get_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_stencil_get(-1)


@pytest.mark.parametrize("mode", george.StencilMode)
def test_tv_layer_stencil_set(test_layer: george.TVPLayer, mode: george.StencilMode) -> None:
    current_layer = george.tv_layer_current_id()
    george.tv_layer_stencil_set(current_layer, mode)

    current_mode = george.tv_layer_stencil_get(current_layer)

    if mode == george.StencilMode.ON:
        assert current_mode == george.StencilMode.NORMAL
    else:
        assert current_mode == mode


@pytest.mark.skipif(not IS_NOT_TVP12, reason="`tv_LayerStencil` does not return -1 when given a bad layer id.")
@pytest.mark.parametrize("mode", george.StencilMode)
def test_tv_layer_stencil_set_wrong_id(mode: george.StencilMode) -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_stencil_set(-1, mode)


def test_tv_layer_show_thumbnails_get() -> None:
    george.tv_layer_show_thumbnails_get(george.tv_layer_current_id())


def test_tv_layer_show_thumbnails_get_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_show_thumbnails_get(-1)


@pytest.mark.parametrize("state", [True, False])
def test_tv_layer_show_thumbnails_set(test_layer: george.TVPLayer, state: bool) -> None:
    current_layer = george.tv_layer_current_id()
    george.tv_layer_show_thumbnails_set(current_layer, state)
    assert george.tv_layer_show_thumbnails_get(current_layer) == state


@pytest.mark.parametrize("state", [True, False])
def test_tv_layer_show_thumbnails_set_wrong_id(state: bool) -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_show_thumbnails_set(-1, state)


def test_tv_layer_auto_break_instance_get() -> None:
    george.tv_layer_auto_break_instance_get(george.tv_layer_current_id())


def test_tv_layer_auto_break_instance_get_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_auto_break_instance_get(-1)


@pytest.mark.parametrize("state", [True, False])
def test_tv_layer_auto_break_instance_set(test_project: george.TVPProject, state: bool) -> None:
    current_layer = george.tv_layer_current_id()
    george.tv_layer_auto_break_instance_set(current_layer, state)
    assert george.tv_layer_auto_break_instance_get(current_layer) == state


@pytest.mark.parametrize("state", [True, False])
def test_tv_layer_auto_break_instance_set_wrong_id(state: bool) -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_auto_break_instance_set(-1, state)


def test_tv_layer_auto_create_instance_get() -> None:
    george.tv_layer_auto_create_instance_get(george.tv_layer_current_id())


def test_tv_layer_auto_create_instance_get_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_auto_create_instance_get(-1)


@pytest.mark.parametrize("state", [True, False])
def test_tv_layer_auto_create_instance_set(test_layer: george.TVPLayer, state: bool) -> None:
    current_layer = george.tv_layer_current_id()
    george.tv_layer_auto_create_instance_set(current_layer, state)
    assert george.tv_layer_auto_create_instance_get(current_layer) == state


@pytest.mark.parametrize("state", [True, False])
def test_tv_layer_auto_create_instance_set_wrong_id(state: bool) -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_auto_create_instance_set(-1, state)


def test_tv_layer_pre_behavior_get() -> None:
    george.tv_layer_pre_behavior_get(george.tv_layer_current_id())


def test_tv_layer_pre_behavior_get_wrong_id() -> None:
    with pytest.raises((george.NoObjectWithIdError, ValueError)):
        george.tv_layer_pre_behavior_get(-1)


@pytest.mark.parametrize("behavior", george.LayerBehavior)
def test_tv_layer_pre_behavior_set(test_layer: george.TVPLayer, behavior: george.LayerBehavior) -> None:
    current_layer = george.tv_layer_current_id()
    george.tv_layer_pre_behavior_set(current_layer, behavior)
    assert george.tv_layer_pre_behavior_get(current_layer) == behavior


@pytest.mark.skipif(not IS_NOT_TVP12, reason="`tv_LayerPreBehavior` does not return -1 when given a bad layer id.")
@pytest.mark.parametrize("behavior", george.LayerBehavior)
def test_tv_layer_pre_behavior_set_wrong_id(behavior: george.LayerBehavior) -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_pre_behavior_set(-1, behavior)


def test_tv_layer_post_behavior_get() -> None:
    george.tv_layer_post_behavior_get(george.tv_layer_current_id())


def test_tv_layer_post_behavior_get_wrong_id() -> None:
    with pytest.raises((george.NoObjectWithIdError, ValueError)):
        george.tv_layer_post_behavior_get(-1)


@pytest.mark.parametrize("behavior", george.LayerBehavior)
def test_tv_layer_post_behavior_set(test_layer: george.TVPLayer, behavior: george.LayerBehavior) -> None:
    current_layer = george.tv_layer_current_id()
    george.tv_layer_post_behavior_set(current_layer, behavior)
    assert george.tv_layer_post_behavior_get(current_layer) == behavior


@pytest.mark.skipif(not IS_NOT_TVP12, reason="`tv_LayerPostBehavior` does not return -1 when given a bad layer id.")
@pytest.mark.parametrize("behavior", george.LayerBehavior)
def test_tv_layer_post_behavior_set_wrong_id(behavior: george.LayerBehavior) -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_post_behavior_set(-1, behavior)


def test_tv_layer_lock_position_get() -> None:
    george.tv_layer_lock_position_get(george.tv_layer_current_id())


@pytest.mark.skipif(not IS_NOT_TVP12, reason="`tv_LayerLockPosition` does not return -1 when given a bad layer id.")
def test_tv_layer_lock_position_get_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_lock_position_get(-1)


@pytest.mark.parametrize("state", [True, False])
def test_tv_layer_lock_position_set(test_layer: george.TVPLayer, state: bool) -> None:
    current_layer = george.tv_layer_current_id()
    george.tv_layer_lock_position_set(current_layer, state)
    assert george.tv_layer_lock_position_get(current_layer) == state


@pytest.mark.skipif(not IS_NOT_TVP12, reason="`tv_LayerLockPosition` does not return -1 when given a bad layer id.")
@pytest.mark.parametrize("state", [True, False])
def test_tv_layer_lock_position_set_wrong_id(state: bool) -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_lock_position_set(-1, state)


def test_tv_preserve_get() -> None:
    george.tv_preserve_get()


@pytest.mark.skipif(not IS_NOT_TVP12, reason="`tv_preserve_set` does not work in tvpaint 12.")
@pytest.mark.parametrize("state", george.LayerTransparency)
def test_tv_preserve_set(test_layer: george.TVPLayer, state: george.LayerTransparency) -> None:
    george.tv_preserve_set(state)
    new_state = george.tv_preserve_get()

    transparency_map = {
        george.LayerTransparency.MINUS_1: george.LayerTransparency.ON,
        george.LayerTransparency.NONE: george.LayerTransparency.OFF,
    }

    assert transparency_map.get(state, state) == new_state


def test_tv_layer_mark_get() -> None:
    george.tv_layer_mark_get(george.tv_layer_current_id(), 0)


def test_tv_layer_mark_get_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_mark_get(-1, 0)


@pytest.mark.parametrize("mark", range(27))
def test_tv_layer_mark_set(test_anim_layer: george.TVPLayer, mark: int) -> None:
    george.tv_layer_mark_set(test_anim_layer.id, 0, mark)
    assert george.tv_layer_mark_get(test_anim_layer.id, 0) == mark


@pytest.mark.skipif(not IS_NOT_TVP12, reason="`tv_LayerMarkSet` does not return -1 when given a bad layer id.")
def test_tv_layer_mark_set_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_mark_set(-1, 0, 0)


def test_tv_layer_anim(test_layer: george.TVPLayer) -> None:
    george.tv_layer_anim(test_layer.id)

    assert george.tv_layer_auto_break_instance_get(test_layer.id)
    assert george.tv_layer_auto_create_instance_get(test_layer.id)
    assert not george.tv_layer_lock_get(test_layer.id)


def test_tv_layer_load_dependencies() -> None:
    george.tv_layer_load_dependencies(george.tv_layer_current_id())


@pytest.mark.parametrize("color_index", range(1, 27))
def test_tv_layer_color_get_color(color_index: int) -> None:
    current_clip = george.tv_clip_current_id()
    color = george.tv_layer_color_get_color(current_clip, color_index)
    assert color.clip_id == current_clip
    assert color.color_index == color_index


def test_tv_layer_color_get_color_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_color_get_color(-1, 0)


name_args = [None, "test"] if IS_NOT_TVP12 else [None]


# We skip index 0 because it's the "Default" color and can't be changed
@pytest.mark.parametrize("color_index", range(1, 27))
@pytest.mark.parametrize("name", name_args)
@pytest.mark.parametrize("rgb", [george.RGBColor(255, 0, 0), george.RGBColor(0, 255, 0)])
def test_tv_layer_color_set_color(
    test_clip: george.TVPClip, color_index: int, name: str | None, rgb: george.RGBColor
) -> None:
    george.tv_layer_color_set_color(test_clip.id, color_index, rgb, name)

    color = george.tv_layer_color_get_color(test_clip.id, color_index)

    assert color.color_index == color_index
    assert color.color_r == rgb.r
    assert color.color_g == rgb.g
    assert color.color_b == rgb.b
    assert color.clip_id == test_clip.id

    if name is not None:
        assert color.name == name


@pytest.mark.skipif(
    not IS_NOT_TVP12, reason="`tv_LayerColor setcolor` does not return -1 when given a bad color index."
)
def test_tv_layer_color_set_color_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_color_set_color(-1, 1, george.RGBColor(0, 0, 0))


def test_tv_layer_color_get(test_layer: george.TVPLayer) -> None:
    index = george.tv_layer_color_get(test_layer.id)
    assert 0 <= index <= 26


def test_tv_layer_color_get_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_layer_color_get(-1)


@pytest.mark.parametrize("color_index", range(27))
def test_tv_layer_color_set_s(test_layer: george.TVPLayer, color_index: int) -> None:
    george.tv_layer_color_set(test_layer.id, color_index)
    assert george.tv_layer_color_get(test_layer.id) == color_index


@pytest.fixture
def layers_with_colors(test_project: george.TVPProject) -> FixtureYield[tuple[int, list[int]]]:
    """
    Fixture that create some layers with a color
    """
    color_index = 5
    layers = [george.tv_layer_create(f"layer_{i}") for i in range(10)]
    color_layers = [layer for i, layer in enumerate(layers) if i % 2 == 0]

    # Set the color of all layers
    for layer in color_layers:
        george.tv_layer_color_set(layer, color_index)

    yield color_index, color_layers


@pytest.mark.skipif(reason="Skip when running full tests otherwise it fails for some reason...")
@pytest.mark.parametrize("color_index", range(27))
def test_tv_layer_color_visible(test_project: george.TVPProject, color_index: int) -> None:
    # It seems that there's no way to set the visibility of a layer color group
    # So we only test that all groups are visible
    assert george.tv_layer_color_visible(color_index)


def test_tv_layer_color_lock(layers_with_colors: tuple[int, list[int]]) -> None:
    color_index, layers_to_lock = layers_with_colors
    assert george.tv_layer_color_lock(color_index) == len(layers_to_lock)
    assert all(george.tv_layer_lock_get(layer) for layer in layers_to_lock)


def test_tv_layer_color_unlock(layers_with_colors: tuple[int, list[int]]) -> None:
    color_index, layers_to_lock = layers_with_colors

    for layer in layers_to_lock:
        george.tv_layer_lock_set(layer, True)

    assert george.tv_layer_color_unlock(color_index) == len(layers_to_lock)
    assert all(not george.tv_layer_lock_get(layer) for layer in layers_to_lock)


@pytest.mark.parametrize("display", george.LayerColorDisplayOpt)
def test_tv_layer_color_show(layers_with_colors: tuple[int, list[int]], display: george.LayerColorDisplayOpt) -> None:
    color_index, layers_to_show = layers_with_colors

    is_display = display == george.LayerColorDisplayOpt.DISPLAY

    for layer in layers_to_show:
        if is_display:
            george.tv_layer_display_set(layer, False)
        else:
            george.tv_layer_collapse_set(layer, True)

    george.tv_layer_color_show(display, color_index)

    check_fn = george.tv_layer_display_get if is_display else george.tv_layer_collapse_get

    assert all(check_fn(layer) for layer in layers_to_show)


@pytest.mark.parametrize("display", george.LayerColorDisplayOpt)
def test_tv_layer_color_hide(layers_with_colors: tuple[int, list[int]], display: george.LayerColorDisplayOpt) -> None:
    color_index, layers_to_hide = layers_with_colors

    george.tv_layer_color_hide(display, color_index)

    check_fn = (
        george.tv_layer_display_get if display == george.LayerColorDisplayOpt.DISPLAY else george.tv_layer_collapse_get
    )

    assert all(not check_fn(layer) for layer in layers_to_hide)


def test_tv_layer_color_select(layers_with_colors: tuple[int, list[int]]) -> None:
    color_index, layers_to_select = layers_with_colors

    george.tv_layer_color_select(color_index)
    assert all(george.tv_layer_selection_get(layer) for layer in layers_to_select)


def test_tv_layer_color_unselect(layers_with_colors: tuple[int, list[int]]) -> None:
    color_index, layers_to_select = layers_with_colors

    for layer in layers_to_select:
        george.tv_layer_selection_set(layer, True)

    george.tv_layer_color_unselect(color_index)
    assert all(not george.tv_layer_selection_get(layer) for layer in layers_to_select)


def can_be_parsed_as_int(value: str) -> bool:
    if " " in value:
        return False

    try:
        int(value)
    except ValueError:
        return False

    return True


@pytest.mark.skip("this test is overly complicated because I couldn't find a way to correctly grasp the logic")
@pytest.mark.parametrize("mode", george.InstanceNamingMode)
@pytest.mark.parametrize("prefix", [None, "pre_"])
@pytest.mark.parametrize("suffix", [None, "_suf"])
@pytest.mark.parametrize("process", [None, *george.InstanceNamingProcess])
@pytest.mark.parametrize("initial_name", ["", "5", " 7", "fest", "test_3"])
def test_tv_instance_name(
    test_layer: george.TVPLayer,
    mode: george.InstanceNamingMode,
    prefix: str | None,
    suffix: str | None,
    process: george.InstanceNamingProcess | None,
    initial_name: str,
) -> None:
    instance = 0

    # Assign an initial name to the instance
    george.tv_instance_set_name(test_layer.id, instance, name=initial_name)

    # Rename all instances
    george.tv_instance_name(test_layer.id, mode, prefix, suffix, process)

    if mode == george.InstanceNamingMode.ALL:
        expected_name = " " + str(instance + 1)
        if prefix:
            expected_name = prefix + expected_name
    else:  # SMART mode
        no_prefix = prefix is None
        no_suffix = suffix is None

        cond_text = (
            len(initial_name) and process == george.InstanceNamingProcess.TEXT and (can_be_parsed_as_int(initial_name))
        )

        cond_empty = (
            len(initial_name)
            and process == george.InstanceNamingProcess.EMPTY
            and (no_prefix != no_suffix and not can_be_parsed_as_int(initial_name))
        )

        cond_number = (
            len(initial_name)
            and process == george.InstanceNamingProcess.NUMBER
            and not (no_prefix == no_suffix and not can_be_parsed_as_int(initial_name))
            and not can_be_parsed_as_int(initial_name)
        )

        if cond_text or cond_empty or cond_number:
            expected_name = initial_name
        else:
            expected_name = str(instance + 1)

            if suffix:
                expected_name += suffix

            if prefix:
                expected_name = prefix + expected_name

    assert expected_name == george.tv_instance_get_name(test_layer.id, instance)


@pytest.mark.skip("Crashed TVPaint")
@pytest.mark.parametrize("mode", george.InstanceNamingMode)
def test_tv_instance_name_wrong_id(mode: george.InstanceNamingMode) -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_instance_name(-1, mode)


def test_tv_instance_get_name(test_layer: george.TVPLayer) -> None:
    # By default there's an instance at frame zero
    george.tv_instance_get_name(test_layer.id, 0)


def test_tv_instance_get_name_wrong_id() -> None:
    with pytest.raises(george.NoObjectWithIdError):
        george.tv_instance_get_name(-1, 0)


@pytest.mark.parametrize("name", ["", "5", " 7", "fest", "test_3"])
def test_tv_instance_set_name(test_layer: george.TVPLayer, name: str) -> None:
    george.tv_instance_set_name(test_layer.id, 0, name)
    assert george.tv_instance_get_name(test_layer.id, 0) == name


def test_tv_instance_set_name_wrong_id() -> None:
    with pytest.raises(george.GeorgeError):
        george.tv_instance_set_name(-1, 0, "test")


def instance_exists(frame: int) -> bool:
    try:
        george.tv_instance_get_name(george.tv_layer_current_id(), frame)
    except george.NoObjectWithIdError:
        return False
    return True


@pytest.mark.parametrize("frame", range(5))
def test_tv_layer_copy_paste_single(test_anim_layer: george.TVPLayer, frame: int) -> None:
    george.tv_layer_image(0)
    george.tv_layer_copy()
    george.tv_layer_image(frame)
    george.tv_layer_paste()

    assert instance_exists(frame)


@pytest.mark.parametrize("frame", range(1, 6))
def test_tv_layer_cut_paste_single(test_anim_layer: george.TVPLayer, frame: int) -> None:
    cut_frame = 10

    # Add another instance because if we cut the first it deletes the layer
    george.tv_layer_copy()
    george.tv_layer_image(cut_frame)
    george.tv_layer_paste()

    # Cut that instance
    george.tv_layer_image(cut_frame)
    george.tv_layer_cut()

    # The instance should be removed
    assert not instance_exists(cut_frame)

    # Paste at another frame
    george.tv_layer_image(frame)
    george.tv_layer_paste()

    assert instance_exists(frame)


def test_tv_layer_insert_image_duplicate(test_anim_layer: george.TVPLayer) -> None:
    initial_frame = 5

    # Copy the instance in the middle
    george.tv_layer_image(0)
    george.tv_layer_copy()
    george.tv_layer_image(initial_frame)
    george.tv_layer_paste()

    george.tv_layer_insert_image(duplicate=True)
    assert instance_exists(initial_frame + 1)


@pytest.mark.parametrize("count", range(1, 8))
@pytest.mark.parametrize("direction", george.InsertDirection)
def test_tv_layer_insert_image(test_anim_layer: george.TVPLayer, count: int, direction: george.InsertDirection) -> None:
    initial_frame = 10

    # Copy the instance in the middle
    george.tv_layer_image(0)
    george.tv_layer_copy()
    george.tv_layer_image(initial_frame)
    george.tv_layer_paste()

    george.tv_layer_insert_image(count, direction)

    offset = 0
    while offset < count:
        if direction == george.InsertDirection.AFTER:  # noqa: SIM108
            next_frame = initial_frame + offset
        else:
            next_frame = initial_frame - offset

        assert instance_exists(next_frame)
        offset += 1


@pytest.mark.parametrize("start", [0, 5, 10, 100])
def test_tv_layer_shift(test_layer: george.TVPLayer, start: int) -> None:
    george.tv_layer_shift(test_layer.id, start)


@pytest.mark.parametrize("blending", george.BlendingMode)
@pytest.mark.parametrize("stamp", [True, False])
def test_tv_layer_merge(create_some_layers: list[Layer], blending: george.BlendingMode, stamp: bool) -> None:
    george.tv_layer_merge(create_some_layers[0].id, blending, stamp)


@pytest.mark.parametrize("keep_color_grp", [False, True])
@pytest.mark.parametrize("keep_img_mark", [False, True])
@pytest.mark.parametrize("keep_instance_name", [False, True])
def test_tv_layer_merge_all(
    create_some_layers: list[Layer],
    keep_color_grp: bool,
    keep_img_mark: bool,
    keep_instance_name: bool,
) -> None:
    george.tv_layer_merge_all(keep_color_grp, keep_img_mark, keep_instance_name)


def test_tv_save_image(tmp_path: Path) -> None:
    save_ext, _ = george.tv_save_mode_get()
    ext = "jpg" if save_ext == george.SaveFormat.JPG else save_ext.value
    out_img = (tmp_path / "out").with_suffix("." + ext)
    george.tv_save_image(out_img)
    assert out_img.exists()


@pytest.mark.parametrize("stretch", [False, True])
def test_tv_load_image(
    test_clip: george.TVPClip,
    test_layer: george.TVPLayer,
    png_sequence: list[Path],
    stretch: bool,
) -> None:
    george.tv_load_image(png_sequence[0], stretch)
    # Verify that there's an instance frame
    assert george.tv_instance_get_name(test_layer.id, 0) == ""


@pytest.mark.skip("Will block the UI")
def test_tv_load_image_file_does_not_exist(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        george.tv_load_image(tmp_path / "file.png")
