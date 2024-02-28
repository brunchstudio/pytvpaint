from __future__ import annotations

import contextlib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Generator, Iterator

from pytvpaint import george
from pytvpaint.george.exceptions import GeorgeError
from pytvpaint.utils import (
    Refreshable,
    Removable,
    get_unique_name,
    refreshed_property,
    render_context,
    set_as_current,
)

if TYPE_CHECKING:
    from pytvpaint.clip import Clip
    from pytvpaint.project import Project
    from pytvpaint.scene import Scene


@contextlib.contextmanager
def restore_current_frame(
    clip: Clip, frame: int | None = None
) -> Generator[None, None, None]:
    previous_frame = clip.current_frame
    if frame:
        clip.current_frame = frame
    yield
    clip.current_frame = previous_frame


@dataclass
class LayerInstance:
    layer: Layer
    start: int

    def __post_init__(self) -> None:
        # Check if the instance exists
        try:
            project_start_frame = self.layer.project.start_frame
            george.tv_instance_get_name(self.layer.id, self.start - project_start_frame)
        except GeorgeError:
            raise ValueError(f"There's no instance at frame {self.start}")

    @property
    def name(self) -> str:
        self.layer.make_current()
        real_frame = self.start - self.layer.project.start_frame
        return george.tv_instance_get_name(self.layer.id, real_frame)

    @name.setter
    def name(self, value: str) -> None:
        self.layer.make_current()
        real_frame = self.start - self.layer.project.start_frame
        george.tv_instance_set_name(self.layer.id, real_frame, value)

    def duplicate(self) -> None:
        """Duplicate the instance and insert it next to it"""
        self.layer.make_current()
        with restore_current_frame(self.layer.clip, self.start):
            george.tv_layer_insert_image(duplicate=True)

    @property
    def next(self) -> LayerInstance | None:
        """Returns the next instance"""
        with restore_current_frame(self.layer.clip, self.start):
            next_frame = george.tv_exposure_next()

        return self.layer.get_instance(next_frame)

    @property
    def previous(self) -> LayerInstance | None:
        """Get the previous instance

        Returns:
            LayerInstance | None: the previous instance, None if there isn't
        """
        with restore_current_frame(self.layer.clip, self.start):
            prev_frame = george.tv_exposure_prev()

        return self.layer.get_instance(prev_frame)


class LayerColor(Refreshable):
    def __init__(
        self,
        color_index: int,
        clip: Clip | None = None,
    ) -> None:
        from pytvpaint.clip import Clip

        super().__init__()
        self._index = color_index
        self._clip = clip or Clip.current_clip()
        self._data = george.tv_layer_color_get_color(self.clip.id, self._index)

    def refresh(self) -> None:
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_layer_color_get_color(self._clip.id, self._index)

    def __repr__(self) -> str:
        return f"LayerColor({self.name})<index:{self.index}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LayerColor):
            return NotImplemented
        return self.index == other.index

    @property
    def index(self) -> int:
        return self._index

    @property
    def clip(self) -> Clip:
        return self._clip

    @refreshed_property
    def name(self) -> str:
        return self._data.name

    @name.setter
    def name(self, value: str) -> None:
        clip_layer_color_names = (color.name for color in self.clip.layer_colors)
        value = get_unique_name(clip_layer_color_names, value)
        george.tv_layer_color_set_color(self.clip.id, self.index, self.color, value)

    @refreshed_property
    def color(self) -> george.RGBColor:
        return george.RGBColor(
            r=self._data.color_r, g=self._data.color_g, b=self._data.color_b
        )

    @color.setter
    def color(self, value: george.RGBColor) -> None:
        george.tv_layer_color_set_color(self.clip.id, self.index, value)

    @property
    def is_visible(self) -> bool:
        self.clip.make_current()
        return george.tv_layer_color_visible(self.index)

    def lock_layers(self, lock: bool) -> None:
        self.clip.make_current()
        if lock:
            george.tv_layer_color_lock(self.index)
        else:
            george.tv_layer_color_unlock(self.index)

    def show_layers(
        self,
        show: bool,
        mode: george.LayerColorDisplayOpt = george.LayerColorDisplayOpt.DISPLAY,
    ) -> None:
        self.clip.make_current()
        if show:
            george.tv_layer_color_show(mode=mode, color_index=self.index)
        else:
            george.tv_layer_color_unselect(self.index)

    def select_layers(self, select: bool) -> None:
        self.clip.make_current()
        if select:
            george.tv_layer_color_select(self.index)
        else:
            george.tv_layer_color_unselect(self.index)

    @classmethod
    def new(
        cls, clip: Clip, index: int, color: george.RGBColor, name: str = ""
    ) -> LayerColor:
        layer_color = cls(color_index=index, clip=clip)
        layer_color.color = color
        layer_color.name = name
        return layer_color


