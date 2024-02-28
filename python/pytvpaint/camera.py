from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

from pytvpaint import george
from pytvpaint.george.camera import TVPCameraPoint
from pytvpaint.utils import (
    Refreshable,
    Removable,
    position_generator,
    refreshed_property,
)

if TYPE_CHECKING:
    from pytvpaint.clip import Clip


class Camera(Refreshable):
    def __init__(self, clip: Clip, data: george.TVPCamera | None = None) -> None:
        super().__init__()
        self._clip = clip
        self._data: george.TVPCamera = data or george.tv_camera_info_get()
        self._points: list[CameraPoint] = []

    def refresh(self) -> None:
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_camera_info_get()

    def __repr__(self) -> str:
        return f"Camera()[{self.clip}]"

    @property
    def clip(self) -> Clip:
        return self._clip

    @refreshed_property
    def width(self) -> int:
        return self._data.width

    @width.setter
    def width(self, value: int) -> None:
        george.tv_camera_info_set(width=value, height=self.height)

    @refreshed_property
    def height(self) -> int:
        return self._data.height

    @height.setter
    def height(self, value: int) -> None:
        george.tv_camera_info_set(height=value, width=self.width)

    @refreshed_property
    def fps(self) -> float:
        return self._data.frame_rate

    @fps.setter
    def fps(self, value: float) -> None:
        george.tv_camera_info_set(
            self.width,
            self.height,
            self.field_order,
            frame_rate=value,
        )

    @refreshed_property
    def pixel_aspect_ratio(self) -> float:
        return self._data.pixel_aspect_ratio

    @pixel_aspect_ratio.setter
    def pixel_aspect_ratio(self, value: float) -> None:
        george.tv_camera_info_set(
            self.width,
            self.height,
            self.field_order,
            self.fps,
            pixel_aspect_ratio=value,
        )

    @refreshed_property
    def anti_aliasing(self) -> int:
        return self._data.anti_aliasing

    @refreshed_property
    def field_order(self) -> george.FieldOrder:
        return self._data.field_order

    @field_order.setter
    def field_order(self, value: george.FieldOrder) -> None:
        george.tv_camera_info_set(self.width, self.height, field_order=value)

    def insert_point(
        self,
        index: int,
        x: int,
        y: int,
        angle: int,
        scale: float,
    ) -> CameraPoint:
        return CameraPoint.new(self, index, x, y, angle, scale)

    @staticmethod
    def current_points_data() -> Iterator[TVPCameraPoint]:
        return position_generator(lambda pos: george.tv_camera_enum_points(pos))

    @property
    def points(self) -> Iterator[CameraPoint]:
        for index, point_data in enumerate(self.current_points_data()):
            yield CameraPoint(index, camera=self, data=point_data)

    def get_point_data_at(self, position: float) -> george.TVPCameraPoint:
        position = max(0.0, min(position, 1.0))
        return george.tv_camera_interpolation(position)

    def remove_point(self, index: int) -> None:
        try:
            point = next(p for i, p in enumerate(self.points) if i == index)
            point.remove()
        except StopIteration:
            pass


class CameraPoint(Removable):
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
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_camera_enum_points(self._index)

    def __repr__(self) -> str:
        return f"CameraPoint({self.camera.clip.name})<index:{self._index}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CameraPoint):
            return NotImplemented
        self.refresh()
        other.refresh()
        return self._data == other._data

    @property
    def data(self) -> george.TVPCameraPoint:
        return self._data

    @property
    def index(self) -> int:
        return self._index

    @property
    def camera(self) -> Camera:
        return self._camera

    @refreshed_property
    def x(self) -> float:
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
        george.tv_camera_insert_point(index, x, y, angle, scale)
        return cls(index, camera)

    def remove(self) -> None:
        george.tv_camera_remove_point(self.index)
        self.mark_removed()
