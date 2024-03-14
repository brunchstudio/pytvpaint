from __future__ import annotations

from pathlib import Path

import pytest

from pytvpaint.george.exceptions import GeorgeError, NoObjectWithIdError
from pytvpaint.george.grg_base import BlendingMode, RGBColor, tv_rect, SaveFormat, tv_save_mode_get
from pytvpaint.george.grg_clip import TVPClip, tv_clip_current_id, tv_layer_image
from pytvpaint.george.grg_layer import (
    InsertDirection,
    InstanceNamingMode,
    InstanceNamingProcess,
    LayerBehavior,
    LayerColorDisplayOpt,
    LayerTransparency,
    StencilMode,
    TVPLayer,
    tv_instance_get_name,
    tv_instance_name,
    tv_instance_set_name,
    tv_layer_anim,
    tv_layer_auto_break_instance_get,
    tv_layer_auto_break_instance_set,
    tv_layer_auto_create_instance_get,
    tv_layer_auto_create_instance_set,
    tv_layer_blending_mode_get,
    tv_layer_blending_mode_set,
    tv_layer_collapse_get,
    tv_layer_collapse_set,
    tv_layer_color_get,
    tv_layer_color_get_color,
    tv_layer_color_hide,
    tv_layer_color_lock,
    tv_layer_color_select,
    tv_layer_color_set,
    tv_layer_color_set_color,
    tv_layer_color_show,
    tv_layer_color_unlock,
    tv_layer_color_unselect,
    tv_layer_color_visible,
    tv_layer_copy,
    tv_layer_create,
    tv_layer_current_id,
    tv_layer_cut,
    tv_layer_density_get,
    tv_layer_density_set,
    tv_layer_display_get,
    tv_layer_display_set,
    tv_layer_duplicate,
    tv_layer_get_id,
    tv_layer_get_pos,
    tv_layer_info,
    tv_layer_insert_image,
    tv_layer_kill,
    tv_layer_load_dependencies,
    tv_layer_lock_get,
    tv_layer_lock_position_get,
    tv_layer_lock_position_set,
    tv_layer_lock_set,
    tv_layer_mark_get,
    tv_layer_mark_set,
    tv_layer_merge,
    tv_layer_merge_all,
    tv_layer_move,
    tv_layer_paste,
    tv_layer_post_behavior_get,
    tv_layer_post_behavior_set,
    tv_layer_pre_behavior_get,
    tv_layer_pre_behavior_set,
    tv_layer_rename,
    tv_layer_select,
    tv_layer_selection_get,
    tv_layer_selection_set,
    tv_layer_set,
    tv_layer_shift,
    tv_layer_show_thumbnails_get,
    tv_layer_show_thumbnails_set,
    tv_layer_stencil_get,
    tv_layer_stencil_set,
    tv_preserve_get,
    tv_preserve_set,
    tv_save_image,
    tv_load_image
)
from pytvpaint.george.grg_project import TVPProject
from pytvpaint.layer import Layer
from tests.conftest import FixtureYield


def test_tv_layer_current_id(test_project: TVPProject) -> None:
    assert tv_layer_current_id()


def test_tv_layer_get_id(test_project: TVPProject) -> None:
    assert tv_layer_get_id(0) == tv_layer_current_id()


def test_tv_layer_get_id_neg_pos_error(test_project: TVPProject) -> None:
    with pytest.raises(GeorgeError, match="No layer at provided position"):
        tv_layer_get_id(-1)


def test_tv_layer_get_pos(test_project: TVPProject) -> None:
    assert tv_layer_get_pos(tv_layer_current_id()) == 0


def test_tv_layer_get_pos_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_get_pos(56)


def test_tv_layer_info() -> None:
    info = tv_layer_info(tv_layer_current_id())
    assert info.id


def test_tv_layer_info_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_info(-4)


