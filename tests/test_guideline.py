import contextlib
from collections.abc import Generator
from pathlib import Path

import pytest

from pytvpaint import george, guideline
from pytvpaint.project import Project


@pytest.fixture(autouse=True)
def clean_guidelines() -> Generator[None, None, None]:
    """Wipe all guidelines before and after each test."""

    def _remove_all() -> None:
        for g_type in george.GuidelineType:
            with contextlib.suppress(Exception):
                george.tv_guideline_remove_all(g_type)

    _remove_all()
    yield
    _remove_all()


def test_guideline_base_properties(test_project_obj: Project) -> None:
    """Test the common properties inherited from the base Guideline class."""
    guideline_obj = guideline.GuidelineLine.new(test_project_obj, x=10, y=10, angle=45)

    assert guideline_obj.position >= 0
    assert guideline_obj.project == test_project_obj

    # Test Name
    guideline_obj.name = "test_line"
    assert guideline_obj.name == "test_line"

    # Test Visibility
    guideline_obj.is_visible = False
    assert guideline_obj.is_visible is False

    # Test Color
    test_color = george.RGBAColor(10, 20, 30, 255)
    guideline_obj.color = test_color
    assert guideline_obj.color == test_color

    # Test Snap
    with pytest.raises(ValueError):
        guideline_obj.snap = True

    guideline_obj.is_visible = True
    guideline_obj.snap = True
    assert guideline_obj.snap is True

    # Test Snap

    # Test Collapse
    guideline_obj.collapse = True
    assert guideline_obj.collapse is True

    # Test Remove / Removable mixin
    assert not guideline_obj.is_removed
    guideline_obj.remove()
    assert guideline_obj.is_removed


def test_guideline_image(test_project_obj: Project, png_sequence: list[Path]) -> None:
    """Test GuidelineImage specific properties."""
    # Grab the first image from the sequence fixture
    test_img = png_sequence[0]

    guideline_obj = guideline.GuidelineImage.new(
        test_project_obj, img_path=test_img, x=10, y=20, rotation=45, scale=2.0, flip=george.FlipDirection.X
    )

    assert guideline_obj.path == test_img
    assert guideline_obj.x == 10
    assert guideline_obj.flip == george.FlipDirection.X

    # Modify property and verify
    guideline_obj.rotation = 90
    assert guideline_obj.rotation == 90
    guideline_obj.scale = 1.5
    assert guideline_obj.scale == 1.5


def test_guideline_line(test_project_obj: Project) -> None:
    """Test GuidelineLine specific properties."""
    guideline_obj = guideline.GuidelineLine.new(test_project_obj, x=50, y=60, angle=15.5)
    assert guideline_obj.x == 50
    assert guideline_obj.y == 60
    assert guideline_obj.angle == 15.5

    guideline_obj.angle = 180
    assert guideline_obj.angle == 180


def test_guideline_segment(test_project_obj: Project) -> None:
    """Test GuidelineSegment specific properties."""
    guideline_obj = guideline.GuidelineSegment.new(test_project_obj, x1=10, y1=10, x2=100, y2=100)
    assert guideline_obj.x1 == 10
    assert guideline_obj.x2 == 100

    guideline_obj.y2 = 200
    assert guideline_obj.y2 == 200


def test_guideline_circle(test_project_obj: Project) -> None:
    """Test GuidelineCircle specific properties."""
    guideline_obj = guideline.GuidelineCircle.new(test_project_obj, x=200, y=200, radius=50)
    assert guideline_obj.radius == 50

    guideline_obj.radius = 75
    assert guideline_obj.radius == 75


def test_guideline_ellipse(test_project_obj: Project) -> None:
    """Test GuidelineEllipse specific properties."""
    guideline_obj = guideline.GuidelineEllipse.new(test_project_obj, x=100, y=100, radius_a=50, radius_b=25)
    assert guideline_obj.radius_a == 50
    assert guideline_obj.radius_b == 25

    guideline_obj.radius_b = 30
    assert guideline_obj.radius_b == 30


def test_guideline_grid(test_project_obj: Project) -> None:
    """Test GuidelineGrid specific properties."""
    guideline_obj = guideline.GuidelineGrid.new(test_project_obj, x=0, y=0, width=1920, height=1080)
    assert guideline_obj.width == 1920
    assert guideline_obj.height == 1080

    guideline_obj.width = 1280
    assert guideline_obj.width == 1280


def test_guideline_marks(test_project_obj: Project) -> None:
    """Test GuidelineMarks specific properties."""
    guideline_obj = guideline.GuidelineMarks.new(test_project_obj, count_x=4, count_y=3)
    assert guideline_obj.count_x == 4

    guideline_obj.count_y = 5


def test_guideline_safe_area(test_project_obj: Project) -> None:
    """Test GuidelineSafeArea specific properties."""
    guideline_obj = guideline.GuidelineSafeArea.new(test_project_obj, sf_out=10, sf_in=20)
    assert guideline_obj.sf_out == 10

    guideline_obj.sf_in = 25
    assert guideline_obj.sf_in == 25


def test_guideline_vanish_point_1(test_project_obj: Project) -> None:
    """Test GuidelineVanishPoint1 specific properties."""
    guideline_obj = guideline.GuidelineVanishPoint1.new(test_project_obj, x=100, y=100, grid=True)
    assert guideline_obj.grid is True

    guideline_obj.grid = False
    assert guideline_obj.grid is False


def test_guideline_vanish_point_2(test_project_obj: Project) -> None:
    """Test GuidelineVanishPoint2 specific properties."""
    guideline_obj = guideline.GuidelineVanishPoint2.new(test_project_obj, x1=10, y1=10, x2=100, y2=100)
    assert guideline_obj.x2 == 100

    guideline_obj.x2 = 150
    assert guideline_obj.x2 == 150


def test_guideline_vanish_point_3(test_project_obj: Project) -> None:
    """Test GuidelineVanishPoint3 specific properties."""
    guideline_obj = guideline.GuidelineVanishPoint3.new(test_project_obj, x1=10, y1=10, x2=100, y2=100, x3=50, y3=50)
    assert guideline_obj.x3 == 50
    assert guideline_obj.y3 == 50

    guideline_obj.y3 = 60
    assert guideline_obj.y3 == 60


def test_guideline_charts(test_project_obj: Project) -> None:
    """Test chart guidelines (which generally don't have modify properties)."""
    # Field Chart
    g_field = guideline.GuidelineFieldChart.new(test_project_obj)
    assert g_field.position >= 0
    assert g_field.TYPE == george.GuidelineType.FIELD_CHART

    # Animator Field
    g_anim = guideline.GuidelineAnimatorField.new(test_project_obj)
    assert g_anim.position >= 0
    assert g_anim.TYPE == george.GuidelineType.ANIMATOR_FIELD
