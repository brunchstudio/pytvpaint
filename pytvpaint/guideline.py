"""Guideline related objects and classes."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Generic, TypeVar

from pytvpaint import george
from pytvpaint.utils import (
    Removable,
    refreshed_property,
)

if TYPE_CHECKING:
    from pytvpaint.project import Project

GuidelineDT = TypeVar("GuidelineDT")
GuidelineT = TypeVar("GuidelineT", bound=george.GuidelineType)


class Guideline(Removable, Generic[GuidelineDT, GuidelineT]):
    """A Guideline is an image or shape used as guideline for artists."""

    TYPE: GuidelineT

    def __init__(
        self,
        position: int,
        project: Project,
        data: GuidelineDT | None = None,
    ) -> None:
        super().__init__()
        self._position: int = position
        self._project: Project = project
        self._data = data

    def __repr__(self) -> str:
        """String representation of the camera point."""
        return f"{self.__class__.__name__}({self.name})<pos:{self.position}>"

    def __eq__(self, other: object) -> bool:
        """Two camera points are equal if their internal data is the same."""
        if not isinstance(other, self.__class__):
            return NotImplemented

        self.refresh()
        other.refresh()
        return self.position == other.position and self._data == other._data

    @property
    def position(self) -> int:
        """The position of the guideline."""
        return self._position

    @property
    def data(self) -> GuidelineDT | None:
        """Returns the raw data of the guideline."""
        return self._data

    @property
    def project(self) -> Project:
        """The project instance the guideline belongs to."""
        return self._project

    @property
    def name(self) -> str:
        """The name of the guideline."""
        return george.tv_guideline_name_get(self.position)

    @name.setter
    def name(self, value: str) -> None:
        george.tv_guideline_name_set(self.position, value)

    @property
    def is_visible(self) -> bool:
        """The guideline visibility."""
        return george.tv_guideline_visibility_get(self.position)

    @is_visible.setter
    def is_visible(self, value: bool) -> None:
        george.tv_guideline_visibility_set(self.position, value)

    @property
    def margin(self) -> int:
        """The guideline margin."""
        return george.tv_guideline_margin_get(self.position)

    @margin.setter
    def margin(self, value: int) -> None:
        george.tv_guideline_margin_set(self.position, value)

    @property
    def color(self) -> george.RGBAColor:
        """The guideline color."""
        return george.tv_guideline_color_get(self.position)

    @color.setter
    def color(self, value: george.RGBAColor) -> None:
        george.tv_guideline_color_set(self.position, value)

    @property
    def snap(self) -> bool:
        """The guideline snap state."""
        return george.tv_guideline_snap_get(self.position)

    @snap.setter
    def snap(self, value: bool) -> None:
        if not self.is_visible:
            raise ValueError("Snap will not change if guideline is not visible")
        george.tv_guideline_snap_set(self.position, value)

    @property
    def collapse(self) -> bool:
        """The guideline collapse state."""
        return george.tv_guideline_collapse_get(self.position)

    @collapse.setter
    def collapse(self, value: bool) -> None:
        george.tv_guideline_collapse_set(self.position, value)

    @classmethod
    def set_all_visible(cls, value: bool) -> None:
        """Set visibility state on all guidelines."""
        george.tv_guideline_visibility_set_all(cls.TYPE, value)

    @classmethod
    def set_all_margin(cls, value: int) -> None:
        """Set the margin on all guidelines."""
        george.tv_guideline_margin_set_all(cls.TYPE, value)

    @classmethod
    def set_all_color(cls, value: george.RGBAColor) -> None:
        """Set the color on all guidelines."""
        george.tv_guideline_color_set_all(cls.TYPE, value)

    @classmethod
    def set_all_snap(cls, value: bool) -> None:
        """Set the snap state on all guidelines."""
        george.tv_guideline_snap_set_all(cls.TYPE, value)

    @staticmethod
    def set_global_visible(value: bool) -> None:
        """Set the visibility on the global guideline."""
        george.tv_guideline_visibility_set(0, value, on_global=True)

    @staticmethod
    def set_global_snap(value: bool) -> None:
        """Set snap state on the global guideline."""
        george.tv_guideline_snap_set(0, value, on_global=True)

    def remove(self) -> None:
        """Remove the guideline.

        Warning:
            the guideline instance won't be usable after removal
        """
        if self.TYPE:
            george.tv_guideline_remove(self.position, self.TYPE)
        self.mark_removed()


class GuidelineImage(Guideline[george.TVPGuidelineImage, george.GuidelineType]):
    """A GuidelineImage is an image used as guideline for artists."""

    TYPE = george.GuidelineType.IMAGE

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineImage | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data: george.TVPGuidelineImage = data or george.tv_guideline_modify_image_get(self._position)

    def refresh(self) -> None:
        """Refreshes the guideline data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_image_get(self._position)

    @refreshed_property
    def path(self) -> Path:
        """The image path."""
        return self._data.path

    @path.setter
    def path(self, value: Path | str) -> None:
        george.tv_guideline_modify_image_set(self.position, img_path=value)

    @refreshed_property
    def x(self) -> float:
        """The x coordinate of the image."""
        return self._data.x

    @x.setter
    def x(self, value: float) -> None:
        george.tv_guideline_modify_image_set(self.position, x=value)

    @refreshed_property
    def y(self) -> float:
        """The y coordinate of the image."""
        return self._data.y

    @y.setter
    def y(self, value: float) -> None:
        george.tv_guideline_modify_image_set(self.position, y=value)

    @refreshed_property
    def rotation(self) -> float:
        """The rotation of the image."""
        return self._data.rotation

    @rotation.setter
    def rotation(self, value: float) -> None:
        george.tv_guideline_modify_image_set(self.position, rotation=value)

    @refreshed_property
    def scale(self) -> float:
        """The scale of the image."""
        return self._data.scale

    @scale.setter
    def scale(self, value: float) -> None:
        george.tv_guideline_modify_image_set(self.position, scale=value)

    @refreshed_property
    def flip(self) -> george.FlipDirection:
        """The orientation of the image."""
        return self._data.flip

    @flip.setter
    def flip(self, value: george.FlipDirection) -> None:
        george.tv_guideline_modify_image_set(self.position, flip=value)

    @classmethod
    def new(
        cls,
        project: Project,
        img_path: Path | str | None = None,
        x: float | None = None,
        y: float | None = None,
        rotation: float | None = None,
        scale: float | None = None,
        flip: george.FlipDirection | None = None,
        alpha_mode: george.GuidelineAlphaMode | None = None,
    ) -> GuidelineImage:
        """Create a new guideline in the project."""
        project.make_current()

        position = george.tv_guideline_add_image(img_path, x, y, rotation, scale, flip, alpha_mode)
        return cls(position, project)