def test_tv_layer_move(test_project: TVPProject) -> None:
    current_layer = tv_layer_current_id()
    total_layers = 10

    for i in range(total_layers):
        tv_layer_create(f"layer_{i}")

    # Make the current layer the original one
    tv_layer_set(current_layer)

    for i in range(total_layers):
        new_pos = i + 1
        tv_layer_move(new_pos)
        layer_info = tv_layer_info(current_layer)
        # Position starts at 1
        assert layer_info.position + 1 == new_pos


@pytest.mark.parametrize("pos", [-1, 2, 100, 1000])
def test_tv_layer_move_wrong_pos(test_project: TVPProject, pos: int) -> None:
    with pytest.raises(
        GeorgeError,
        match="Couldn't move current layer to position",
    ):
        tv_layer_move(pos)


def test_tv_layer_set(test_project: TVPProject) -> None:
    layers = [tv_layer_create(f"layer_{i}") for i in range(5)]

    for layer in layers:
        tv_layer_set(layer)
        assert tv_layer_current_id() == layer


def test_tv_layer_set_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_set(-16)


def test_tv_layer_selection_get(test_layer: TVPLayer) -> None:
    assert not tv_layer_selection_get(test_layer.id)


def test_tv_layer_selection_get_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_selection_get(-1)


@pytest.mark.parametrize("selected", [True, False])
def test_tv_layer_selection_set(test_project: TVPProject, selected: bool) -> None:
    layers = [tv_layer_create(f"layer_{i}") for i in range(5)]

    for layer in layers:
        tv_layer_selection_set(layer, new_state=selected)
        assert tv_layer_info(layer).selected == selected


@pytest.mark.parametrize("selected", [True, False])
def test_tv_layer_selection_set_wrong_id(selected: bool) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_selection_set(-1, selected)


def test_tv_layer_selection_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_selection_set(-16, True)


def test_tv_layer_select_n(test_project: TVPProject, test_anim_layer: TVPLayer) -> None:
    end_frame = 10

    # Draw something in order to select frames
    tv_layer_copy()
    tv_layer_image(end_frame)
    tv_layer_paste()
    tv_rect(0, 0, 200, 200)

    selected_frames = tv_layer_select(0, end_frame)
    assert selected_frames == end_frame


LAYER_NAMES_TO_TEST = ["new_layer", "0", "new layer", ""]


@pytest.mark.parametrize("name", LAYER_NAMES_TO_TEST)
def test_tv_layer_create(test_project: TVPProject, name: str) -> None:
    new_layer = tv_layer_create(name)
    assert tv_layer_info(new_layer).name == name


@pytest.mark.parametrize("new_name", LAYER_NAMES_TO_TEST)
def test_tv_layer_duplicate(test_project: TVPProject, new_name: str) -> None:
    dup_layer_id = tv_layer_duplicate(new_name)
    assert tv_layer_current_id() == dup_layer_id
    assert tv_layer_info(tv_layer_current_id()).name == new_name


@pytest.mark.parametrize("new_name", LAYER_NAMES_TO_TEST)
def test_tv_layer_rename(test_layer: TVPLayer, new_name: str) -> None:
    tv_layer_rename(tv_layer_current_id(), new_name)


def test_tv_layer_rename_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_rename(-1, "test")


def test_tv_layer_kill(test_project: TVPProject) -> None:
    new_layer = tv_layer_create("destroy")
    tv_layer_kill(new_layer)

    # Layer shouldn't exist anymore
    with pytest.raises(NoObjectWithIdError):
        tv_layer_get_pos(new_layer)


def test_tv_layer_kill_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_kill(-5)


def test_tv_layer_density_get() -> None:
    assert 0 <= tv_layer_density_get() <= 100


@pytest.mark.parametrize("density", [0, 50, 100, 25, 150, -50])
def test_tv_layer_density_set(density: int) -> None:
    tv_layer_density_set(density)
    assert tv_layer_density_get() == min(max(0, density), 100)


def test_tv_layer_display_get(test_layer: TVPLayer) -> None:
    current_layer = tv_layer_info(tv_layer_current_id())
    assert current_layer.visibility == tv_layer_display_get(current_layer.id)


def test_tv_layer_display_get_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_display_get(-1)


