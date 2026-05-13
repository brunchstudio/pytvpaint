import contextlib
from pathlib import Path

import pytest

from pytvpaint import george
from tests.conftest import FixtureYield


@pytest.fixture(autouse=True)
def clean_guidelines() -> FixtureYield[None]:
    """Wipe all guidelines before and after each test to ensure a clean TVP state."""

    def _remove_all() -> None:
        for g_type in george.GuidelineType:
            with contextlib.suppress(Exception):
                george.tv_guideline_remove_all(g_type)

    _remove_all()
    yield
    _remove_all()


def test_grg_guideline_base_properties(guideline_pos: int) -> None:
    """Test getting and setting global/common properties on a guideline."""
    assert george.tv_guideline_enum(guideline_pos, george.GuidelineType.LINE) == guideline_pos

    # Name
    george.tv_guideline_name_set(guideline_pos, "test_line")
    assert george.tv_guideline_name_get(guideline_pos) == "test_line"

    # Collapse
    george.tv_guideline_collapse_set(guideline_pos, collapse=True)
    assert george.tv_guideline_collapse_get(guideline_pos) is True

    # Removal
    george.tv_guideline_remove(guideline_pos, george.GuidelineType.LINE)
    with pytest.raises(Exception):  # Assuming your client raises a GeorgeError on invalid enum
        george.tv_guideline_enum(guideline_pos, george.GuidelineType.LINE)


def test_grg_guideline_visibility(guideline_pos: int) -> None:
    george.tv_guideline_visibility_set(guideline_pos, is_visible=False)
    assert george.tv_guideline_visibility_get(guideline_pos) is False
    # Visibility Apply All
    george.tv_guideline_visibility_set_all(george.GuidelineType.LINE, is_visible=True)
    assert george.tv_guideline_visibility_get(guideline_pos) is True
    george.tv_guideline_visibility_set_all(None, is_visible=False, apply_all=True)
    assert george.tv_guideline_visibility_get(guideline_pos) is False
    # Visibility Global
    george.tv_guideline_visibility_set(0, is_visible=False, on_global=True)
    assert george.tv_guideline_visibility_get(0, on_global=True) is False
    george.tv_guideline_visibility_set(0, is_visible=True, on_global=True)
    assert george.tv_guideline_visibility_get(0, on_global=True) is True


def test_grg_guideline_margin(guideline_pos: int) -> None:
    george.tv_guideline_margin_set(guideline_pos, margin=10)
    assert george.tv_guideline_margin_get(guideline_pos) == 10
    # Margin Apply All
    george.tv_guideline_margin_set_all(george.GuidelineType.LINE, margin=20)
    assert george.tv_guideline_margin_get(guideline_pos) == 20
    george.tv_guideline_margin_set_all(None, margin=35, apply_all=True)
    assert george.tv_guideline_margin_get(guideline_pos) == 35


def test_grg_guideline_color(guideline_pos: int) -> None:
    test_color = george.RGBAColor(255, 128, 64, 255)
    george.tv_guideline_color_set(guideline_pos, test_color)
    assert george.tv_guideline_color_get(guideline_pos) == test_color
    # Color Apply All
    test_color2 = george.RGBAColor(24, 165, 123, 255)
    george.tv_guideline_color_set_all(george.GuidelineType.LINE, color=test_color2)
    assert george.tv_guideline_color_get(guideline_pos) == test_color2

    test_color3 = george.RGBAColor(76, 46, 58, 255)
    george.tv_guideline_color_set_all(None, color=test_color3, apply_all=True)
    assert george.tv_guideline_color_get(guideline_pos) == test_color3


def test_grg_guideline_snap(guideline_pos: int) -> None:
    # set visibility ot True otherwise snap functions won't work
    george.tv_guideline_visibility_set_all(None, is_visible=True, apply_all=True)

    george.tv_guideline_snap_set(guideline_pos, snap=False)
    assert george.tv_guideline_snap_get(guideline_pos) is False
    george.tv_guideline_snap_set(guideline_pos, snap=True)
    assert george.tv_guideline_snap_get(guideline_pos) is True
    george.tv_guideline_snap_set(guideline_pos, snap=False)
    assert george.tv_guideline_snap_get(guideline_pos) is False
    # Color Snap All
    george.tv_guideline_snap_set_all(george.GuidelineType.LINE, snap=True)
    assert george.tv_guideline_snap_get(guideline_pos) is True
    george.tv_guideline_snap_set_all(None, snap=False, apply_all=True)
    assert george.tv_guideline_snap_get(guideline_pos) is False
    # Snap Global
    george.tv_guideline_snap_set(0, snap=True, on_global=True)
    assert george.tv_guideline_snap_get(0, on_global=True) is True
    george.tv_guideline_snap_set(0, snap=False, on_global=True)
    assert george.tv_guideline_snap_get(0, on_global=True) is False