class GuidelineLine(Guideline[george.TVPGuidelineLine, george.GuidelineType]):
    """A GuidelineLine is a line used as guideline for artists."""

    TYPE = george.GuidelineType.LINE

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineLine | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data: george.TVPGuidelineLine = data or george.tv_guideline_modify_line_get(self._position)

    def refresh(self) -> None:
        """Refreshes the guideline data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_line_get(self._position)

    @refreshed_property
    def x(self) -> float:
        """The x coordinate of the guideline."""
        return self._data.x

    @x.setter
    def x(self, value: float) -> None:
        george.tv_guideline_modify_line_set(self.position, x=value)

    @refreshed_property
    def y(self) -> float:
        """The y coordinate of the guideline."""
        return self._data.y

    @y.setter
    def y(self, value: float) -> None:
        george.tv_guideline_modify_line_set(self.position, y=value)

    @refreshed_property
    def angle(self) -> float:
        """The angle of the guideline."""
        return self._data.angle

    @angle.setter
    def angle(self, value: float) -> None:
        george.tv_guideline_modify_line_set(self.position, angle=value)

    @classmethod
    def new(
        cls,
        project: Project,
        x: float | None = None,
        y: float | None = None,
        angle: float | None = None,
    ) -> GuidelineLine:
        """Create a new guideline in the project."""
        project.make_current()

        position = george.tv_guideline_add_line(x, y, angle)
        return cls(position, project)


class GuidelineSegment(Guideline[george.TVPGuidelineSegment, george.GuidelineType]):
    """A GuidelineSegment is a segment drawing used as guideline for artists."""

    TYPE = george.GuidelineType.SEGMENT

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineSegment | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data: george.TVPGuidelineSegment = data or george.tv_guideline_modify_segment_get(self._position)

    def refresh(self) -> None:
        """Refreshes the guideline data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_segment_get(self._position)

    @refreshed_property
    def x1(self) -> float:
        """The x coordinate of the guideline."""
        return self._data.x1

    @x1.setter
    def x1(self, value: float) -> None:
        george.tv_guideline_modify_segment_set(self.position, x1=value)

    @refreshed_property
    def y1(self) -> float:
        """The y coordinate of the guideline."""
        return self._data.y1

    @y1.setter
    def y1(self, value: float) -> None:
        george.tv_guideline_modify_segment_set(self.position, y1=value)

    @refreshed_property
    def x2(self) -> float:
        """The x2 coordinate of the guideline."""
        return self._data.x2

    @x2.setter
    def x2(self, value: float) -> None:
        george.tv_guideline_modify_segment_set(self.position, x2=value)

    @refreshed_property
    def y2(self) -> float:
        """The y2 coordinate of the guideline."""
        return self._data.y2

    @y2.setter
    def y2(self, value: float) -> None:
        george.tv_guideline_modify_segment_set(self.position, y2=value)

    @classmethod
    def new(
        cls,
        project: Project,
        x1: float | None = None,
        y1: float | None = None,
        x2: float | None = None,
        y2: float | None = None,
    ) -> GuidelineSegment:
        """Create a new guideline in the project."""
        project.make_current()

        position = george.tv_guideline_add_segment(x1, y1, x2, y2)
        return cls(position, project)


