from __future__ import annotations

from typing import Any

import pytest
from pytvpaint.george.base import FieldOrder
from pytvpaint.george.camera import (
    TVPCameraPoint,
    tv_camera_enum_points,
    tv_camera_info_get,
    tv_camera_info_set,
    tv_camera_insert_point,
    tv_camera_interpolation,
    tv_camera_remove_point,
    tv_camera_set_point,
)
from pytvpaint.george.exceptions import GeorgeError
from pytvpaint.george.project import TVPProject


def test_tv_camera_info_get(test_project: TVPProject) -> None:
    camera = tv_camera_info_get()
    assert camera.width == test_project.width
    assert camera.height == test_project.height
    assert camera.frame_rate == test_project.frame_rate
    assert camera.pixel_aspect_ratio == test_project.pixel_aspect_ratio


@pytest.mark.parametrize(
    "args",
    [
        tuple(),
        (20, 20),
        (200, 1009),
        (500, 500, FieldOrder.LOWER),
        (500, 20, FieldOrder.NONE),
        (500, 20, FieldOrder.UPPER),
        (500, 20, FieldOrder.UPPER, 12.0),
        (500, 20, FieldOrder.UPPER, 50.0, 2.0),
        (1, 20, FieldOrder.NONE, 50.0, 2.0),
    ],
)
def test_tv_camera_info_set(
    test_project: TVPProject,
    args: tuple[Any, ...],
) -> None:
    tv_camera_info_set(*args)

    attrs_check = [
        "width",
        "height",
        "field_order",
        "frame_rate",
        "pixel_aspect_ratio",
    ]

    camera = tv_camera_info_get()
    for attr, arg in zip(attrs_check, args):
        current = getattr(camera, attr)
        err_msg = f"Error checking {attr} (expected: {arg}, current: {current})"
        assert current == arg, err_msg


def test_tv_camera_enum_points(test_project: TVPProject) -> None:
    tv_camera_insert_point(0, 0, 0, 0, 1)
    assert tv_camera_enum_points(0)


def test_tv_camera_enum_points_wrong_index(test_project: TVPProject) -> None:
    with pytest.raises(GeorgeError):
        tv_camera_enum_points(0)


def map_value(start: int, end: int, ratio: float) -> float:
    return start + (end - start) * ratio


def test_tv_camera_interpolation(test_project: TVPProject) -> None:
    start_x = 0
    start_y = 0
    end_x = 50
    end_y = 50

    tv_camera_insert_point(0, start_x, start_y, 0, 1)
    tv_camera_insert_point(5, end_x, end_y, 0, 3)

    steps = 10
    for i in range(steps + 1):
        ratio = i / steps
        inter = tv_camera_interpolation(i / steps)
        assert round(inter.x) == map_value(start_x, end_x, ratio)
        assert round(inter.y) == map_value(start_y, end_y, ratio)


def test_tv_camera_insert_point(test_project: TVPProject) -> None:
    point = TVPCameraPoint(50, 26, 0, scale=0.0)
    tv_camera_insert_point(0, point.x, point.y, point.angle, point.angle)
    assert tv_camera_interpolation(0.0) == point


def test_tv_camera_remove_point() -> None:
    tv_camera_insert_point(0, 50, 25, 0, 0.0)
    tv_camera_remove_point(0)

    with pytest.raises(GeorgeError):
        tv_camera_enum_points(0)


def test_tv_camera_set_point() -> None:
    tv_camera_insert_point(0, 50, 25, 0, 0.0)
    new_point = TVPCameraPoint(67, 34, 1, 0.5)
    tv_camera_set_point(0, new_point.x, new_point.y, new_point.angle, new_point.scale)
    assert tv_camera_enum_points(0) == new_point