def test_guideline_image(test_project: george.TVPProject, png_sequence: list[Path]) -> None:
    """Test adding and modifying an image guideline."""
    dummy_img = png_sequence[0]
    guideline_pos = george.tv_guideline_add_image(
        img_path=dummy_img, x=100, y=100, rotation=45, scale=2.0, flip=george.FlipDirection.X
    )

    get_res = george.tv_guideline_modify_image_get(guideline_pos)
    assert get_res.x == 100
    assert get_res.y == 100
    assert get_res.rotation == 45
    assert get_res.scale == 2.0
    assert get_res.flip == george.FlipDirection.X

    george.tv_guideline_modify_image_set(guideline_pos, rotation=90, scale=3.0, flip=george.FlipDirection.Y)

    set_res = george.tv_guideline_modify_image_get(guideline_pos)
    assert set_res.rotation == 90
    assert set_res.scale == 3.0
    assert set_res.flip == george.FlipDirection.Y


def test_guideline_line(test_project: george.TVPProject) -> None:
    """Test adding and modifying a line guideline."""
    guideline_pos = george.tv_guideline_add_line(x=50, y=60, angle=15.5)

    get_res = george.tv_guideline_modify_line_get(guideline_pos)
    assert get_res.x == 50
    assert get_res.y == 60
    assert get_res.angle == 15.5

    george.tv_guideline_modify_line_set(guideline_pos, angle=180)

    set_res = george.tv_guideline_modify_line_get(guideline_pos)
    assert set_res.angle == 180


def test_guideline_segment(test_project: george.TVPProject) -> None:
    """Test adding and modifying a segment guideline."""
    guideline_pos = george.tv_guideline_add_segment(x1=10, y1=10, x2=100, y2=100)

    get_res = george.tv_guideline_modify_segment_get(guideline_pos)
    assert get_res.x1 == 10
    assert get_res.y1 == 10
    assert get_res.x2 == 100
    assert get_res.y2 == 100

    george.tv_guideline_modify_segment_set(guideline_pos, x2=200)
    set_res = george.tv_guideline_modify_segment_get(guideline_pos)
    assert set_res.x2 == 200


def test_guideline_circle(test_project: george.TVPProject) -> None:
    """Test adding and modifying a circle guideline."""
    guideline_pos = george.tv_guideline_add_circle(x=200, y=200, radius=50)

    get_res = george.tv_guideline_modify_circle_get(guideline_pos)
    assert get_res.x == 200
    assert get_res.y == 200
    assert get_res.radius == 50

    george.tv_guideline_modify_circle_set(guideline_pos, radius=75)
    set_res = george.tv_guideline_modify_circle_get(guideline_pos)
    assert set_res.radius == 75


def test_guideline_ellipse(test_project: george.TVPProject) -> None:
    """Test adding and modifying an ellipse guideline."""
    guideline_pos = george.tv_guideline_add_ellipse(x=100, y=100, radius_a=50, radius_b=25)

    get_res = george.tv_guideline_modify_ellipse_get(guideline_pos)
    assert get_res.x == 100
    assert get_res.y == 100
    assert get_res.radius_a == 50
    assert get_res.radius_b == 25

    george.tv_guideline_modify_ellipse_set(guideline_pos, radius_b=30)
    set_res = george.tv_guideline_modify_ellipse_get(guideline_pos)
    assert set_res.radius_b == 30