class GuidelineCircle(Guideline[george.TVPGuidelineCircle, george.GuidelineType]):
    """A GuidelineCircle is a circle used as guideline for artists."""

    TYPE = george.GuidelineType.CIRCLE

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineCircle | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data: george.TVPGuidelineCircle = data or george.tv_guideline_modify_circle_get(self._position)

    def refresh(self) -> None:
        """Refreshes the guideline data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_circle_get(self._position)

    @refreshed_property
    def x(self) -> float:
        """The x coordinate of the guideline."""
        return self._data.x

    @x.setter
    def x(self, value: float) -> None:
        george.tv_guideline_modify_circle_set(self.position, x=value)

    @refreshed_property
    def y(self) -> float:
        """The y coordinate of the guideline."""
        return self._data.y

    @y.setter
    def y(self, value: float) -> None:
        george.tv_guideline_modify_circle_set(self.position, y=value)

    @refreshed_property
    def radius(self) -> float:
        """The radius of the guideline."""
        return self._data.radius

    @radius.setter
    def radius(self, value: float) -> None:
        george.tv_guideline_modify_circle_set(self.position, radius=value)

    @classmethod
    def new(
        cls,
        project: Project,
        x: float | None = None,
        y: float | None = None,
        radius: float | None = None,
    ) -> GuidelineCircle:
        """Create a new guideline in the project."""
        project.make_current()

        position = george.tv_guideline_add_circle(x, y, radius)
        return cls(position, project)


class GuidelineEllipse(Guideline[george.TVPGuidelineEllipse, george.GuidelineType]):
    """A GuidelineEllipse is an ellipse used as guideline for artists."""

    TYPE = george.GuidelineType.ELLIPSE

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineEllipse | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data: george.TVPGuidelineEllipse = data or george.tv_guideline_modify_ellipse_get(self._position)

    def refresh(self) -> None:
        """Refreshes the guideline data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_ellipse_get(self._position)

    @refreshed_property
    def x(self) -> float:
        """The x coordinate of the guideline."""
        return self._data.x

    @x.setter
    def x(self, value: float) -> None:
        george.tv_guideline_modify_ellipse_set(self.position, x=value)

    @refreshed_property
    def y(self) -> float:
        """The y coordinate of the guideline."""
        return self._data.y

    @y.setter
    def y(self, value: float) -> None:
        george.tv_guideline_modify_ellipse_set(self.position, y=value)

    @refreshed_property
    def radius_a(self) -> float:
        """The radius_a of the guideline."""
        return self._data.radius_a

    @radius_a.setter
    def radius_a(self, value: float) -> None:
        george.tv_guideline_modify_ellipse_set(self.position, radius_a=value)

    @refreshed_property
    def radius_b(self) -> float:
        """The radius_b of the guideline."""
        return self._data.radius_b

    @radius_b.setter
    def radius_b(self, value: float) -> None:
        george.tv_guideline_modify_ellipse_set(self.position, radius_b=value)

    @classmethod
    def new(
        cls,
        project: Project,
        x: float | None = None,
        y: float | None = None,
        radius_a: float | None = None,
        radius_b: float | None = None,
    ) -> GuidelineEllipse:
        """Create a new guideline in the project."""
        project.make_current()

        position = george.tv_guideline_add_ellipse(x, y, radius_a, radius_b)
        return cls(position, project)