class Layer(Removable):
    def __init__(self, layer_id: int, clip: Clip | None = None) -> None:
        from pytvpaint.clip import Clip

        super().__init__()
        self._id = layer_id
        self._clip = clip or Clip.current_clip()
        self._data = george.tv_layer_info(self.id)

    def refresh(self) -> None:
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_layer_info(self._id)

    def __repr__(self) -> str:
        return f"Layer({self.name})<id:{self.id}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Layer):
            return NotImplemented
        return self.id == other.id

    @property
    def id(self) -> int:
        return self._id

    @property
    def project(self) -> Project:
        return self._clip.project

    @property
    def scene(self) -> Scene:
        return self._clip.scene

    @property
    def clip(self) -> Clip:
        """The layer's clip"""
        return self._clip

    @property
    def position(self) -> int:
        return george.tv_layer_get_pos(self.id)

    @position.setter
    def position(self, value: int) -> None:
        if self.position == value:
            return
        self.make_current()
        george.tv_layer_move(value + 1)

    @refreshed_property
    def name(self) -> str:
        return self._data.name

    @name.setter
    @set_as_current
    def name(self, value: str) -> None:
        if value == self.name:
            return
        value = get_unique_name(self.clip.layer_names, value)
        george.tv_layer_rename(self.id, value)

    @refreshed_property
    def layer_type(self) -> george.LayerType:
        return self._data.type

    @property
    def opacity(self) -> int:
        return george.tv_layer_density_get()

    @opacity.setter
    @set_as_current
    def opacity(self, value: int) -> None:
        value = max(0, min(value, 100))
        george.tv_layer_density_set(value)

    @refreshed_property
    def start(self) -> int:
        """The layer start frame according to the project's start frame"""
        return self._data.first_frame + self.project.start_frame

    @refreshed_property
    def end(self) -> int:
        return self._data.last_frame + self.project.start_frame

    @property
    def color(self) -> LayerColor:
        color_index = george.tv_layer_color_get(self.id)
        return next(c for i, c in enumerate(self.clip.layer_colors) if i == color_index)

    @color.setter
    def color(self, color: LayerColor) -> None:
        george.tv_layer_color_set(self.id, color.index)

    @property
    def is_current(self) -> bool:
        return self.id == self.current_layer_id()

    def make_current(self) -> None:
        if self.is_current:
            return
        if self.clip:
            self.clip.make_current()
        george.tv_layer_set(self.id)

    @property
    def is_selected(self) -> bool:
        return george.tv_layer_selection_get(self.id)

    @is_selected.setter
    def is_selected(self, value: bool) -> None:
        george.tv_layer_selection_set(self.id, new_state=value)

    @property
    def is_visible(self) -> bool:
        return george.tv_layer_display_get(self.id)

    @is_visible.setter
    def is_visible(self, value: bool) -> None:
        george.tv_layer_display_set(self.id, new_state=value)

    @property
    def is_locked(self) -> bool:
        return george.tv_layer_lock_get(self.id)

    @is_locked.setter
    def is_locked(self, value: bool) -> None:
        george.tv_layer_lock_set(self.id, new_state=value)

    @property
    def is_collapsed(self) -> bool:
        return george.tv_layer_collapse_get(self.id)

    @is_collapsed.setter
    def is_collapsed(self, value: bool) -> None:
        george.tv_layer_collapse_set(self.id, new_state=value)

    @property
    def blending_mode(self) -> george.BlendingMode:
        return george.tv_layer_blending_mode_get(self.id)

    @blending_mode.setter
    def blending_mode(self, value: george.BlendingMode) -> None:
        george.tv_layer_blending_mode_set(self.id, mode=value)

    @property
    def stencil(self) -> george.StencilMode:
        return george.tv_layer_stencil_get(self.id)

    @stencil.setter
    def stencil(self, mode: george.StencilMode) -> None:
        george.tv_layer_stencil_set(self.id, mode=mode)

    @property
    def thumbnails_visible(self) -> bool:
        return george.tv_layer_show_thumbnails_get(self.id)

    @thumbnails_visible.setter
    def thumbnails_visible(self, value: bool) -> None:
        george.tv_layer_show_thumbnails_set(self.id, value)

    @property
    def auto_break_instance(self) -> bool:
        return george.tv_layer_auto_break_instance_get(self.id)

    @auto_break_instance.setter
    def auto_break_instance(self, value: bool) -> None:
        if value and not self.is_anim_layer:
            msg = "Can't set auto break instance because it's not an animation layer"
            raise ValueError(msg)
        george.tv_layer_auto_break_instance_set(self.id, value)

    @property
    def auto_create_instance(self) -> bool:
        return george.tv_layer_auto_create_instance_get(self.id)

    @auto_create_instance.setter
    def auto_create_instance(self, value: bool) -> None:
        george.tv_layer_auto_create_instance_set(self.id, value)

    @property
    def pre_behavior(self) -> george.LayerBehavior:
        return george.tv_layer_pre_behavior_get(self.id)

    @pre_behavior.setter
    def pre_behavior(self, value: george.LayerBehavior) -> None:
        george.tv_layer_pre_behavior_set(self.id, value)

    @property
    def post_behavior(self) -> george.LayerBehavior:
        return george.tv_layer_post_behavior_get(self.id)

    @post_behavior.setter
    def post_behavior(self, value: george.LayerBehavior) -> None:
        george.tv_layer_post_behavior_set(self.id, value)

    @property
    def is_position_locked(self) -> bool:
        return george.tv_layer_lock_position_get(self.id)

    @is_position_locked.setter
    def is_position_locked(self, value: bool) -> None:
        george.tv_layer_lock_position_set(self.id, value)

    @property
    def preserve_transparency(self) -> george.LayerTransparency:
        return george.tv_preserve_get()

    @preserve_transparency.setter
    @set_as_current
    def preserve_transparency(self, value: george.LayerTransparency) -> None:
        george.tv_preserve_set(value)

    @set_as_current
    def convert_to_anim_layer(self) -> None:
        """Converts the layer to an animation layer"""
        george.tv_layer_anim(self.id)

    @property
    def is_anim_layer(self) -> bool:
        return self.layer_type == george.LayerType.SEQUENCE

    def load_dependencies(self) -> None:
        """Load all dependencies of the layer in memory"""
        george.tv_layer_load_dependencies(self.id)

    @staticmethod
    def current_layer_id() -> int:
        return george.tv_layer_current_id()

    @classmethod
    def current_layer(cls) -> Layer:
        from pytvpaint.clip import Clip

        return cls(layer_id=cls.current_layer_id(), clip=Clip.current_clip())

    @set_as_current
    def shift(self, new_start: int) -> None:
        george.tv_layer_shift(self.id, new_start - self.project.start_frame)

    @set_as_current
    def merge(
        self,
        layer: Layer,
        blending_mode: george.BlendingMode,
        stamp: bool = False,
        erase: bool = False,
        keep_color_grp: bool = True,
        keep_img_mark: bool = True,
        keep_instance_name: bool = True,
    ) -> None:
        george.tv_layer_merge(
            layer.id,
            blending_mode,
            stamp,
            erase,
            keep_color_grp,
            keep_img_mark,
            keep_instance_name,
        )

    @staticmethod
    def merge_all(
        keep_color_grp: bool = True,
        keep_img_mark: bool = True,
        keep_instance_name: bool = True,
    ) -> None:
        george.tv_layer_merge_all(keep_color_grp, keep_img_mark, keep_instance_name)

    @staticmethod
    @george.undo
    def new(
        name: str,
        clip: Clip | None = None,
        color_index: int | None = None,
    ) -> Layer:
        from pytvpaint.clip import Clip

        clip = clip or Clip.current_clip()
        clip.make_current()

        name = get_unique_name(clip.layer_names, name)
        layer_id = george.tv_layer_create(name)

        layer = Layer(layer_id=layer_id, clip=clip)

        if color_index:
            layer.color = LayerColor(color_index)

        return layer

    @classmethod
    @george.undo
    def new_anim_layer(
        cls,
        name: str,
        clip: Clip | None = None,
        color_index: int | None = None,
    ) -> Layer:
        layer = cls.new(name, clip, color_index)
        layer.convert_to_anim_layer()
        layer.thumbnails_visible = True
        return layer

    @classmethod
    @george.undo
    def new_background_layer(
        cls,
        name: str,
        clip: Clip | None = None,
        color_index: int | None = None,
    ) -> Layer:
        layer = cls.new(name, clip, color_index)
        layer.thumbnails_visible = True
        layer.pre_behavior = george.LayerBehavior.HOLD
        layer.post_behavior = george.LayerBehavior.HOLD
        return layer

    @set_as_current
    @george.undo
    def duplicate(self, name: str) -> Layer:
        name = get_unique_name(self.clip.layer_names, name)
        layer_id = george.tv_layer_duplicate(name)

        return Layer(layer_id=layer_id, clip=self.clip)

    def remove(self) -> None:
        self.clip.make_current()
        george.tv_layer_kill(self.id)
        self.mark_removed()

    def render_frame(
        self,
        export_path: Path | str,
        frame: int | None = None,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        format_opts: list[str] | None = None,
    ) -> Path:
        export_path = Path(export_path)
        save_format = george.SaveFormat.from_extension(export_path.suffix)
        export_path.parent.mkdir(parents=True, exist_ok=True)

        frame = frame or self.clip.current_frame
        self.clip.current_frame = frame

        with render_context(
            alpha_mode,
            save_format,
            format_opts,
            layers_to_render=[self],
        ):
            george.tv_save_image(export_path)

        if not export_path.exists():
            raise FileNotFoundError(
                f"Could not find rendered image at : {export_path.as_posix()}"
            )

        return export_path

    def get_mark_color(self, frame: int) -> LayerColor | None:
        frame = frame - self.project.start_frame
        color_index = george.tv_layer_mark_get(self.id, frame)
        if not color_index:
            return None
        return self.clip.get_layer_color(by_index=color_index)

    def add_mark(self, frame: int, color_index: int) -> None:
        if not self.is_anim_layer:
            raise Exception("Can't add a mark because it's not an animation layer")
        frame = frame - self.project.start_frame
        george.tv_layer_mark_set(self.id, frame, color_index)

    def remove_mark(self, frame: int) -> None:
        # Setting it at 0 clears the mark
        self.add_mark(frame, 0)

    @property
    def marks(self) -> Iterator[tuple[int, LayerColor]]:
        """Iterator over the layer marks including the frame and the color"""
        for frame in range(self.start, self.end + 1):
            layer_color = self.get_mark_color(frame)
            if not layer_color:
                continue
            yield (frame, layer_color)

    def clear_marks(self) -> None:
        for frame, _ in self.marks:
            self.remove_mark(frame)

    @set_as_current
    def select_frames(self, start: int, frame_count: int) -> None:
        george.tv_layer_select(start - self.clip.start, frame_count)

    @property
    def selected_frames(self) -> list[int]:
        start, count = george.tv_layer_select_info(full=True)
        return [start + self.clip.start + offset for offset in range(count)]

    @set_as_current
    def cut_selection(self) -> None:
        george.tv_layer_cut()

    @set_as_current
    def copy_selection(self) -> None:
        george.tv_layer_copy()

    @set_as_current
    def paste_selection(self) -> None:
        george.tv_layer_paste()

    @refreshed_property
    @set_as_current
    def instances(self) -> Iterator[LayerInstance]:
        project_start_frame = self.project.start_frame

        # Exposure frames starts at 0
        instance_frame = self.start
        self.clip.current_frame = self.start

        while True:
            instance = self.get_instance(instance_frame)
            if instance is None:
                break
            yield instance
            with restore_current_frame(self.clip, instance_frame):
                instance_frame = george.tv_exposure_next() + project_start_frame

    def get_instance(self, frame: int) -> LayerInstance | None:
        try:
            instance_frame = frame - self.project.start_frame
            george.tv_instance_get_name(self.id, instance_frame)
            return LayerInstance(self, frame)
        except GeorgeError:
            return None

    def rename_instances(
        self,
        mode: george.InstanceNamingMode,
        prefix: str | None = None,
        suffix: str | None = None,
        process: george.InstanceNamingProcess | None = None,
    ) -> None:
        george.tv_instance_name(self.id, mode, prefix, suffix, process)