@pytest.mark.parametrize("new_state", [True, False])
def test_tv_layer_display_set(test_layer: TVPLayer, new_state: bool) -> None:
    current_layer = tv_layer_info(tv_layer_current_id())
    tv_layer_display_set(current_layer.id, new_state)
    assert tv_layer_info(current_layer.id).visibility == new_state


def test_tv_layer_lock_get(test_layer: TVPLayer) -> None:
    tv_layer_lock_get(tv_layer_current_id())


def test_tv_layer_lock_get_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_lock_get(-1)


@pytest.mark.parametrize("lock", [True, False])
def test_tv_layer_lock_set(test_layer: TVPLayer, lock: bool) -> None:
    current_layer = tv_layer_current_id()
    tv_layer_lock_set(current_layer, lock)
    assert tv_layer_lock_get(current_layer) == lock


@pytest.mark.parametrize("lock", [True, False])
def test_tv_layer_lock_set_wrong_id(lock: bool) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_lock_set(-1, lock)


def test_tv_layer_collapse_get() -> None:
    tv_layer_collapse_get(tv_layer_current_id())


def test_tv_layer_collapse_get_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_collapse_get(-1)


@pytest.mark.parametrize("collapse", [True, False])
def test_tv_layer_collapse_set(test_layer: TVPLayer, collapse: bool) -> None:
    current_layer = tv_layer_current_id()
    tv_layer_collapse_set(current_layer, collapse)
    assert tv_layer_collapse_get(current_layer) == collapse


@pytest.mark.parametrize("collapse", [True, False])
def test_tv_layer_collapse_set_wrong_id(collapse: bool) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_collapse_set(-1, collapse)


def test_tv_layer_blending_mode_get() -> None:
    assert tv_layer_blending_mode_get(tv_layer_current_id()) in list(BlendingMode)


def test_tv_layer_blending_mode_get_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_blending_mode_get(-1)


@pytest.mark.parametrize("mode", BlendingMode)
def test_tv_layer_blending_mode_set(test_layer: TVPLayer, mode: BlendingMode) -> None:
    current_layer = tv_layer_current_id()
    tv_layer_blending_mode_set(current_layer, mode)
    assert tv_layer_blending_mode_get(current_layer) == mode


def test_tv_layer_blending_mode_set_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_blending_mode_set(-1, BlendingMode.ADD)


def test_tv_layer_stencil_get() -> None:
    tv_layer_stencil_get(tv_layer_current_id())


def test_tv_layer_stencil_get_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_stencil_get(-1)


@pytest.mark.parametrize("mode", StencilMode)
def test_tv_layer_stencil_set(test_layer: TVPLayer, mode: StencilMode) -> None:
    current_layer = tv_layer_current_id()
    tv_layer_stencil_set(current_layer, mode)

    current_mode = tv_layer_stencil_get(current_layer)

    if mode == StencilMode.ON:
        assert current_mode == StencilMode.NORMAL
    else:
        assert current_mode == mode


@pytest.mark.parametrize("mode", StencilMode)
def test_tv_layer_stencil_set_wrong_id(mode: StencilMode) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_stencil_set(-1, mode)


def test_tv_layer_show_thumbnails_get() -> None:
    tv_layer_show_thumbnails_get(tv_layer_current_id())


def test_tv_layer_show_thumbnails_get_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_show_thumbnails_get(-1)


@pytest.mark.parametrize("state", [True, False])
def test_tv_layer_show_thumbnails_set(test_layer: TVPLayer, state: bool) -> None:
    current_layer = tv_layer_current_id()
    tv_layer_show_thumbnails_set(current_layer, state)
    assert tv_layer_show_thumbnails_get(current_layer) == state


@pytest.mark.parametrize("state", [True, False])
def test_tv_layer_show_thumbnails_set_wrong_id(state: bool) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_show_thumbnails_set(-1, state)


def test_tv_layer_auto_break_instance_get() -> None:
    tv_layer_auto_break_instance_get(tv_layer_current_id())


def test_tv_layer_auto_break_instance_get_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_auto_break_instance_get(-1)


