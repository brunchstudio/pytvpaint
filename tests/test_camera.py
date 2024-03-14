import pytest

from pytvpaint import george
from pytvpaint.camera import Camera, CameraPoint
from pytvpaint.clip import Clip
from pytvpaint.george.grg_base import FieldOrder
from tests.conftest import FixtureYield


@pytest.fixture
def current_camera(test_clip_obj: Clip) -> FixtureYield[Camera]:
    yield Camera(test_clip_obj)


def test_camera_init(test_clip_obj: Clip) -> None:
    camera_data = george.tv_camera_info_get()
    camera = Camera(test_clip_obj, data=camera_data)

    assert camera.clip == test_clip_obj

    assert camera.width == camera_data.width
    assert camera.height == camera_data.height
    assert camera.field_order == camera_data.field_order
    assert camera.fps == camera_data.frame_rate
    assert camera.pixel_aspect_ratio == camera_data.pixel_aspect_ratio
    assert camera.anti_aliasing == camera_data.anti_aliasing


def test_camera_refresh(current_camera: Camera) -> None:
    current_camera.refresh()


@pytest.mark.parametrize("width", [1, 50, 100, 1920])
def test_camera_width(current_camera: Camera, width: int) -> None:
    current_camera.width = width
    assert current_camera.width == width


@pytest.mark.parametrize("height", [1, 50, 100, 1080])
def test_camera_height(current_camera: Camera, height: int) -> None:
    current_camera.height = height
    assert current_camera.height == height


@pytest.mark.parametrize("fps", [5.0, 10.0, 24.0, 60.0])
def test_camera_fps(current_camera: Camera, fps: float) -> None:
    current_camera.fps = fps
    assert current_camera.fps == fps


@pytest.mark.parametrize("aspect_ratio", [0.5, 1, 4])
def test_camera_pixel_aspect_ratio(current_camera: Camera, aspect_ratio: float) -> None:
    current_camera.pixel_aspect_ratio = aspect_ratio
    assert current_camera.pixel_aspect_ratio == aspect_ratio


@pytest.mark.parametrize("field_order", FieldOrder)
def test_camera_field_order(current_camera: Camera, field_order: FieldOrder) -> None:
    current_camera.field_order = field_order
    assert current_camera.field_order == field_order


def test_camera_insert_point(current_camera: Camera) -> None:
    point = current_camera.insert_point(0, 50, 50, 34, 1.5)
    assert next(current_camera.points) == point


def test_camera_current_points_data(current_camera: Camera) -> None:
    george.tv_camera_insert_point(0, 50, 50, 34, 1.5)
    point = george.tv_camera_enum_points(0)
    assert next(Camera.current_points()) == CameraPoint(0, camera=current_camera, data=point)


def test_camera_get_point_data_at(current_camera: Camera) -> None:
    start = current_camera.insert_point(0, 50, 50, 10, 1.2)
    end = current_camera.insert_point(1, 10, 5, 48, 0.4)

    assert current_camera.get_point_data_at(0.0) == start.data
    assert current_camera.get_point_data_at(1.0) == end.data


def test_camera_remove_point(current_camera: Camera) -> None:
    current_camera.insert_point(0, 50, 50, 34, 1.5)
    current_camera.remove_point(0)
    assert len(list(current_camera.points)) == 0
