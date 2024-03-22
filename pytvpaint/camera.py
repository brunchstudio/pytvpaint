"""Camera related objects and classes."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from pytvpaint import george, utils
from pytvpaint.utils import (
    Refreshable,
    Removable,
    refreshed_property,
    set_as_current,
)

if TYPE_CHECKING:
    from pytvpaint.clip import Clip


class Camera(Refreshable):
    """The Camera class represents the camera in a TVPaint clip.

    There's only one camera in the clip so instantiating multiple objects of this class won't create cameras.
    """

    def __init__(self, clip: Clip, data: george.TVPCamera | None = None) -> None:
        super().__init__()
        self._clip = clip
        self._data: george.TVPCamera = data or george.tv_camera_info_get()
        self._points: list[CameraPoint] = []

    def refresh(self) -> None:
        """Refreshed the camera data."""
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_camera_info_get()

    def __repr__(self) -> str:
        """String representation of the camera."""
        return f"Camera()[{self.clip}]"

    @property
    def clip(self) -> Clip:
        """The camera's clip."""
        return self._clip

    def make_current(self) -> None:
        """Makes the parent clip the current one, thereby making sure the correct camera will be set."""
        self._clip.make_current()

    @refreshed_property
    @set_as_current
    def width(self) -> int:
        """The sensor width of the camera."""
        return self._data.width

    @width.setter
    @set_as_current
    def width(self, value: int) -> None:
        george.tv_camera_info_set(width=value, height=self.height)

    @refreshed_property
    @set_as_current
    def height(self) -> int:
        """The sensor height of the camera."""
        return self._data.height

    @height.setter
    @set_as_current
    def height(self, value: int) -> None:
        george.tv_camera_info_set(height=value, width=self.width)

    @refreshed_property
    @set_as_current
    def fps(self) -> float:
        """The framerate of the camera."""
        return self._data.frame_rate

    @fps.setter
    @set_as_current
    def fps(self, value: float) -> None:
        george.tv_camera_info_set(
            self.width,
            self.height,
            self.field_order,
            frame_rate=value,
        )

    @refreshed_property
    @set_as_current
    def pixel_aspect_ratio(self) -> float:
        """The pixel aspect ratio of the camera."""
        return self._data.pixel_aspect_ratio

    @pixel_aspect_ratio.setter
    @set_as_current
    def pixel_aspect_ratio(self, value: float) -> None:
        george.tv_camera_info_set(
            self.width,
            self.height,
            self.field_order,
            self.fps,
            pixel_aspect_ratio=value,
        )

    @refreshed_property
    @set_as_current
    def anti_aliasing(self) -> int:
        """The antialiasing value of the camera."""
        return self._data.anti_aliasing

    @refreshed_property
    @set_as_current
    def field_order(self) -> george.FieldOrder:
        """The field order of the camera."""
        return self._data.field_order

    @field_order.setter
    @set_as_current
    def field_order(self, value: george.FieldOrder) -> None:
        george.tv_camera_info_set(self.width, self.height, field_order=value)

    @set_as_current
    def insert_point(
        self,
        index: int,
        x: int,
        y: int,
        angle: int,
        scale: float,
    ) -> CameraPoint:
        """Insert a new point in the camera path."""
        return CameraPoint.new(self, index, x, y, angle, scale)

    @property
    @set_as_current
    def points(self) -> Iterator[CameraPoint]:
        """Iterator for the `CameraPoint` objects of the camera."""
        points_data = utils.position_generator(
            lambda pos: george.tv_camera_enum_points(pos)
        )
        for index, point_data in enumerate(points_data):
            yield CameraPoint(index, camera=self, data=point_data)

    @set_as_current
    def get_point_data_at(self, position: float) -> george.TVPCameraPoint:
        """Get the points data interpolated at that position (between 0 and 1)."""
        position = max(0.0, min(position, 1.0))
        return george.tv_camera_interpolation(position)

    @set_as_current
    def remove_point(self, index: int) -> None:
        """Remove a point at that index."""
        try:
            point = next(p for i, p in enumerate(self.points) if i == index)
            point.remove()
        except StopIteration:
            pass


class CameraPoint(Removable):
    """A CameraPoint is a point on the camera path.

    You can use them to animate the camera movement.
    """

    def __init__(
        self,
        index: int,
        camera: Camera,
        data: george.TVPCameraPoint | None = None,
    ) -> None:
        super().__init__()
        self._index: int = index
        self._camera: Camera = camera
        self._data = data or george.tv_camera_enum_points(self._index)

    def refresh(self) -> None:
        """Refreshed the camera point data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_camera_enum_points(self._index)

    def __repr__(self) -> str:
        """String representation of the camera point."""
        return f"CameraPoint({self.camera.clip.name})<index:{self._index}>"

    def __eq__(self, other: object) -> bool:
        """Two camera points are equal if their internal data is the same."""
        if not isinstance(other, CameraPoint):
            return NotImplemented
        self.refresh()
        other.refresh()
        return self._data == other._data

    @property
    def data(self) -> george.TVPCameraPoint:
        """Returns the raw data of the point."""
        return self._data

    @property
    def index(self) -> int:
        """The index of the point in the path."""
        return self._index

    @property
    def camera(self) -> Camera:
        """The camera instance it belongs to."""
        return self._camera

    @refreshed_property
    def x(self) -> float:
        """The x coordinate of the point."""
        return self._data.x

    @x.setter
    def x(self, value: float) -> None:
        current_data = george.tv_camera_enum_points(self.index)
        george.tv_camera_set_point(
            self.index,
            x=value,
            y=current_data.y,
            angle=current_data.angle,
            scale=current_data.scale,
        )

    @refreshed_property
    def y(self) -> float:
        """The y coordinate of the point."""
        return self._data.y

    @y.setter
    def y(self, value: float) -> None:
        current_data = george.tv_camera_enum_points(self.index)
        george.tv_camera_set_point(
            self.index,
            x=current_data.x,
            y=value,
            angle=current_data.angle,
            scale=current_data.scale,
        )

    @refreshed_property
    def angle(self) -> float:
        """The angle of the camera at that point."""
        return self._data.angle

    @angle.setter
    def angle(self, value: float) -> None:
        current_data = george.tv_camera_enum_points(self.index)
        george.tv_camera_set_point(
            self.index,
            x=current_data.x,
            y=current_data.y,
            angle=value,
            scale=current_data.scale,
        )

    @refreshed_property
    def scale(self) -> float:
        """The scale of the camera at that point."""
        return self._data.scale

    @scale.setter
    def scale(self, value: float) -> None:
        current_data = george.tv_camera_enum_points(self.id)
        george.tv_camera_set_point(
            self.id,
            x=current_data.x,
            y=current_data.y,
            angle=current_data.angle,
            scale=value,
        )

    @classmethod
    def new(
        cls,
        camera: Camera,
        index: int,
        x: int,
        y: int,
        angle: int,
        scale: float,
    ) -> CameraPoint:
        """Create a new point and add it to the camera path at that index."""
        george.tv_camera_insert_point(index, x, y, angle, scale)
        return cls(index, camera)

    def remove(self) -> None:
        """Remove the camera point.

        Warning:
            the point instance won't be usable after that call
        """
        george.tv_camera_remove_point(self.index)
        self.mark_removed()
