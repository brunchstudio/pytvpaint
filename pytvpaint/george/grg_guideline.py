"""Guideline related George functions."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import cast

from pytvpaint.george.client import send_cmd
from pytvpaint.george.grg_base import GrgErrorValue, RGBAColor
from pytvpaint.george.client.parse import (
    DataclassInstance,
    get_dataclass_fields,
    args_dict_to_list,
    tv_parse_dict,
)


class GuidelineType(Enum):
    """All guideline types.

    Attributes:
        IMAGE:
        LINE:
        SEGMENT:
        CIRCLE:
        ELLIPSE:
        GRID:
        MARKS:
        FIELD_CHART:
        ANIMATOR_FIELD:
        SAFE_AREA:
        VANISH_POINT_1:
        VANISH_POINT_2:
        VANISH_POINT_3:
    """

    IMAGE = "image"
    LINE = "line"
    SEGMENT = "segment"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    GRID = "grid"
    MARKS = "marks"
    FIELD_CHART = "fieldchart"
    ANIMATOR_FIELD = "animatorfield"
    SAFE_AREA = "safearea"
    VANISH_POINT_1 = "vanishpoint1"
    VANISH_POINT_2 = "vanishpoint2"
    VANISH_POINT_3 = "vanishpoint3"


class FlipDirection(Enum):
    """Filp Direction.

    Attributes:
        X:
        Y:
        XY:
    """

    X = "x"
    Y = "y"
    XY = "xy"
    NONE = "none"


class GuidelineAlphaMode(Enum):
    """The alpha load mode.

    Attributes:
        PREMULTIPLY:
        NO_PREMULTIPLY:
    """

    PREMULTIPLY = "premultiply"
    NO_PREMULTIPLY = "nopremultiply"


@dataclass(frozen=True)
class TVPGuidelineImage:
    """TVPaint project info values."""

    position: int = field(metadata={"parsed": False})

    path: Path
    x: float
    y: float
    rotation: float
    scale: float
    flip: FlipDirection


@dataclass(frozen=True)
class TVPGuidelineLine:
    """TVPaint project info values."""

    position: int = field(metadata={"parsed": False})

    x: float
    y: float
    angle: float


@dataclass(frozen=True)
class TVPGuidelineSegment:
    """TVPaint project info values."""

    position: int = field(metadata={"parsed": False})

    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(frozen=True)
class TVPGuidelineCircle:
    """TVPaint project info values."""

    position: int = field(metadata={"parsed": False})

    x: float
    y: float
    radius: float


@dataclass(frozen=True)
class TVPGuidelineEllipse:
    """TVPaint project info values."""

    position: int = field(metadata={"parsed": False})

    x: float
    y: float
    radius_a: float
    radius_b: float


@dataclass(frozen=True)
class TVPGuidelineGrid:
    """TVPaint project info values."""

    position: int = field(metadata={"parsed": False})

    x: float
    y: float
    width: float = field(metadata={"alt_name": "w"})
    height: float = field(metadata={"alt_name": "h"})


@dataclass(frozen=True)
class TVPGuidelineMarks:
    """TVPaint project info values."""

    position: int = field(metadata={"parsed": False})

    count_x: float
    count_y: float


@dataclass(frozen=True)
class TVPGuidelineSafeArea:
    """TVPaint project info values."""

    position: int = field(metadata={"parsed": False})

    sf_out: float = field(metadata={"alt_name": "out"})
    sf_in: float = field(metadata={"alt_name": "in"})


@dataclass(frozen=True)
class TVPGuidelineVanishPoint1:
    """TVPaint project info values."""

    position: int = field(metadata={"parsed": False})

    x: float
    y: float
    ray: int
    grid: bool


@dataclass(frozen=True)
class TVPGuidelineVanishPoint2:
    """TVPaint project info values."""

    position: int = field(metadata={"parsed": False})

    x1: float
    y1: float
    x2: float
    y2: float
    ray: int


@dataclass(frozen=True)
class TVPGuidelineVanishPoint3:
    """TVPaint project info values."""

    position: int = field(metadata={"parsed": False})

    x1: float
    y1: float
    x2: float
    y2: float
    x3: float
    y3: float
    ray: int


@dataclass(frozen=True)
class TVPGuideField:
    """TVPaint project info values."""

    position: int = field(metadata={"parsed": False})


def tv_guideline_enum(position: int, guideline_type: GuidelineType) -> int:
    """Check the existence of a guideline at the given position.

    Raises:
        GeorgeError: if given an invalid scene id or clip position or elements have been removed
    """
    return int(
        send_cmd(
            "tv_GuidelineEnum",
            position,
            guideline_type.value,
            error_values=[-1, -2, GrgErrorValue.NONE],
        )
    )


def tv_guideline_remove_all(guideline_type: GuidelineType) -> None:
    """Removes all guidelines of the given type."""
    send_cmd(
        "tv_GuidelineRemove",
        "all",
        guideline_type.value,
        error_values=[-1, -2],
    )


def tv_guideline_remove(position: int, guideline_type: GuidelineType) -> None:
    """Removes the guidelines at the given position and type."""
    send_cmd(
        "tv_GuidelineRemove",
        guideline_type.value,
        position,
        error_values=[GrgErrorValue.NONE],
    )


def tv_guideline_name_get(position: int) -> str:
    """Get the name of the guideline at the given position."""
    return str(
        send_cmd(
            "tv_GuidelineName",
            position,
            error_values=[GrgErrorValue.ERROR],
        )
    ).strip()


def tv_guideline_name_set(position: int, name: str) -> None:
    """Set the name of the guideline at the given position."""
    send_cmd(
        "tv_GuidelineName",
        position,
        name,
        error_values=[GrgErrorValue.ERROR],
    )


def tv_guideline_visibility_get(position: int, on_global: bool = False) -> bool:
    """Get the visibility of the guideline at the given position."""
    return bool(
        int(
            send_cmd(
                "tv_GuidelineVisible",
                position if not on_global else "global",
                error_values=[-1, -2],
            )
        )
    )


def tv_guideline_visibility_set(position: int, is_visible: bool, on_global: bool = False) -> None:
    """Set the visibility of the guideline at the given position."""
    send_cmd(
        "tv_GuidelineVisible",
        position if not on_global else "global",
        int(is_visible),
        error_values=[-1, -2],
    )


def tv_guideline_visibility_set_all(
    guideline_type: GuidelineType | None, is_visible: bool, apply_all: bool = False
) -> None:
    """Set the visibility of the guideline of the given type or all of them regardless of type.

    Args:
        guideline_type: the guideline type or None if `apply_all` is used.
        is_visible: True to set as visible, False otherwise.
        apply_all: True to apply to all guidelines regardless of type.
    """
    if guideline_type is not None and not apply_all:
        apply_to = guideline_type.value
    else:
        apply_to = "all"

    send_cmd(
        "tv_GuidelineVisible",
        apply_to,
        int(is_visible),
        error_values=[-1, -2],
    )


def tv_guideline_margin_get(position: int, on_global: bool = False) -> int:
    """Get the margin of the guideline at the given position."""
    return int(
        send_cmd(
            "tv_GuidelineMarge",
            position if not on_global else "global",
            error_values=[-1, -2],
        )
    )


def tv_guideline_margin_set(position: int, margin: int, on_global: bool = False) -> None:
    """Set the margin of the guideline at the given position."""
    send_cmd(
        "tv_GuidelineMarge",
        position if not on_global else "global",
        margin,
        error_values=[-1, -2],
    )


def tv_guideline_margin_set_all(guideline_type: GuidelineType | None, margin: int, apply_all: bool = False) -> None:
    """Set the margin of the guideline of the given type or all of them regardless of type.

    Args:
        guideline_type: the guideline type or None if `apply_all` is used.
        margin: the margin to apply.
        apply_all: True to apply to all guidelines regardless of type.
    """
    if guideline_type is not None and not apply_all:
        apply_to = guideline_type.value
    else:
        apply_to = "all"

    send_cmd(
        "tv_GuidelineMarge",
        apply_to,
        margin,
        error_values=[-1, -2],
    )


def tv_guideline_color_get(position: int, on_global: bool = False) -> RGBAColor:
    """Get the color of the guideline at the given position."""
    result = send_cmd(
        "tv_GuidelineColor",
        position if not on_global else "global",
        error_values=[-1, -2],
    )
    r, g, b, a = result.split()
    return RGBAColor(*[int(c) for c in (r, g, b, a)])


def tv_guideline_color_set(position: int, color: RGBAColor, on_global: bool = False) -> None:
    """Set the color of the guideline at the given position."""
    send_cmd(
        "tv_GuidelineColor",
        position if not on_global else "global",
        color.r,
        color.g,
        color.b,
        color.a,
        error_values=[-1, -2],
    )


def tv_guideline_color_set_all(guideline_type: GuidelineType | None, color: RGBAColor, apply_all: bool = False) -> None:
    """Set the color of the guideline of the given type or all of them regardless of type.

    Args:
        guideline_type: the guideline type or None if `apply_all` is used.
        color: the color to apply.
        apply_all: True to apply to all guidelines regardless of type.
    """
    if guideline_type is not None and not apply_all:
        apply_to = guideline_type.value
    else:
        apply_to = "all"

    send_cmd(
        "tv_GuidelineColor",
        apply_to,
        color.r,
        color.g,
        color.b,
        color.a,
        error_values=[-1, -2],
    )


def tv_guideline_snap_get(position: int, on_global: bool = False) -> bool:
    """Get the snap status of the guideline at the given position."""
    return bool(
        int(
            send_cmd(
                "tv_GuidelineSnap",
                position if not on_global else "global",
                error_values=[-1, -2],
            )
        )
    )


def tv_guideline_snap_set(position: int, snap: bool, on_global: bool = False) -> None:
    """Set the guideline snap at the given position."""
    send_cmd(
        "tv_GuidelineSnap",
        position if not on_global else "global",
        int(snap),
        error_values=[-1, -2],
    )


def tv_guideline_snap_set_all(guideline_type: GuidelineType | None, snap: bool, apply_all: bool = False) -> None:
    """Set the guideline snap for the given type or all of them regardless of type.

    Args:
        guideline_type: the guideline type or None if `apply_all` is used.
        snap: True to snap, False otherwise.
        apply_all: True to apply to all guidelines regardless of type.
    """
    if guideline_type is not None and not apply_all:
        apply_to = guideline_type.value
    else:
        apply_to = "all"

    send_cmd(
        "tv_GuidelineSnap",
        apply_to,
        int(snap),
        error_values=[-1, -2],
    )


def tv_guideline_collapse_get(position: int) -> bool:
    """Get the collapse status of the guideline at the given position."""
    return bool(
        int(
            send_cmd(
                "tv_guidelineCollapse",
                position,
                error_values=[-1, -2],
            )
        )
    )


def tv_guideline_collapse_set(position: int, collapse: bool) -> None:
    """Set the guideline collapse at the given position."""
    send_cmd(
        "tv_guidelineCollapse",
        position,
        int(collapse),
        error_values=[-1, -2],
    )


def tv_guideline_add_image(
    img_path: Path | str | None = None,
    x: float | None = None,
    y: float | None = None,
    rotation: float | None = None,
    scale: float | None = None,
    flip: FlipDirection | None = None,
    alpha_mode: GuidelineAlphaMode | None = None,
) -> int:
    """Set info for the image guideline at the given position."""
    args = args_dict_to_list(
        {
            "img_path": img_path,
            "x": x,
            "y": y,
            "rotation": rotation,
            "scale": scale,
            "flip": flip,
            "alphamode": alpha_mode,
        }
    )

    return int(
        send_cmd(
            "tv_GuidelineAdd",
            "image",
            *args,
            error_values=[-1, -2],
        )
    )


def tv_guideline_modify_image_get(position: int) -> TVPGuidelineImage:
    """Get info for the image guideline at the given position."""

    result = send_cmd(
        "tv_GuidelineModify",
        position,
        error_values=[-1, -2],
    )

    guideline = tv_parse_dict(result, with_fields=TVPGuidelineImage)
    guideline["position"] = position
    return TVPGuidelineImage(**guideline)


def tv_guideline_modify_image_set(
    position: int,
    img_path: Path | str | None = None,
    x: float | None = None,
    y: float | None = None,
    rotation: float | None = None,
    scale: float | None = None,
    flip: FlipDirection | None = None,
) -> TVPGuidelineImage:
    """Set info for the image guideline at the given position."""
    args = args_dict_to_list(
        {
            "position": position,
            "img_path": img_path,
            "x": x,
            "y": y,
            "rotation": rotation,
            "scale": scale,
            "flip": flip,
        }
    )

    result = send_cmd(
        "tv_GuidelineModify",
        *args,
        error_values=[-1, -2],
    )

    fields = get_dataclass_fields(cast(DataclassInstance, TVPGuidelineImage))
    guideline = tv_parse_dict(result, with_fields=fields)
    guideline["position"] = position
    return TVPGuidelineImage(**guideline)


def tv_guideline_modify_line_get(position: int) -> TVPGuidelineLine:
    """Get info for the image guideline at the given position."""

    result = send_cmd(
        "tv_GuidelineModify",
        position,
        error_values=[-1, -2],
    )

    guideline = tv_parse_dict(result, with_fields=TVPGuidelineLine)
    guideline["position"] = position
    return TVPGuidelineLine(**guideline)


def tv_guideline_modify_segment_get(position: int) -> TVPGuidelineSegment:
    """Get info for the image guideline at the given position."""

    result = send_cmd(
        "tv_GuidelineModify",
        position,
        error_values=[-1, -2],
    )

    guideline = tv_parse_dict(result, with_fields=TVPGuidelineSegment)
    guideline["position"] = position
    return TVPGuidelineSegment(**guideline)


def tv_guideline_modify_circle_get(position: int) -> TVPGuidelineCircle:
    """Get info for the image guideline at the given position."""

    result = send_cmd(
        "tv_GuidelineModify",
        position,
        error_values=[-1, -2],
    )

    guideline = tv_parse_dict(result, with_fields=TVPGuidelineCircle)
    guideline["position"] = position
    return TVPGuidelineCircle(**guideline)


def tv_guideline_modify_ellipse_get(position: int) -> TVPGuidelineEllipse:
    """Get info for the image guideline at the given position."""

    result = send_cmd(
        "tv_GuidelineModify",
        position,
        error_values=[-1, -2],
    )

    guideline = tv_parse_dict(result, with_fields=TVPGuidelineEllipse)
    guideline["position"] = position
    return TVPGuidelineEllipse(**guideline)


def tv_guideline_modify_grid_get(position: int) -> TVPGuidelineGrid:
    """Get info for the image guideline at the given position."""

    result = send_cmd(
        "tv_GuidelineModify",
        position,
        error_values=[-1, -2],
    )

    guideline = tv_parse_dict(result, with_fields=TVPGuidelineGrid)
    guideline["position"] = position
    return TVPGuidelineGrid(**guideline)


def tv_guideline_modify_marks_get(position: int) -> TVPGuidelineMarks:
    """Get info for the image guideline at the given position."""

    result = send_cmd(
        "tv_GuidelineModify",
        position,
        error_values=[-1, -2],
    )

    guideline = tv_parse_dict(result, with_fields=TVPGuidelineMarks)
    guideline["position"] = position
    return TVPGuidelineMarks(**guideline)


def tv_guideline_modify_safe_area_get(position: int) -> TVPGuidelineSafeArea:
    """Get info for the image guideline at the given position."""

    result = send_cmd(
        "tv_GuidelineModify",
        position,
        error_values=[-1, -2],
    )

    guideline = tv_parse_dict(result, with_fields=TVPGuidelineSafeArea)
    guideline["position"] = position
    return TVPGuidelineSafeArea(**guideline)


def tv_guideline_modify_vanish_point_1_get(position: int) -> TVPGuidelineVanishPoint1:
    """Get info for the image guideline at the given position."""

    result = send_cmd(
        "tv_GuidelineModify",
        position,
        error_values=[-1, -2],
    )

    guideline = tv_parse_dict(result, with_fields=TVPGuidelineVanishPoint1)
    guideline["position"] = position
    return TVPGuidelineVanishPoint1(**guideline)


def tv_guideline_modify_vanish_point_2_get(position: int) -> TVPGuidelineVanishPoint2:
    """Get info for the image guideline at the given position."""

    result = send_cmd(
        "tv_GuidelineModify",
        position,
        error_values=[-1, -2],
    )

    guideline = tv_parse_dict(result, with_fields=TVPGuidelineVanishPoint2)
    guideline["position"] = position
    return TVPGuidelineVanishPoint2(**guideline)


def tv_guideline_modify_vanish_point_3_get(position: int) -> TVPGuidelineVanishPoint3:
    """Get info for the image guideline at the given position."""

    result = send_cmd(
        "tv_GuidelineModify",
        position,
        error_values=[-1, -2],
    )

    guideline = tv_parse_dict(result, with_fields=TVPGuidelineVanishPoint3)
    guideline["position"] = position
    return TVPGuidelineVanishPoint3(**guideline)