def test_guideline_grid(test_project: george.TVPProject) -> None:
    """Test adding and modifying a grid guideline."""
    guideline_pos = george.tv_guideline_add_grid(x=0, y=0, width=1920, height=1080)

    get_res = george.tv_guideline_modify_grid_get(guideline_pos)
    assert get_res.x == 0
    assert get_res.y == 0
    assert get_res.width == 1920
    assert get_res.height == 1080

    george.tv_guideline_modify_grid_set(guideline_pos, width=1280, height=720)

    set_res = george.tv_guideline_modify_grid_get(guideline_pos)
    assert set_res.width == 1280
    assert set_res.height == 720


def test_guideline_marks(test_project: george.TVPProject) -> None:
    """Test adding and modifying a marks guideline."""
    guideline_pos = george.tv_guideline_add_marks(count_x=4, count_y=3)

    get_res = george.tv_guideline_modify_marks_get(guideline_pos)
    assert get_res.count_x == 4
    assert get_res.count_y == 3

    # FIXME This function doesn't seem to work in tvpaint, values are never changed !
    # george.tv_guideline_modify_marks_set(guideline_pos, count_x=5)  # noqa: ERA001
    # set_res = george.tv_guideline_modify_marks_get(guideline_pos)  # noqa: ERA001
    # assert set_res.count_x == 5  # noqa: ERA001


def test_guideline_safe_area(test_project: george.TVPProject) -> None:
    """Test adding and modifying a safe area guideline."""
    guideline_pos = george.tv_guideline_add_safe_area(sf_out=10, sf_in=20)

    get_res = george.tv_guideline_modify_safe_area_get(guideline_pos)
    assert get_res.sf_out == 10
    assert get_res.sf_in == 20

    george.tv_guideline_modify_safe_area_set(guideline_pos, sf_in=25)
    set_res = george.tv_guideline_modify_safe_area_get(guideline_pos)
    assert set_res.sf_in == 25


def test_guideline_vanish_point1(test_project: george.TVPProject) -> None:
    """Test adding and modifying vanish point guidelines (1, 2, and 3)."""
    # VP 1
    pos1 = george.tv_guideline_add_vanish_point_1(x=100, y=100, grid=True)
    get_res1 = george.tv_guideline_modify_vanish_point_1_get(pos1)
    assert get_res1.x == 100
    assert get_res1.y == 100
    assert get_res1.grid is True

    george.tv_guideline_modify_vanish_point_1_set(pos1, x=25, grid=False)
    set_res1 = george.tv_guideline_modify_vanish_point_1_get(pos1)
    assert set_res1.x == 25
    assert set_res1.grid is False


def test_guideline_vanish_point2(test_project: george.TVPProject) -> None:
    pos2 = george.tv_guideline_add_vanish_point_2(x1=10, y1=10, x2=100, y2=100)
    get_res2 = george.tv_guideline_modify_vanish_point_2_get(pos2)
    assert get_res2.x1 == 10
    assert get_res2.y1 == 10
    assert get_res2.x2 == 100
    assert get_res2.y2 == 100

    george.tv_guideline_modify_vanish_point_2_set(pos2, y1=20, y2=50, ray=5)
    set_res2 = george.tv_guideline_modify_vanish_point_2_get(pos2)
    assert set_res2.y1 == 20
    assert set_res2.y2 == 50
    assert set_res2.ray == 5


def test_guideline_vanish_point3(test_project: george.TVPProject) -> None:
    pos3 = george.tv_guideline_add_vanish_point_3(x1=10, y1=10, x2=100, y2=100, x3=50, y3=50)
    get_res3 = george.tv_guideline_modify_vanish_point_3_get(pos3)
    assert get_res3.x1 == 10
    assert get_res3.y1 == 10
    assert get_res3.x2 == 100
    assert get_res3.y2 == 100
    assert get_res3.x3 == 50
    assert get_res3.x3 == 50

    george.tv_guideline_modify_vanish_point_3_set(pos3, y1=20, y2=50, y3=60)
    set_res3 = george.tv_guideline_modify_vanish_point_3_get(pos3)
    assert set_res3.y1 == 20
    assert set_res3.y2 == 50
    assert set_res3.y3 == 60


def test_guideline_charts(test_project: george.TVPProject) -> None:
    """Test adding field and animator charts (these typically lack modify endpoints)."""
    pos_field = george.tv_guideline_add_field_chart()
    assert pos_field >= 0

    pos_anim = george.tv_guideline_add_animator_chart()
    assert pos_anim >= 0