@pytest.mark.parametrize("state", [True, False])
def test_tv_layer_auto_break_instance_set(
    test_project: TVPProject, state: bool
) -> None:
    current_layer = tv_layer_current_id()
    tv_layer_auto_break_instance_set(current_layer, state)
    assert tv_layer_auto_break_instance_get(current_layer) == state


@pytest.mark.parametrize("state", [True, False])
def test_tv_layer_auto_break_instance_set_wrong_id(state: bool) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_auto_break_instance_set(-1, state)


def test_tv_layer_auto_create_instance_get() -> None:
    tv_layer_auto_create_instance_get(tv_layer_current_id())


def test_tv_layer_auto_create_instance_get_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_auto_create_instance_get(-1)


@pytest.mark.parametrize("state", [True, False])
def test_tv_layer_auto_create_instance_set(test_layer: TVPLayer, state: bool) -> None:
    current_layer = tv_layer_current_id()
    tv_layer_auto_create_instance_set(current_layer, state)
    assert tv_layer_auto_create_instance_get(current_layer) == state


@pytest.mark.parametrize("state", [True, False])
def test_tv_layer_auto_create_instance_set_wrong_id(state: bool) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_auto_create_instance_set(-1, state)


def test_tv_layer_pre_behavior_get() -> None:
    tv_layer_pre_behavior_get(tv_layer_current_id())


def test_tv_layer_pre_behavior_get_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_pre_behavior_get(-1)


@pytest.mark.parametrize("behavior", LayerBehavior)
def test_tv_layer_pre_behavior_set(
    test_layer: TVPLayer, behavior: LayerBehavior
) -> None:
    current_layer = tv_layer_current_id()
    tv_layer_pre_behavior_set(current_layer, behavior)
    assert tv_layer_pre_behavior_get(current_layer) == behavior


@pytest.mark.parametrize("behavior", LayerBehavior)
def test_tv_layer_pre_behavior_set_wrong_id(behavior: LayerBehavior) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_pre_behavior_set(-1, behavior)


def test_tv_layer_post_behavior_get() -> None:
    tv_layer_post_behavior_get(tv_layer_current_id())


def test_tv_layer_post_behavior_get_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_post_behavior_get(-1)


@pytest.mark.parametrize("behavior", LayerBehavior)
def test_tv_layer_post_behavior_set(
    test_layer: TVPLayer, behavior: LayerBehavior
) -> None:
    current_layer = tv_layer_current_id()
    tv_layer_post_behavior_set(current_layer, behavior)
    assert tv_layer_post_behavior_get(current_layer) == behavior


@pytest.mark.parametrize("behavior", LayerBehavior)
def test_tv_layer_post_behavior_set_wrong_id(behavior: LayerBehavior) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_post_behavior_set(-1, behavior)


def test_tv_layer_lock_position_get() -> None:
    tv_layer_lock_position_get(tv_layer_current_id())


def test_tv_layer_lock_position_get_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_lock_position_get(-1)


@pytest.mark.parametrize("state", [True, False])
def test_tv_layer_lock_position_set(test_layer: TVPLayer, state: bool) -> None:
    current_layer = tv_layer_current_id()
    tv_layer_lock_position_set(current_layer, state)
    assert tv_layer_lock_position_get(current_layer) == state


@pytest.mark.parametrize("state", [True, False])
def test_tv_layer_lock_position_set_wrong_id(state: bool) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_lock_position_set(-1, state)


def test_tv_preserve_get() -> None:
    tv_preserve_get()


@pytest.mark.parametrize("state", LayerTransparency)
def test_tv_preserve_set(test_layer: TVPLayer, state: LayerTransparency) -> None:
    tv_preserve_set(state)
    new_state = tv_preserve_get()

    transparency_map = {
        LayerTransparency.MINUS_1: LayerTransparency.ON,
        LayerTransparency.NONE: LayerTransparency.OFF,
    }

    assert transparency_map.get(state, state) == new_state


def test_tv_layer_mark_get() -> None:
    tv_layer_mark_get(tv_layer_current_id(), 0)