class GuidelineGrid(Guideline[george.TVPGuidelineGrid, george.GuidelineType]):
    """A GuidelineGrid is a grid used as guideline for artists."""

    TYPE = george.GuidelineType.GRID

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineGrid | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data: george.TVPGuidelineGrid = data or george.tv_guideline_modify_grid_get(self._position)

    def refresh(self) -> None:
        """Refreshes the guideline data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_grid_get(self._position)

    @refreshed_property
    def x(self) -> float:
        """The x coordinate of the guideline."""
        return self._data.x

    @x.setter
    def x(self, value: float) -> None:
        george.tv_guideline_modify_grid_set(self.position, x=value)

    @refreshed_property
    def y(self) -> float:
        """The y coordinate of the guideline."""
        return self._data.y

    @y.setter
    def y(self, value: float) -> None:
        george.tv_guideline_modify_grid_set(self.position, y=value)

    @refreshed_property
    def width(self) -> float:
        """The width of the guideline."""
        return self._data.width

    @width.setter
    def width(self, value: float) -> None:
        george.tv_guideline_modify_grid_set(self.position, width=value)

    @refreshed_property
    def height(self) -> float:
        """The height of the guideline."""
        return self._data.height

    @height.setter
    def height(self, value: float) -> None:
        george.tv_guideline_modify_grid_set(self.position, height=value)

    @classmethod
    def new(
        cls,
        project: Project,
        x: float | None = None,
        y: float | None = None,
        width: float | None = None,
        height: float | None = None,
    ) -> GuidelineGrid:
        """Create a new guideline in the project."""
        project.make_current()

        position = george.tv_guideline_add_grid(x, y, width, height)
        return cls(position, project)


class GuidelineMarks(Guideline[george.TVPGuidelineMarks, george.GuidelineType]):
    """A GuidelineCircle is a set of marks used as guidelines for artists."""

    TYPE = george.GuidelineType.MARKS

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineMarks | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data: george.TVPGuidelineMarks = data or george.tv_guideline_modify_marks_get(self._position)

    def refresh(self) -> None:
        """Refreshes the guideline data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_marks_get(self._position)

    @refreshed_property
    def count_x(self) -> int:
        """The number of vertical marks."""
        return self._data.count_x

    @count_x.setter
    def count_x(self, value: int) -> None:
        """The number of vertical marks.

        Warning:
            function GuidelineMarks.x doesn't seem to work in tvpaint, values are never changed.
        """
        george.tv_guideline_modify_marks_set(self.position, count_x=value)

    @refreshed_property
    def count_y(self) -> int:
        """The number of horizontal marks."""
        return self._data.count_y

    @count_y.setter
    def count_y(self, value: int) -> None:
        """The number of vertical marks.

        Warning:
            function GuidelineMarks.y doesn't seem to work in tvpaint, values are never changed.
        """
        george.tv_guideline_modify_marks_set(self.position, count_y=value)

    @classmethod
    def new(
        cls,
        project: Project,
        count_x: int | None = None,
        count_y: int | None = None,
    ) -> GuidelineMarks:
        """Create a new guideline in the project."""
        project.make_current()

        position = george.tv_guideline_add_marks(count_x, count_y)
        return cls(position, project)


class GuidelineFieldChart(Guideline[george.TVPGuideField, george.GuidelineType]):
    """A GuidelineFieldChart is a field chart used as guideline for artists."""

    TYPE = george.GuidelineType.FIELD_CHART

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuideField | None = None,
    ) -> None:
        super().__init__(position, project, data)

    @classmethod
    def new(cls, project: Project) -> GuidelineFieldChart:
        """Create a new guideline in the project."""
        project.make_current()

        position = george.tv_guideline_add_field_chart()
        return cls(position, project)


