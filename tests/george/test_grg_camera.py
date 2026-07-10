from __future__ import annotations

from typing import Any

import pytest

from pytvpaint import george

IS_TVP12 = george.tv_version()[1].startswith("12")


def test_tv_camera_info_get(test_project: george.TVPProject) -> None:
    camera = george.tv_camera_info_get()
    assert camera.width == test_project.width
    assert camera.height == test_project.height
    assert camera.pixel_aspect_ratio == test_project.pixel_aspect_ratio
    if not IS_TVP12:
        assert camera.frame_rate == test_project.frame_rate


@pytest.mark.parametrize(
    "args",
    [
        tuple(),
        (20, 20),
        (200, 1009),
        (500, 500, george.FieldOrder.LOWER),
        (500, 20, george.FieldOrder.NONE),
        (500, 20, george.FieldOrder.UPPER),
        (500, 20, george.FieldOrder.UPPER, 12.0),
        (500, 20, george.FieldOrder.UPPER, 50.0, 2.0),
        (1, 20, george.FieldOrder.NONE, 50.0, 2.0),
    ],
)
def test_tv_camera_info_set(
    test_project: george.TVPProject,
    args: tuple[Any, ...],
) -> None:
    george.tv_camera_info_set(*args)

    attrs_check = [
        "width",
        "height",
        "field_order",
        "frame_rate",
        "pixel_aspect_ratio",
    ]

    camera = george.tv_camera_info_get()
    for attr, arg in zip(attrs_check, args):
        current = getattr(camera, attr)
        err_msg = f"Error checking {attr} (expected: {arg}, current: {current})"

        if IS_TVP12 and attr in ("frame_rate", "field_order"):
            continue
        assert current == arg, err_msg


def test_tv_camera_enum_points(test_project: george.TVPProject) -> None:
    george.tv_camera_insert_point(0, 0, 0, 0, 1)
    assert george.tv_camera_enum_points(0)


@pytest.mark.skipif(IS_TVP12, reason="`tv_camera_enum_points` no longer returns -1 when given a bad point index.")
def test_tv_camera_enum_points_wrong_index(test_project: george.TVPProject) -> None:
    with pytest.raises(george.GeorgeError):
        george.tv_camera_enum_points(0)


def map_value(start: int, end: int, ratio: float) -> float:
    return start + (end - start) * ratio


@pytest.mark.skipif(IS_TVP12, reason="Function no longer works properly in TVP 12")
def test_tv_camera_interpolation(test_project: george.TVPProject) -> None:
    start_x = 0
    start_y = 0
    end_x = 50
    end_y = 50

    george.tv_camera_insert_point(0, start_x, start_y, 0, 1)
    george.tv_camera_insert_point(5, end_x, end_y, 0, 3)

    steps = 10
    for i in range(steps + 1):
        ratio = i / steps
        inter = george.tv_camera_interpolation(ratio)
        assert round(inter.x) == map_value(start_x, end_x, ratio)
        assert round(inter.y) == map_value(start_y, end_y, ratio)


@pytest.mark.skipif(
    IS_TVP12,
    reason="Skipping since tv_camera_interpolation no longer works properly in TVP 12",
)
def test_tv_camera_insert_point(test_project: george.TVPProject) -> None:
    point = george.TVPCameraPoint(50, 26, 0, scale=0.0)
    george.tv_camera_insert_point(0, point.x, point.y, point.angle, point.angle)
    assert george.tv_camera_interpolation(0.0) == point


def test_tv_camera_remove_point(test_project: george.TVPProject) -> None:
    # Note : leave `test_project` in test args otherwise test won't work
    george.tv_camera_insert_point(0, 50, 25, 0, 0.0)
    george.tv_camera_remove_point(0)

    with pytest.raises(george.GeorgeError):
        george.tv_camera_enum_points(0)


@pytest.mark.skipif(
    IS_TVP12,
    reason="Skipping since tv_camera_enum_points no longer works properly in TVP 12",
)
def test_tv_camera_set_point() -> None:
    george.tv_camera_insert_point(0, 50, 25, 0, 0.0)
    new_point = george.TVPCameraPoint(67, 34, 1, 0.5)
    george.tv_camera_set_point(0, new_point.x, new_point.y, new_point.angle, new_point.scale)
    assert george.tv_camera_enum_points(0) == new_point