def test_tv_layer_mark_get_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_mark_get(-1, 0)


@pytest.mark.parametrize("mark", range(27))
def test_tv_layer_mark_set(test_anim_layer: TVPLayer, mark: int) -> None:
    tv_layer_mark_set(test_anim_layer.id, 0, mark)
    assert tv_layer_mark_get(test_anim_layer.id, 0) == mark


def test_tv_layer_mark_set_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_mark_set(-1, 0, 0)


def test_tv_layer_anim(test_layer: TVPLayer) -> None:
    tv_layer_anim(test_layer.id)

    assert tv_layer_auto_break_instance_get(test_layer.id)
    assert tv_layer_auto_create_instance_get(test_layer.id)
    assert not tv_layer_lock_get(test_layer.id)


def test_tv_layer_load_dependencies() -> None:
    tv_layer_load_dependencies(tv_layer_current_id())


@pytest.mark.parametrize("color_index", range(1, 27))
def test_tv_layer_color_get_color(color_index: int) -> None:
    current_clip = tv_clip_current_id()
    color = tv_layer_color_get_color(current_clip, color_index)
    assert color.clip_id == current_clip
    assert color.color_index == color_index


def test_tv_layer_color_get_color_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_color_get_color(-1, 0)


# We skip index 0 because it's the "Default" color and can't be changed
@pytest.mark.parametrize("color_index", range(1, 27))
@pytest.mark.parametrize("name", [None, "test"])
@pytest.mark.parametrize("rgb", [RGBColor(255, 0, 0), RGBColor(0, 255, 0)])
def test_tv_layer_color_set_color(
    test_clip: TVPClip, color_index: int, name: str | None, rgb: RGBColor
) -> None:
    tv_layer_color_set_color(test_clip.id, color_index, rgb, name)

    color = tv_layer_color_get_color(test_clip.id, color_index)

    assert color.color_index == color_index
    assert color.color_r == rgb.r
    assert color.color_g == rgb.g
    assert color.color_b == rgb.b
    assert color.clip_id == test_clip.id

    if name is not None:
        assert color.name == name


def test_tv_layer_color_set_color_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_color_set_color(-1, 1, RGBColor(0, 0, 0))


def test_tv_layer_color_get(test_layer: TVPLayer) -> None:
    index = tv_layer_color_get(test_layer.id)
    assert 0 <= index <= 26


def test_tv_layer_color_get_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_layer_color_get(-1)


@pytest.mark.parametrize("color_index", range(27))
def test_tv_layer_color_set_s(test_layer: TVPLayer, color_index: int) -> None:
    tv_layer_color_set(test_layer.id, color_index)
    assert tv_layer_color_get(test_layer.id) == color_index


@pytest.fixture
def layers_with_colors(test_project: TVPProject) -> FixtureYield[tuple[int, list[int]]]:
    """
    Fixture that create some layers with a color
    """
    color_index = 5
    layers = [tv_layer_create(f"layer_{i}") for i in range(10)]
    color_layers = [layer for i, layer in enumerate(layers) if i % 2 == 0]

    # Set the color of all layers
    for layer in color_layers:
        tv_layer_color_set(layer, color_index)

    yield color_index, color_layers


def test_tv_layer_color_lock(layers_with_colors: tuple[int, list[int]]) -> None:
    color_index, layers_to_lock = layers_with_colors
    assert tv_layer_color_lock(color_index) == len(layers_to_lock)
    assert all(tv_layer_lock_get(layer) for layer in layers_to_lock)


def test_tv_layer_color_unlock(layers_with_colors: tuple[int, list[int]]) -> None:
    color_index, layers_to_lock = layers_with_colors

    for layer in layers_to_lock:
        tv_layer_lock_set(layer, True)

    assert tv_layer_color_unlock(color_index) == len(layers_to_lock)
    assert all(not tv_layer_lock_get(layer) for layer in layers_to_lock)