class GuidelineAnimatorField(Guideline[george.TVPGuideField, george.GuidelineType]):
    """A GuidelineAnimatorField is a shape used as guideline for artists."""

    TYPE = george.GuidelineType.ANIMATOR_FIELD

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuideField | None = None,
    ) -> None:
        super().__init__(position, project, data)

    @classmethod
    def new(cls, project: Project) -> GuidelineAnimatorField:
        """Create a new guideline in the project."""
        project.make_current()

        position = george.tv_guideline_add_animator_chart()
        return cls(position, project)


class GuidelineSafeArea(Guideline[george.TVPGuidelineSafeArea, george.GuidelineType]):
    """A GuidelineSafeArea is an area used as guideline for artists."""

    TYPE = george.GuidelineType.SAFE_AREA

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineSafeArea | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data: george.TVPGuidelineSafeArea = data or george.tv_guideline_modify_safe_area_get(self._position)

    def refresh(self) -> None:
        """Refreshes the guideline data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_safe_area_get(self._position)

    @refreshed_property
    def sf_out(self) -> float:
        """The out value of the safe area."""
        return self._data.sf_out

    @sf_out.setter
    def sf_out(self, value: float) -> None:
        george.tv_guideline_modify_safe_area_set(self.position, sf_out=value)

    @refreshed_property
    def sf_in(self) -> float:
        """The in value of the safe area."""
        return self._data.sf_in

    @sf_in.setter
    def sf_in(self, value: float) -> None:
        george.tv_guideline_modify_safe_area_set(self.position, sf_in=value)

    @classmethod
    def new(
        cls,
        project: Project,
        sf_out: int | None = None,
        sf_in: int | None = None,
    ) -> GuidelineSafeArea:
        """Create a new guideline in the project."""
        project.make_current()

        position = george.tv_guideline_add_safe_area(sf_out, sf_in)
        return cls(position, project)


class GuidelineVanishPoint1(Guideline[george.TVPGuidelineVanishPoint1, george.GuidelineType]):
    """A GuidelineVanishPoint1 is a point used as guideline for artists."""

    TYPE = george.GuidelineType.VANISH_POINT_1

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineVanishPoint1 | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data: george.TVPGuidelineVanishPoint1 = data or george.tv_guideline_modify_vanish_point_1_get(
            self._position
        )

    def refresh(self) -> None:
        """Refreshes the guideline data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_vanish_point_1_get(self._position)

    @refreshed_property
    def x(self) -> float:
        """The x coordinate of the guideline."""
        return self._data.x

    @x.setter
    def x(self, value: float) -> None:
        george.tv_guideline_modify_vanish_point_1_set(self.position, x=value)

    @refreshed_property
    def y(self) -> float:
        """The y coordinate of the guideline."""
        return self._data.y

    @y.setter
    def y(self, value: float) -> None:
        george.tv_guideline_modify_vanish_point_1_set(self.position, y=value)

    @refreshed_property
    def ray(self) -> int:
        """The number of rays in the guideline."""
        return self._data.ray

    @ray.setter
    def ray(self, value: int) -> None:
        george.tv_guideline_modify_vanish_point_1_set(self.position, ray=value)

    @refreshed_property
    def grid(self) -> bool:
        """The grid state of the guideline."""
        return self._data.grid

    @grid.setter
    def grid(self, value: bool) -> None:
        george.tv_guideline_modify_vanish_point_1_set(self.position, grid=value)

    @classmethod
    def new(
        cls,
        project: Project,
        x: float | None = None,
        y: float | None = None,
        grid: bool | None = None,
    ) -> GuidelineVanishPoint1:
        """Create a new guideline in the project."""
        project.make_current()

        position = george.tv_guideline_add_vanish_point_1(x, y, grid)
        return cls(position, project)


