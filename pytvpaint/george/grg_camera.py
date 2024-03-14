"""Camera related George functions."""

from __future__ import annotations

from dataclasses import dataclass

from pytvpaint.george.client import send_cmd
from pytvpaint.george.client.parse import (
    tv_parse_list,
    validate_args_list,
)
from pytvpaint.george.grg_base import FieldOrder, GrgErrorValue


@dataclass(frozen=True)
class TVPCamera:
    """TVPaint camera info values."""

    width: int
    height: int
    field_order: FieldOrder
    frame_rate: float
    pixel_aspect_ratio: float
    anti_aliasing: int


@dataclass(frozen=True)
class TVPCameraPoint:
    """camera 2D point info."""

    x: float
    y: float
    angle: float
    scale: float


def tv_camera_info_get() -> TVPCamera:
    """Get the information of the camera."""
    return TVPCamera(**tv_parse_list(send_cmd("tv_CameraInfo"), with_fields=TVPCamera))


def tv_camera_info_set(
    width: int | None = None,
    height: int | None = None,
    field_order: FieldOrder | None = None,
    frame_rate: float | None = None,
    pixel_aspect_ratio: float | None = None,
) -> TVPCamera:
    """Set the information of the camera."""
    optional_args = [
        (width, height),
        field_order.value if field_order else None,
        frame_rate,
        pixel_aspect_ratio,
    ]

    args = validate_args_list(optional_args)

    result = send_cmd("tv_CameraInfo", *args)
    return TVPCamera(**tv_parse_list(result, with_fields=TVPCamera))


def tv_camera_enum_points(index: int) -> TVPCameraPoint:
    """Get the position/angle/scale values of the n-th point of the camera path."""
    res = send_cmd("tv_CameraEnumPoints", index, error_values=[GrgErrorValue.NONE])
    return TVPCameraPoint(**tv_parse_list(res, with_fields=TVPCameraPoint))


def tv_camera_interpolation(position: float) -> TVPCameraPoint:
    """Get the position/angle/scale values at the given position on the camera path (between 0 and 1)."""
    res = tv_parse_list(
        send_cmd("tv_CameraInterpolation", position),
        with_fields=TVPCameraPoint,
    )
    return TVPCameraPoint(**res)


def tv_camera_insert_point(
    index: int,
    x: float,
    y: float,
    angle: float,
    scale: float,
) -> None:
    """Add a point to the camera path *before* the given index."""
    send_cmd("tv_CameraInsertPoint", index, x, y, angle, scale)


def tv_camera_remove_point(index: int) -> None:
    """Remove a point at the given index."""
    send_cmd("tv_CameraRemovePoint", index)


def tv_camera_set_point(
    index: int,
    x: float,
    y: float,
    angle: float,
    scale: float,
) -> None:
    """Set position/angle/scale value of a point at the given index and make it current."""
    send_cmd("tv_CameraSetPoint", index, x, y, angle, scale)
