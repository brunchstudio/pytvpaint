"""Guideline related objects and classes."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar, Generic
from typing import TYPE_CHECKING

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

    TYPE: GuidelineT = None

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

    def refresh(self) -> None:
        """Refreshes the guideline data."""
        super().refresh()

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
    def data(self) -> GuidelineDT:
        """Returns the raw data of the guideline."""
        return self._data

    @property
    def project(self) -> Project:
        """The project instance the guideline belongs to."""
        return self._project

    @property
    def name(self) -> str:
        return george.tv_guideline_name_get(self.position)

    @name.setter
    def name(self, value: str) -> None:
        george.tv_guideline_name_set(self.position, value)

    @property
    def is_visible(self) -> bool:
        return george.tv_guideline_visibility_get(self.position)

    @is_visible.setter
    def is_visible(self, value: bool) -> None:
        george.tv_guideline_visibility_set(self.position, value)

    @property
    def margin(self) -> int:
        return george.tv_guideline_margin_get(self.position)

    @margin.setter
    def margin(self, value: int) -> None:
        george.tv_guideline_margin_set(self.position, value)

    @property
    def color(self) -> george.RGBAColor:
        return george.tv_guideline_color_get(self.position)

    @color.setter
    def color(self, value: george.RGBAColor) -> None:
        george.tv_guideline_color_set(self.position, value)

    @property
    def snap(self) -> bool:
        return george.tv_guideline_snap_get(self.position)

    @snap.setter
    def snap(self, value: bool) -> None:
        george.tv_guideline_snap_set(self.position, value)

    @property
    def collapse(self) -> bool:
        return george.tv_guideline_collapse_get(self.position)

    @collapse.setter
    def collapse(self, value: bool) -> None:
        george.tv_guideline_collapse_set(self.position, value)

    def remove(self) -> None:
        """Remove the guideline.

        Warning:
            the guideline instance won't be usable after removal
        """
        if self.TYPE:
            george.tv_guideline_remove(self.position, self.TYPE)
        self.mark_removed()


class GuidelineImage(Guideline[george.TVPGuidelineImage, george.GuidelineType]):

    TYPE = george.GuidelineType.IMAGE

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineImage | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data = data or george.tv_guideline_modify_image_get(self._position)

    def refresh(self) -> None:
        """Refreshes the camera point data."""
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

    TYPE = george.GuidelineType.LINE

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineLine | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data = data or george.tv_guideline_modify_line_get(self._position)

    def refresh(self) -> None:
        """Refreshes the camera point data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_line_get(self._position)


class GuidelineSegment(Guideline[george.TVPGuidelineSegment, george.GuidelineType]):

    TYPE = george.GuidelineType.SEGMENT

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineSegment | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data = data or george.tv_guideline_modify_segment_get(self._position)

    def refresh(self) -> None:
        """Refreshes the camera point data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_segment_get(self._position)


class GuidelineCircle(Guideline[george.TVPGuidelineCircle, george.GuidelineType]):

    TYPE = george.GuidelineType.CIRCLE

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineCircle | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data = data or george.tv_guideline_modify_circle_get(self._position)

    def refresh(self) -> None:
        """Refreshes the camera point data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_circle_get(self._position)


class GuidelineEllipse(Guideline[george.TVPGuidelineEllipse, george.GuidelineType]):

    TYPE = george.GuidelineType.ELLIPSE

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineEllipse | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data = data or george.tv_guideline_modify_ellipse_get(self._position)

    def refresh(self) -> None:
        """Refreshes the camera point data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_ellipse_get(self._position)


class GuidelineGrid(Guideline[george.TVPGuidelineGrid, george.GuidelineType]):

    TYPE = george.GuidelineType.GRID

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineGrid | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data = data or george.tv_guideline_modify_grid_get(self._position)

    def refresh(self) -> None:
        """Refreshes the camera point data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_grid_get(self._position)


class GuidelineMarks(Guideline[george.TVPGuidelineMarks, george.GuidelineType]):

    TYPE = george.GuidelineType.MARKS

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineMarks | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data = data or george.tv_guideline_modify_marks_get(self._position)

    def refresh(self) -> None:
        """Refreshes the camera point data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_marks_get(self._position)


class GuidelineFieldChart(Guideline[george.TVPGuideField, george.GuidelineType]):

    TYPE = george.GuidelineType.FIELD_CHART

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuideField | None = None,
    ) -> None:
        super().__init__(position, project, data)


class GuidelineAnimatorField(Guideline[george.TVPGuideField, george.GuidelineType]):

    TYPE = george.GuidelineType.ANIMATOR_FIELD

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuideField | None = None,
    ) -> None:
        super().__init__(position, project, data)


class GuidelineSafeArea(Guideline[george.TVPGuidelineSafeArea, george.GuidelineType]):

    TYPE = george.GuidelineType.SAFE_AREA

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineSafeArea | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data = data or george.tv_guideline_modify_safe_area_get(self._position)

    def refresh(self) -> None:
        """Refreshes the camera point data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_safe_area_get(self._position)


class GuidelineVanishPoint1(Guideline[george.TVPGuidelineVanishPoint1, george.GuidelineType]):

    TYPE = george.GuidelineType.VANISH_POINT_1

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineVanishPoint1 | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data = data or george.tv_guideline_modify_vanish_point_1_get(self._position)

    def refresh(self) -> None:
        """Refreshes the camera point data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_vanish_point_1_get(self._position)


class GuidelineVanishPoint2(Guideline[george.TVPGuidelineVanishPoint2, george.GuidelineType]):

    TYPE = george.GuidelineType.VANISH_POINT_2

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineVanishPoint2 | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data = data or george.tv_guideline_modify_vanish_point_2_get(self._position)

    def refresh(self) -> None:
        """Refreshes the camera point data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_vanish_point_2_get(self._position)


class GuidelineVanishPoint3(Guideline[george.TVPGuidelineVanishPoint3, george.GuidelineType]):

    TYPE = george.GuidelineType.VANISH_POINT_3

    def __init__(
        self,
        position: int,
        project: Project,
        data: george.TVPGuidelineVanishPoint3 | None = None,
    ) -> None:
        super().__init__(position, project)
        self._data = data or george.tv_guideline_modify_vanish_point_3_get(self._position)

    def refresh(self) -> None:
        """Refreshes the camera point data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_guideline_modify_vanish_point_3_get(self._position)