class GuidelineVanishPoint2(Guideline[george.TVPGuidelineVanishPoint2, george.GuidelineType]):
    """A GuidelineVanishPoint2 is a set of points used as guideline for artists."""

    TYPE = george.GuidelineType.VANISH_POINT_2

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineVanishPoint2 | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data: george.TVPGuidelineVanishPoint2 = data or george.tv_guideline_modify_vanish_point_2_get(
            self._position
        )

    def refresh(self) -> None:
        """Refreshes the guideline data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_vanish_point_2_get(self._position)

    @refreshed_property
    def x1(self) -> float:
        """The x1 coordinate of the guideline."""
        return self._data.x1

    @x1.setter
    def x1(self, value: float) -> None:
        george.tv_guideline_modify_vanish_point_2_set(self.position, x1=value)

    @refreshed_property
    def y1(self) -> float:
        """The y1 coordinate of the guideline."""
        return self._data.y1

    @y1.setter
    def y1(self, value: float) -> None:
        george.tv_guideline_modify_vanish_point_2_set(self.position, y1=value)

    @refreshed_property
    def x2(self) -> float:
        """The x2 coordinate of the guideline."""
        return self._data.x2

    @x2.setter
    def x2(self, value: float) -> None:
        george.tv_guideline_modify_vanish_point_2_set(self.position, x2=value)

    @refreshed_property
    def y2(self) -> float:
        """The y2 coordinate of the guideline."""
        return self._data.y2

    @y2.setter
    def y2(self, value: float) -> None:
        george.tv_guideline_modify_vanish_point_2_set(self.position, y2=value)

    @refreshed_property
    def ray(self) -> int:
        """The number of rays in the guideline."""
        return self._data.ray

    @ray.setter
    def ray(self, value: int) -> None:
        george.tv_guideline_modify_vanish_point_2_set(self.position, ray=value)

    @classmethod
    def new(
        cls,
        project: Project,
        x1: float | None = None,
        y1: float | None = None,
        x2: float | None = None,
        y2: float | None = None,
    ) -> GuidelineVanishPoint2:
        """Create a new guideline in the project."""
        project.make_current()

        position = george.tv_guideline_add_vanish_point_2(x1, y1, x2, y2)
        return cls(position, project)


class GuidelineVanishPoint3(Guideline[george.TVPGuidelineVanishPoint3, george.GuidelineType]):
    """A GuidelineVanishPoint3 is a set of points used as guideline for artists."""

    TYPE = george.GuidelineType.VANISH_POINT_3

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineVanishPoint3 | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data: george.TVPGuidelineVanishPoint3 = data or george.tv_guideline_modify_vanish_point_3_get(
            self._position
        )

    def refresh(self) -> None:
        """Refreshes the guideline data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_vanish_point_3_get(self._position)

    @refreshed_property
    def x1(self) -> float:
        """The x1 coordinate of the guideline."""
        return self._data.x1

    @x1.setter
    def x1(self, value: float) -> None:
        george.tv_guideline_modify_vanish_point_3_set(self.position, x1=value)

    @refreshed_property
    def y1(self) -> float:
        """The y1 coordinate of the guideline."""
        return self._data.y1

    @y1.setter
    def y1(self, value: float) -> None:
        george.tv_guideline_modify_vanish_point_3_set(self.position, y1=value)

    @refreshed_property
    def x2(self) -> float:
        """The x2 coordinate of the guideline."""
        return self._data.x2

    @x2.setter
    def x2(self, value: float) -> None:
        george.tv_guideline_modify_vanish_point_3_set(self.position, x2=value)

    @refreshed_property
    def y2(self) -> float:
        """The y2 coordinate of the guideline."""
        return self._data.y2

    @y2.setter
    def y2(self, value: float) -> None:
        george.tv_guideline_modify_vanish_point_3_set(self.position, y2=value)

    @refreshed_property
    def x3(self) -> float:
        """The x3 coordinate of the guideline."""
        return self._data.y3

    @x3.setter
    def x3(self, value: float) -> None:
        george.tv_guideline_modify_vanish_point_3_set(self.position, x3=value)

    @refreshed_property
    def y3(self) -> float:
        """The y3 coordinate of the guideline."""
        return self._data.y3

    @y3.setter
    def y3(self, value: float) -> None:
        george.tv_guideline_modify_vanish_point_3_set(self.position, y3=value)

    @refreshed_property
    def ray(self) -> int:
        """The number of rays in the guideline."""
        return self._data.ray

    @ray.setter
    def ray(self, value: int) -> None:
        george.tv_guideline_modify_vanish_point_3_set(self.position, ray=value)

    @classmethod
    def new(
        cls,
        project: Project,
        x1: float | None = None,
        y1: float | None = None,
        x2: float | None = None,
        y2: float | None = None,
        x3: float | None = None,
        y3: float | None = None,
    ) -> GuidelineVanishPoint3:
        """Create a new guideline in the project."""
        project.make_current()

        position = george.tv_guideline_add_vanish_point_3(x1, y1, x2, y2, x3, y3)
        return cls(position, project)