@pytest.mark.parametrize("display", LayerColorDisplayOpt)
def test_tv_layer_color_show(
    layers_with_colors: tuple[int, list[int]], display: LayerColorDisplayOpt
) -> None:
    color_index, layers_to_show = layers_with_colors

    is_display = display == LayerColorDisplayOpt.DISPLAY

    for layer in layers_to_show:
        if is_display:
            tv_layer_display_set(layer, False)
        else:
            tv_layer_collapse_set(layer, True)

    tv_layer_color_show(display, color_index)

    check_fn = tv_layer_display_get if is_display else tv_layer_collapse_get

    assert all(check_fn(layer) for layer in layers_to_show)


@pytest.mark.parametrize("display", LayerColorDisplayOpt)
def test_tv_layer_color_hide(
    layers_with_colors: tuple[int, list[int]], display: LayerColorDisplayOpt
) -> None:
    color_index, layers_to_hide = layers_with_colors

    tv_layer_color_hide(display, color_index)

    check_fn = (
        tv_layer_display_get
        if display == LayerColorDisplayOpt.DISPLAY
        else tv_layer_collapse_get
    )

    assert all(not check_fn(layer) for layer in layers_to_hide)


@pytest.mark.parametrize("color_index", range(27))
def test_tv_layer_color_visible(color_index: int) -> None:
    # It seems that there's no way to set the visibility of a layer color group
    # So we only test that all groups are visible
    assert tv_layer_color_visible(color_index)


def test_tv_layer_color_select(layers_with_colors: tuple[int, list[int]]) -> None:
    color_index, layers_to_select = layers_with_colors

    tv_layer_color_select(color_index)
    assert all(tv_layer_selection_get(layer) for layer in layers_to_select)


def test_tv_layer_color_unselect(layers_with_colors: tuple[int, list[int]]) -> None:
    color_index, layers_to_select = layers_with_colors

    for layer in layers_to_select:
        tv_layer_selection_set(layer, True)

    tv_layer_color_unselect(color_index)
    assert all(not tv_layer_selection_get(layer) for layer in layers_to_select)


def can_be_parsed_as_int(value: str) -> bool:
    if " " in value:
        return False

    try:
        int(value)
    except ValueError:
        return False

    return True


