import pytest
from pytvpaint.layer import Layer, LayerInstance

from tests.conftest import FixtureYield


@pytest.fixture
def test_layer_instance(test_anim_layer_obj: Layer) -> FixtureYield[LayerInstance]:
    start_frame = test_anim_layer_obj.project.start_frame
    yield LayerInstance(test_anim_layer_obj, start_frame)


def test_layer_instance_init(test_anim_layer_obj: Layer) -> None:
    start_frame = test_anim_layer_obj.project.start_frame
    instance = LayerInstance(test_anim_layer_obj, start_frame)

    assert instance.start == start_frame
    assert instance.layer == test_anim_layer_obj


def test_layer_instance_init_wrong_frame(test_anim_layer_obj: Layer) -> None:
    with pytest.raises(ValueError, match="no instance at frame"):
        LayerInstance(test_anim_layer_obj, 67)


@pytest.mark.parametrize("name", ["name", "l", "lo6", "8.2"])
def test_layer_instance_name(test_layer_instance: LayerInstance, name: str) -> None:
    test_layer_instance.name = name
    assert test_layer_instance.name == name


def test_layer_instance_duplicate(test_layer_instance: LayerInstance) -> None:
    test_layer_instance.duplicate()
    assert test_layer_instance.layer.get_instance(test_layer_instance.start + 1)