@pytest.mark.parametrize("mode", InstanceNamingMode)
@pytest.mark.parametrize("prefix", [None, "pre_"])
@pytest.mark.parametrize("suffix", [None, "_suf"])
@pytest.mark.parametrize("process", [None, *InstanceNamingProcess])
@pytest.mark.parametrize("initial_name", ["", "5", " 7", "fest", "test_3"])
def test_tv_instance_name(
    test_layer: TVPLayer,
    mode: InstanceNamingMode,
    prefix: str | None,
    suffix: str | None,
    process: InstanceNamingProcess | None,
    initial_name: str,
) -> None:
    """
    TODO: this test is overly complicated because I couldn't find a way to correctly grasp the logic
    """
    instance = 0

    # Assign an initial name to the instance
    tv_instance_set_name(test_layer.id, instance, name=initial_name)

    # Rename all instances
    tv_instance_name(test_layer.id, mode, prefix, suffix, process)

    if mode == InstanceNamingMode.ALL:
        expected_name = " " + str(instance + 1)
        if prefix:
            expected_name = prefix + expected_name
    else:  # SMART mode
        no_prefix = prefix is None
        no_suffix = suffix is None

        cond_text = (
            len(initial_name)
            and process == InstanceNamingProcess.TEXT
            and (can_be_parsed_as_int(initial_name))
        )

        cond_empty = (
            len(initial_name)
            and process == InstanceNamingProcess.EMPTY
            and (no_prefix != no_suffix and not can_be_parsed_as_int(initial_name))
        )

        cond_number = (
            len(initial_name)
            and process == InstanceNamingProcess.NUMBER
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

    assert expected_name == tv_instance_get_name(test_layer.id, instance)


@pytest.mark.skip("Crashed TVPaint")
@pytest.mark.parametrize("mode", InstanceNamingMode)
def test_tv_instance_name_wrong_id(mode: InstanceNamingMode) -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_instance_name(-1, mode)


def test_tv_instance_get_name(test_layer: TVPLayer) -> None:
    # By default there's an instance at frame zero
    tv_instance_get_name(test_layer.id, 0)


def test_tv_instance_get_name_wrong_id() -> None:
    with pytest.raises(NoObjectWithIdError):
        tv_instance_get_name(-1, 0)


@pytest.mark.parametrize("name", ["", "5", " 7", "fest", "test_3"])
def test_tv_instance_set_name(test_layer: TVPLayer, name: str) -> None:
    tv_instance_set_name(test_layer.id, 0, name)
    assert tv_instance_get_name(test_layer.id, 0) == name


def test_tv_instance_set_name_wrong_id() -> None:
    with pytest.raises(GeorgeError):
        tv_instance_set_name(-1, 0, "test")


def instance_exists(frame: int) -> bool:
    try:
        tv_instance_get_name(tv_layer_current_id(), frame)
    except NoObjectWithIdError:
        return False
    return True


@pytest.mark.parametrize("frame", range(5))
def test_tv_layer_copy_paste(test_anim_layer: TVPLayer, frame: int) -> None:
    tv_layer_image(0)
    tv_layer_copy()
    tv_layer_image(frame)
    tv_layer_paste()

    assert instance_exists(frame)


@pytest.mark.parametrize("frame", range(1, 6))
def test_tv_layer_cut_paste(test_anim_layer: TVPLayer, frame: int) -> None:
    cut_frame = 10

    # Add another instance because if we cut the first it deletes the layer
    tv_layer_copy()
    tv_layer_image(cut_frame)
    tv_layer_paste()

    # Cut that instance
    tv_layer_image(cut_frame)
    tv_layer_cut()

    # The instance should be removed
    assert not instance_exists(cut_frame)

    # Paste at another frame
    tv_layer_image(frame)
    tv_layer_paste()

    assert instance_exists(frame)


def test_tv_layer_insert_image_duplicate(test_anim_layer: TVPLayer) -> None:
    initial_frame = 5

    # Copy the instance in the middle
    tv_layer_image(0)
    tv_layer_copy()
    tv_layer_image(initial_frame)
    tv_layer_paste()

    tv_layer_insert_image(duplicate=True)
    assert instance_exists(initial_frame + 1)


@pytest.mark.parametrize("count", range(1, 8))
@pytest.mark.parametrize("direction", InsertDirection)
def test_tv_layer_insert_image(
    test_anim_layer: TVPLayer, count: int, direction: InsertDirection
) -> None:
    initial_frame = 10

    # Copy the instance in the middle
    tv_layer_image(0)
    tv_layer_copy()
    tv_layer_image(initial_frame)
    tv_layer_paste()

    tv_layer_insert_image(count, direction)

    offset = 0
    while offset < count:
        if direction == InsertDirection.AFTER:
            next_frame = initial_frame + offset
        else:
            next_frame = initial_frame - offset

        assert instance_exists(next_frame)
        offset += 1


@pytest.mark.parametrize("start", [0, 5, 10, 100])
def test_tv_layer_shift(test_layer: TVPLayer, start: int) -> None:
    tv_layer_shift(test_layer.id, start)


@pytest.mark.parametrize("blending", BlendingMode)
@pytest.mark.parametrize("stamp", [True, False])
def test_tv_layer_merge(
    create_some_layers: list[Layer], blending: BlendingMode, stamp: bool
) -> None:
    tv_layer_merge(create_some_layers[0].id, blending, stamp)


@pytest.mark.parametrize("keep_color_grp", [False, True])
@pytest.mark.parametrize("keep_img_mark", [False, True])
@pytest.mark.parametrize("keep_instance_name", [False, True])
def test_tv_layer_merge_all(
    create_some_layers: list[Layer],
    keep_color_grp: bool,
    keep_img_mark: bool,
    keep_instance_name: bool,
) -> None:
    tv_layer_merge_all(keep_color_grp, keep_img_mark, keep_instance_name)


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
    with pytest.raises(FileNotFoundError):
        tv_load_image(tmp_path / "file.png")
