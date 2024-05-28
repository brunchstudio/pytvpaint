"""Layer related classes."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from fileseq.filesequence import FileSequence
from fileseq.frameset import FrameSet

from pytvpaint import george, log, utils
from pytvpaint.george.exceptions import GeorgeError
from pytvpaint.utils import (
    Refreshable,
    Removable,
    refreshed_property,
    set_as_current,
)

if TYPE_CHECKING:
    from pytvpaint.clip import Clip
    from pytvpaint.project import Project
    from pytvpaint.scene import Scene


@dataclass
class LayerInstance:
    """A layer instance is a frame where there is a drawing. It only has a start frame.

    Note:
        `LayerInstance` is special because we can't track their position, meaning that if the user move an instance the Python object values won't match.
    """

    layer: Layer
    start: int

    def __post_init__(self) -> None:
        """Checks if the instance exists after init.

        Raises:
            ValueError: if no layer instance found at provided start frame
        """
        try:
            project_start_frame = self.layer.project.start_frame
            george.tv_instance_get_name(self.layer.id, self.start - project_start_frame)
        except GeorgeError:
            raise ValueError(f"There's no instance at frame {self.start}")

    def __eq__(self, other: object) -> bool:
        """Checks if two instances are the same, meaning their start frames are equal."""
        if not isinstance(other, LayerInstance):
            return NotImplemented
        return self.start == other.start

    @property
    def name(self) -> str:
        """Get or set the instance name."""
        self.layer.make_current()
        real_frame = self.start - self.layer.project.start_frame
        return george.tv_instance_get_name(self.layer.id, real_frame)

    @name.setter
    def name(self, value: str) -> None:
        self.layer.make_current()
        real_frame = self.start - self.layer.project.start_frame
        george.tv_instance_set_name(self.layer.id, real_frame, value)

    @property
    def length(self) -> int:
        """Get or set the instance's number of frames or length.

        Raises:
            ValueError: If the length provided is inferior to 1
        """
        self.layer.make_current()
        next_instance = self.next
        end = (next_instance.start - 1) if next_instance else self.layer.end
        return (end - self.start) + 1

    @length.setter
    def length(self, value: int) -> None:
        if value < 1:
            raise ValueError("Instance Length must be at least equal to 1")
        self.layer.make_current()
        real_start = self.start - self.layer.project.start_frame
        george.tv_exposure_set(real_start, value)

    @property
    def end(self) -> int:
        """Get or set the instance's end frame.

        Raises:
            ValueError: If the end frame provided is inferior to the instance's start frame
        """
        return self.start + (self.length - 1)

    @end.setter
    def end(self, value: int) -> None:
        if value < self.start:
            raise ValueError(
                f"End must be equal to or superior to instance start ({self.start})"
            )

        new_length = (value - self.start) + 1
        self.length = new_length

    def split(self, at_frame: int) -> LayerInstance:
        """Split the instance into two instances at the given frame.

        Args:
            at_frame: the frame where the split will occur

        Raises:
            ValueError: If `at_frame` is superior to the instance's end frame

        Returns:
            LayerInstance: the new layer instance
        """
        if at_frame > self.end:
            raise ValueError(
                f"`at_frame` must be in range of the instance's start-end ({self.start}-{self.end})"
            )

        self.layer.make_current()
        real_frame = at_frame - self.layer.project.start_frame
        george.tv_exposure_break(real_frame)

        return LayerInstance(self.layer, at_frame)

    def duplicate(
        self, direction: george.InsertDirection = george.InsertDirection.AFTER
    ) -> None:
        """Duplicate the instance and insert it in the given direction."""
        self.layer.make_current()

        # tvp won't insert images if the insert frame is the same as the instance start, let's move it
        move_frame = self.layer.clip.current_frame
        if move_frame == self.start and self.layer.start != self.start:
            move_frame = self.layer.start
        else:
            move_frame = self.layer.end + 1

        with utils.restore_current_frame(self.layer.clip, move_frame):
            self.copy()
            at_frame = (
                self.end if direction == george.InsertDirection.AFTER else self.start
            )
            self.paste(at_frame=at_frame)

    def cut(self) -> None:
        """Cut all the frames/images/exposures of the instance and store them in the image buffer."""
        self.layer.make_current()
        self.select()
        self.layer.cut_selection()

    def copy(self) -> None:
        """Copy all the frames/images/exposures of the instance and store them in the image buffer."""
        self.layer.make_current()
        self.select()
        self.layer.copy_selection()

    def paste(self, at_frame: int | None) -> None:
        """Paste all the frames/images/exposures stored in the image buffer to the current instance at the given frame.

        Args:
            at_frame: the frame where the stored frames will be pasted. Default is the current frame
        """
        at_frame = at_frame if at_frame is not None else self.layer.clip.current_frame

        self.layer.make_current()
        with utils.restore_current_frame(self.layer.clip, at_frame):
            self.layer.paste_selection()

    def select(self) -> None:
        """Select all frames in this instance."""
        self.layer.select_frames(self.start, (self.length - 1))

    @property
    def next(self) -> LayerInstance | None:
        """Returns the next instance.

        Returns:
            the next instance or None if at the end of the layer
        """
        self.layer.make_current()
        with utils.restore_current_frame(self.layer.clip, self.start):
            next_frame = george.tv_exposure_next()

        next_frame += self.layer.project.start_frame
        if next_frame > self.layer.end:
            return None

        next_instance = LayerInstance(self.layer, next_frame)

        if next_instance == self:
            return None
        return next_instance

    @property
    def previous(self) -> LayerInstance | None:
        """Get the previous instance.

        Returns:
            the previous instance, None if there isn't
        """
        self.layer.make_current()
        with utils.restore_current_frame(self.layer.clip, self.start):
            prev_frame = george.tv_exposure_prev()

        prev_frame += self.layer.project.start_frame
        prev_frame = max(self.layer.start, prev_frame)

        prev_instance = LayerInstance(self.layer, prev_frame)

        if prev_instance == self:
            return None
        return prev_instance


class LayerColor(Refreshable):
    """The color of a layer identified by an index. Layer colors are specific to a clip."""

    def __init__(
        self,
        color_index: int,
        clip: Clip | None = None,
    ) -> None:
        """Construct a LayerColor from an index and a clip (if None it gets the current clip)."""
        from pytvpaint.clip import Clip

        super().__init__()
        self._index = color_index
        self._clip = clip or Clip.current_clip()
        self._data = george.tv_layer_color_get_color(self.clip.id, self._index)

    def refresh(self) -> None:
        """Refreshes the layer color data."""
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_layer_color_get_color(self._clip.id, self._index)

    def __repr__(self) -> str:
        """Returns the string representation of LayerColor."""
        return f"LayerColor({self.name})<index:{self.index}>"

    def __eq__(self, other: object) -> bool:
        """Two LayerColor objects are equal if their index are the same."""
        if not isinstance(other, LayerColor):
            return NotImplemented
        return self.index == other.index

    @property
    def index(self) -> int:
        """The layer color index."""
        return self._index

    @property
    def clip(self) -> Clip:
        """The layer color clip."""
        return self._clip

    @refreshed_property
    def name(self) -> str:
        """The name of the color."""
        return self._data.name

    @name.setter
    def name(self, value: str) -> None:
        """Set the name of the color."""
        clip_layer_color_names = (color.name for color in self.clip.layer_colors)
        value = utils.get_unique_name(clip_layer_color_names, value)
        george.tv_layer_color_set_color(self.clip.id, self.index, self.color, value)

    @refreshed_property
    def color(self) -> george.RGBColor:
        """Get the color value."""
        return george.RGBColor(
            r=self._data.color_r,
            g=self._data.color_g,
            b=self._data.color_b,
        )

    @color.setter
    def color(self, value: george.RGBColor) -> None:
        """Set the color value."""
        george.tv_layer_color_set_color(self.clip.id, self.index, value)

    @property
    def is_visible(self) -> bool:
        """Get the visibility of the color index."""
        self.clip.make_current()
        return george.tv_layer_color_visible(self.index)

    def lock_layers(self, lock: bool) -> None:
        """Lock or unlock all layers with this color."""
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
        """Show or hide layers with this color.

        Args:
            show: whether to show the layers using this color or not
            mode: the display mode. Defaults to george.LayerColorDisplayOpt.DISPLAY.
        """
        self.clip.make_current()
        if show:
            george.tv_layer_color_show(mode, self.index)
        else:
            george.tv_layer_color_hide(mode, self.index)

    def select_layers(self, select: bool) -> None:
        """Select or unselect layers with this color."""
        self.clip.make_current()
        if select:
            george.tv_layer_color_select(self.index)
        else:
            george.tv_layer_color_unselect(self.index)


class Layer(Removable):
    """A Layer is inside a clip and contains drawings."""

    def __init__(self, layer_id: int, clip: Clip | None = None) -> None:
        from pytvpaint.clip import Clip

        super().__init__()
        self._id = layer_id
        self._clip = clip or Clip.current_clip()
        self._data = george.tv_layer_info(self.id)

    def refresh(self) -> None:
        """Refreshes the layer data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        try:
            self._data = george.tv_layer_info(self._id)
        except GeorgeError:
            self.mark_removed()
            self.refresh()

    def __repr__(self) -> str:
        """The string representation of the layer."""
        return f"Layer({self.name})<id:{self.id}>"

    def __eq__(self, other: object) -> bool:
        """Two layers are equal if their id is the same."""
        if not isinstance(other, Layer):
            return NotImplemented
        return self.id == other.id

    @property
    def id(self) -> int:
        """The layers unique identifier.

        Warning:
            layer ids are not persistent across project load/close
        """
        return self._id

    @property
    def project(self) -> Project:
        """The project containing this layer."""
        return self._clip.project

    @property
    def scene(self) -> Scene:
        """The scene containing this layer."""
        return self._clip.scene

    @property
    def clip(self) -> Clip:
        """The clip containing this layer."""
        return self._clip

    @property
    def position(self) -> int:
        """The position in the layer stack.

        Note:
            layer positions start at 0
        """
        return george.tv_layer_get_pos(self.id)

    @position.setter
    def position(self, value: int) -> None:
        """Moves the layer to the provided position.

        Note:
            This function fixes the issues with positions not been set correctly by TVPaint when value is superior to 0
        """
        if self.position == value:
            return

        value = max(0, value)
        # TVPaint will always set the position at (value - 1) if value is superior to 0, so we need to add +1 in
        #  that case to set the position correctly, I don't know why it works this way, but it honestly makes no sense
        if value != 0:
            value += 1

        self.make_current()
        george.tv_layer_move(value)

    @refreshed_property
    def name(self) -> str:
        """The layer name."""
        return self._data.name

    @name.setter
    @set_as_current
    def name(self, value: str) -> None:
        """Set the layer name.

        Note:
            it uses `get_unique_name` to find a unique layer name across all the layers in the clip
        """
        if value == self.name:
            return
        value = utils.get_unique_name(self.clip.layer_names, value)
        george.tv_layer_rename(self.id, value)

    @refreshed_property
    def layer_type(self) -> george.LayerType:
        """The layer type."""
        return self._data.type

    @property
    def opacity(self) -> int:
        """Get the layer opacity value.

        Note:
            In George, this is called density, we renamed it to `opacity` as it seems more appropriate
        """
        return george.tv_layer_density_get()

    @opacity.setter
    @set_as_current
    def opacity(self, value: int) -> None:
        """Set the layers opacity value (between 0 and 100)."""
        value = max(0, min(value, 100))
        george.tv_layer_density_set(value)

    @refreshed_property
    def start(self) -> int:
        """The layer start frame according to the project's start frame."""
        return self._data.first_frame + self.project.start_frame

    @refreshed_property
    def end(self) -> int:
        """The layer end frame according to the project's start frame."""
        return self._data.last_frame + self.project.start_frame

    @property
    def color(self) -> LayerColor:
        """Get the layer color."""
        color_index = george.tv_layer_color_get(self.id)
        return next(c for i, c in enumerate(self.clip.layer_colors) if i == color_index)

    @color.setter
    def color(self, color: LayerColor) -> None:
        """Set the layer color."""
        george.tv_layer_color_set(self.id, color.index)

    @property
    def is_current(self) -> bool:
        """Returns True if the layer is the current one in the clip."""
        return self.id == self.current_layer_id()

    def make_current(self) -> None:
        """Make the layer current, it also makes the clip current."""
        if self.is_current:
            return
        if self.clip:
            self.clip.make_current()
        george.tv_layer_set(self.id)

    @property
    def is_selected(self) -> bool:
        """Returns True if the layer is selected."""
        return george.tv_layer_selection_get(self.id)

    @is_selected.setter
    def is_selected(self, value: bool) -> None:
        """Select or deselect the layer."""
        george.tv_layer_selection_set(self.id, new_state=value)

    @property
    def is_visible(self) -> bool:
        """Returns True if the layer is visible."""
        return george.tv_layer_display_get(self.id)

    @is_visible.setter
    def is_visible(self, value: bool) -> None:
        """Set the visibility state of the layer."""
        george.tv_layer_display_set(self.id, new_state=value)

    @property
    def is_locked(self) -> bool:
        """Returns True if the layer is locked."""
        return george.tv_layer_lock_get(self.id)

    @is_locked.setter
    def is_locked(self, value: bool) -> None:
        """Lock or unlock the layer."""
        george.tv_layer_lock_set(self.id, new_state=value)

    @property
    def is_collapsed(self) -> bool:
        """Returns True if the layer is collapsed."""
        return george.tv_layer_collapse_get(self.id)

    @is_collapsed.setter
    def is_collapsed(self, value: bool) -> None:
        """Collapse or uncollapse the layer."""
        george.tv_layer_collapse_set(self.id, new_state=value)

    @property
    def blending_mode(self) -> george.BlendingMode:
        """Get the layer blending mode value."""
        return george.tv_layer_blending_mode_get(self.id)

    @blending_mode.setter
    def blending_mode(self, value: george.BlendingMode) -> None:
        """Set the layer blending mode value."""
        george.tv_layer_blending_mode_set(self.id, mode=value)

    @property
    def stencil(self) -> george.StencilMode:
        """Get the layer stencil mode value."""
        return george.tv_layer_stencil_get(self.id)

    @stencil.setter
    def stencil(self, mode: george.StencilMode) -> None:
        """Set the layer stencil mode value."""
        george.tv_layer_stencil_set(self.id, mode=mode)

    @property
    def thumbnails_visible(self) -> bool:
        """Returns True if thumbnails are shown on that layer."""
        return george.tv_layer_show_thumbnails_get(self.id)

    @thumbnails_visible.setter
    def thumbnails_visible(self, value: bool) -> None:
        """Show or hide the thumbnails for that layer."""
        george.tv_layer_show_thumbnails_set(self.id, value)

    @property
    def auto_break_instance(self) -> bool:
        """Get the auto break instance value."""
        return george.tv_layer_auto_break_instance_get(self.id)

    @auto_break_instance.setter
    def auto_break_instance(self, value: bool) -> None:
        """Set the auto break instance value.

        Raises:
            ValueError: the layer is not an animation layer
        """
        if value and not self.is_anim_layer:
            msg = "Can't set auto break instance because it's not an animation layer"
            raise ValueError(msg)
        george.tv_layer_auto_break_instance_set(self.id, value)

    @property
    def auto_create_instance(self) -> bool:
        """Get the auto create instance value."""
        return george.tv_layer_auto_create_instance_get(self.id)

    @auto_create_instance.setter
    def auto_create_instance(self, value: bool) -> None:
        """Set the auto create instance value."""
        george.tv_layer_auto_create_instance_set(self.id, value)

    @property
    def pre_behavior(self) -> george.LayerBehavior:
        """Get the pre-behavior value."""
        return george.tv_layer_pre_behavior_get(self.id)

    @pre_behavior.setter
    def pre_behavior(self, value: george.LayerBehavior) -> None:
        """Set the pre-behavior value."""
        george.tv_layer_pre_behavior_set(self.id, value)

    @property
    def post_behavior(self) -> george.LayerBehavior:
        """Get the post-behavior value."""
        return george.tv_layer_post_behavior_get(self.id)

    @post_behavior.setter
    def post_behavior(self, value: george.LayerBehavior) -> None:
        """Set the post-behavior value."""
        george.tv_layer_post_behavior_set(self.id, value)

    @property
    def is_position_locked(self) -> bool:
        """Returns True if the layer position is locked."""
        return george.tv_layer_lock_position_get(self.id)

    @is_position_locked.setter
    def is_position_locked(self, value: bool) -> None:
        """Lock or unlock the layer position."""
        george.tv_layer_lock_position_set(self.id, value)

    @property
    def preserve_transparency(self) -> george.LayerTransparency:
        """Get the preserve transparency value."""
        return george.tv_preserve_get()

    @preserve_transparency.setter
    @set_as_current
    def preserve_transparency(self, value: george.LayerTransparency) -> None:
        """Set the preserve transparency value."""
        george.tv_preserve_set(value)

    @set_as_current
    def convert_to_anim_layer(self) -> None:
        """Converts the layer to an animation layer."""
        george.tv_layer_anim(self.id)

    @property
    def is_anim_layer(self) -> bool:
        """Returns True if the layer is an animation layer."""
        return self.layer_type == george.LayerType.SEQUENCE

    def load_dependencies(self) -> None:
        """Load all dependencies of the layer in memory."""
        george.tv_layer_load_dependencies(self.id)

    @staticmethod
    def current_layer_id() -> int:
        """Returns the current layer id."""
        return george.tv_layer_current_id()

    @classmethod
    def current_layer(cls) -> Layer:
        """Returns the current layer object."""
        from pytvpaint.clip import Clip

        return cls(layer_id=cls.current_layer_id(), clip=Clip.current_clip())

    @set_as_current
    def shift(self, new_start: int) -> None:
        """Move the layer to a new frame."""
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
        """Merge this layer with the given one.

        Args:
            layer: the layer to merge with
            blending_mode: the blending mode to use
            stamp: Use stamp mode
            erase: Remove the source layer
            keep_color_grp: Keep the color group
            keep_img_mark: Keep the image mark
            keep_instance_name: Keep the instance name
        """
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
        """Merge all the layers in the stack.

        Args:
            keep_color_grp: Keep the color group
            keep_img_mark: Keep the image mark
            keep_instance_name: Keep the instance name
        """
        george.tv_layer_merge_all(keep_color_grp, keep_img_mark, keep_instance_name)

    @staticmethod
    @george.undoable
    def new(
        name: str,
        clip: Clip | None = None,
        color: LayerColor | None = None,
    ) -> Layer:
        """Create a new layer.

        Args:
            name: the name of the new layer
            clip: the parent clip
            color: the layer color

        Returns:
            Layer: the new layer

        Note:
            The layer name is checked against all other layers to have a unique name using `get_unique_name`.
            This can take a while if you have a lot of layers.
        """
        from pytvpaint.clip import Clip

        clip = clip or Clip.current_clip()
        clip.make_current()

        name = utils.get_unique_name(clip.layer_names, name)
        layer_id = george.tv_layer_create(name)

        layer = Layer(layer_id=layer_id, clip=clip)

        if color:
            layer.color = color

        return layer

    @classmethod
    @george.undoable
    def new_anim_layer(
        cls,
        name: str,
        clip: Clip | None = None,
        color: LayerColor | None = None,
    ) -> Layer:
        """Create a new animation layer.

        Args:
            name: the name of the new layer
            clip: the parent clip
            color: the layer color

        Returns:
            Layer: the new animation layer

        Note:
            It activates the thumbnail visibility
        """
        layer = cls.new(name, clip, color)
        layer.convert_to_anim_layer()
        layer.thumbnails_visible = True
        return layer

    @classmethod
    @george.undoable
    def new_background_layer(
        cls,
        name: str,
        clip: Clip | None = None,
        color: LayerColor | None = None,
        image: Path | str | None = None,
        stretch: bool = False,
    ) -> Layer:
        """Create a new background layer with hold as pre- and post-behavior.

        Args:
            name: the name of the new layer
            clip: the parent clip
            color: the layer color
            image: the background image to load
            stretch: whether to stretch the image to fit the view

        Returns:
            Layer: the new animation layer
        """
        from pytvpaint.clip import Clip

        clip = clip or Clip.current_clip()
        layer = cls.new(name, clip, color)
        layer.pre_behavior = george.LayerBehavior.HOLD
        layer.post_behavior = george.LayerBehavior.HOLD
        layer.thumbnails_visible = True

        image = Path(image or "")
        if image.is_file():
            layer.convert_to_anim_layer()
            layer.load_image(image, frame=clip.start, stretch=stretch)

        return layer

    @set_as_current
    @george.undoable
    def duplicate(self, name: str) -> Layer:
        """Duplicate this layer.

        Args:
            name: the duplicated layer name

        Returns:
            Layer: the duplicated layer
        """
        name = utils.get_unique_name(self.clip.layer_names, name)
        layer_id = george.tv_layer_duplicate(name)

        return Layer(layer_id=layer_id, clip=self.clip)

    def remove(self) -> None:
        """Remove the layer from the clip.

        Warning:
            The current instance won't be usable after this call since it will be mark removed.
        """
        self.clip.make_current()
        self.is_locked = False
        george.tv_layer_kill(self.id)
        self.mark_removed()

    @set_as_current
    def render(
        self,
        output_path: Path | str | FileSequence,
        start: int | None = None,
        end: int | None = None,
        use_camera: bool = False,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        background_mode: george.BackgroundMode | None = None,
        format_opts: list[str] | None = None,
    ) -> None:
        """Render the layer to a single frame or frame sequence or movie.

        Args:
            output_path: a single file or file sequence pattern
            start: the start frame to render the layer's start if None. Defaults to None.
            end: the end frame to render or the layer's end if None. Defaults to None.
            use_camera: use the camera for rendering, otherwise render the whole canvas. Defaults to False.
            alpha_mode: the alpha mode for rendering. Defaults to george.AlphaSaveMode.PREMULTIPLY.
            background_mode: the background mode for rendering. Defaults to None.
            format_opts: custom format options. Defaults to None.

        Raises:
            ValueError: if requested range (start-end) not in clip range/bounds
            ValueError: if output is a movie
            FileNotFoundError: if the render failed and no files were found on disk or missing frames

        Note:
            This functions uses the layer's range as a basis (start-end). This  is different from a project range, which
            uses the project timeline. For more details on the differences in frame ranges and the timeline in TVPaint,
            please check the `Usage/Rendering` section of the documentation.

        Warning:
            Even tough pytvpaint does a pretty good job of correcting the frame ranges for rendering, we're still
            encountering some weird edge cases where TVPaint will consider the range invalid for seemingly no reason.
        """
        start = self.start if start is None else start
        end = self.end if end is None else end
        self.clip.render(
            output_path=output_path,
            start=start,
            end=end,
            use_camera=use_camera,
            layer_selection=[self],
            alpha_mode=alpha_mode,
            background_mode=background_mode,
            format_opts=format_opts,
        )

    @set_as_current
    def render_frame(
        self,
        export_path: Path | str,
        frame: int | None = None,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        background_mode: george.BackgroundMode | None = george.BackgroundMode.NONE,
        format_opts: list[str] | None = None,
    ) -> Path:
        """Render a frame from the layer.

        Args:
            export_path: the frame export path (the extension determines the output format)
            frame: the frame to render or the current frame if None. Defaults to None.
            alpha_mode: the render alpha mode
            background_mode: the render background mode
            format_opts: custom output format options to pass when rendering

        Raises:
            FileNotFoundError: if the render failed or output not found on disk

        Returns:
            Path: render output path
        """
        export_path = Path(export_path)
        save_format = george.SaveFormat.from_extension(export_path.suffix)
        export_path.parent.mkdir(parents=True, exist_ok=True)

        frame = frame or self.clip.current_frame
        self.clip.current_frame = frame

        with utils.render_context(
            alpha_mode,
            background_mode,
            save_format,
            format_opts,
            layer_selection=[self],
        ):
            george.tv_save_image(export_path)

        if not export_path.exists():
            raise FileNotFoundError(
                f"Could not find rendered image ({frame}) at : {export_path.as_posix()}"
            )

        return export_path

    @set_as_current
    def render_instances(
        self,
        export_path: Path | str | FileSequence,
        start: int | None = None,
        end: int | None = None,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        background_mode: george.BackgroundMode | None = None,
        format_opts: list[str] | None = None,
    ) -> FileSequence:
        """Render all layer instances in the provided range for the current layer.

        Args:
            export_path: the export path (the extension determines the output format)
            start: the start frame to render the layer's start if None. Defaults to None.
            end: the end frame to render or the layer's end if None. Defaults to None.
            alpha_mode: the render alpha mode
            background_mode: the render background mode
            format_opts: custom output format options to pass when rendering

        Raises:
            ValueError: if requested range (start-end) not in layer range/bounds
            ValueError: if output is a movie
            FileNotFoundError: if the render failed or output not found on disk

        Returns:
            FileSequence: instances output sequence
        """
        file_sequence, start, end, is_sequence, is_image = utils.handle_output_range(
            export_path, self.start, self.end, start, end
        )

        if start < self.start or end > self.end:
            raise ValueError(
                f"Render ({start}-{end}) not in clip range ({(self.start, self.end)})"
            )
        if not is_image:
            raise ValueError(
                f"Video formats ({file_sequence.extension()}) are not supported for instance rendering !"
            )

        # render to output
        frames = []
        for layer_instance in self.instances:
            cur_frame = layer_instance.start
            instance_output = Path(file_sequence.frame(cur_frame))
            self.render_frame(
                instance_output, cur_frame, alpha_mode, background_mode, format_opts
            )
            frames.append(str(cur_frame))

        file_sequence.setFrameSet(FrameSet(",".join(frames)))
        return file_sequence

    @set_as_current
    def load_image(
        self, image_path: str | Path, frame: int | None = None, stretch: bool = False
    ) -> None:
        """Load an image in the current layer at a given frame.

        Args:
            image_path: path to the image to load
            frame: the frame where the image will be loaded, if none provided, image will be loaded at current frame
            stretch: whether to stretch the image to fit the view

        Raises:
            FileNotFoundError: if the file doesn't exist at provided path
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found at : {image_path}")

        frame = frame or self.clip.current_frame
        with utils.restore_current_frame(self.clip, frame):
            # if no instance at the specified frame, then create a new one
            if not self.get_instance(frame):
                self.add_instance(frame)

            george.tv_load_image(image_path.as_posix(), stretch)

    def get_mark_color(self, frame: int) -> LayerColor | None:
        """Get the mark color at a specific frame.

        Args:
            frame: frame with a mark

        Returns:
            LayerColor | None: the layer color if there was a mark
        """
        frame = frame - self.project.start_frame
        color_index = george.tv_layer_mark_get(self.id, frame)
        if not color_index:
            return None

        return self.clip.get_layer_color(by_index=color_index)

    def add_mark(self, frame: int, color: LayerColor) -> None:
        """Add a mark to a frame.

        Args:
            frame: frame to put a mark on
            color: the color index

        Raises:
            TypeError: if the layer is not an animation layer
        """
        if not self.is_anim_layer:
            raise TypeError(
                f"Can't add a mark because this is not an animation layer ({self})"
            )
        frame = frame - self.project.start_frame
        george.tv_layer_mark_set(self.id, frame, color.index)

    def remove_mark(self, frame: int) -> None:
        """Remove a mark.

        Args:
            frame: a frame number with a mark
        """
        # Setting it at 0 clears the mark
        self.add_mark(frame, LayerColor(0, self.clip))

    @property
    def marks(self) -> Iterator[tuple[int, LayerColor]]:
        """Iterator over the layer marks including the frame and the color.

        Yields:
            frame (int): the mark frame
            color (LayerColor): the mark color
        """
        for frame in range(self.start, self.end + 1):
            layer_color = self.get_mark_color(frame)
            if not layer_color:
                continue
            yield (frame, layer_color)

    def clear_marks(self) -> None:
        """Clear all the marks in the layer."""
        for frame, _ in self.marks:
            self.remove_mark(frame)

    @set_as_current
    def select_frames(self, start: int, end: int) -> None:
        """Select the frames from a start and count.

        Args:
            start: the selection start frame
            end: the selected end frame
        """
        if not self.is_anim_layer:
            log.warning(
                "Selection may display weird behaviour when applied to a non animation layer"
            )
        frame_count = (end - start) + 1
        george.tv_layer_select(start - self.clip.start, frame_count)

    @set_as_current
    def select_all_frames(self) -> None:
        """Select all frames in the layer."""
        frame, frame_count = george.tv_layer_select_info(full=True)
        george.tv_layer_select(frame, frame_count)

    @set_as_current
    def clear_selection(self) -> None:
        """Clear frame selection in the layer."""
        # selecting frames after the layer's end frame will result in a empty selection, thereby clearing the selection
        george.tv_layer_select(self.end + 1, 0)

    @property
    def selected_frames(self) -> list[int]:
        """Get the list of selected frames.

        Returns:
            Array of selected frame numbers
        """
        start, count = george.tv_layer_select_info(full=False)
        return [(start + self.clip.start + offset) for offset in range(count)]

    @set_as_current
    def cut_selection(self) -> None:
        """Cut the selected instances."""
        george.tv_layer_cut()

    @set_as_current
    def copy_selection(self) -> None:
        """Copy the selected instances."""
        george.tv_layer_copy()

    @set_as_current
    def paste_selection(self) -> None:
        """Paste the previously copied instances."""
        george.tv_layer_paste()

    @refreshed_property
    @set_as_current
    def instances(self) -> Iterator[LayerInstance]:
        """Iterates over the layer instances.

        Yields:
            each LayerInstance present in the layer
        """
        # instances start at layer start
        current_instance = LayerInstance(self, self.start)

        while True:
            yield current_instance

            nex_instance = current_instance.next
            if nex_instance is None:
                break

            current_instance = nex_instance

    def get_instance(self, frame: int, strict: bool = False) -> LayerInstance | None:
        """Get the instance at that frame.

        Args:
            frame: the instance frame
            strict: True will only return Instance if the given frame is the start of the instance. Default is False

        Returns:
            the instance if found else None
        """
        for layer_instance in self.instances:
            if strict:
                if layer_instance.start != frame:
                    continue
                return layer_instance

            if not (layer_instance.start <= frame <= layer_instance.end):
                continue
            return layer_instance

        return None

    def get_instances(self, from_frame: int, to_frame: int) -> Iterator[LayerInstance]:
        """Iterates over the layer instances and returns the one in the range (from_frame-to_frame).

        Yields:
            each LayerInstance in the range (from_frame-to_frame)
        """
        for layer_instance in self.instances:
            if layer_instance.end < from_frame:
                continue
            if from_frame <= layer_instance.start <= to_frame:
                yield layer_instance
            if layer_instance.start > to_frame:
                break

    def add_instance(
        self,
        start: int | None = None,
        nb_frames: int = 1,
        direction: george.InsertDirection | None = None,
        split: bool = False,
    ) -> LayerInstance:
        """Crates a new instance.

        Args:
            start: start frame. Defaults to clip current frame if none provided
            nb_frames: number of frames in the new instance. Default is 1, this is the total number of frames created.
            direction: direction where new frames will be added/inserted
            split: True to make each added frame a new image

        Raises:
            TypeError: if the layer is not an animation layer
            ValueError: if the number of frames `nb_frames` is inferior or equal to 0
            ValueError: if an instance already exists at the given range (start + nb_frames)

        Returns:
            LayerInstance: new layer instance
        """
        if not self.is_anim_layer:
            raise TypeError("The layer needs to be an animation layer")

        if nb_frames <= 0:
            raise ValueError("Instance number of frames must be at least 1")

        if start and self.get_instance(start):
            raise ValueError(
                "An instance already exists at the designated frame range. "
                "Edit or delete it before adding a new one."
            )

        start = start if start is not None else self.clip.current_frame
        self.clip.make_current()

        temp_layer = Layer.new_anim_layer(str(uuid4()))
        temp_layer.make_current()

        with utils.restore_current_frame(self.clip, 1):
            if nb_frames > 1:
                if split:
                    george.tv_layer_insert_image(count=nb_frames, direction=direction)
                else:
                    layer_instance = next(temp_layer.instances)
                    layer_instance.length = nb_frames

            temp_layer.select_all_frames()
            temp_layer.copy_selection()
            self.clip.current_frame = start
            self.make_current()
            self.paste_selection()
            temp_layer.remove()

        return LayerInstance(self, start)

    def rename_instances(
        self,
        mode: george.InstanceNamingMode,
        prefix: str | None = None,
        suffix: str | None = None,
        process: george.InstanceNamingProcess | None = None,
    ) -> None:
        """Rename all the instances.

        Args:
            mode: the instance renaming mode
            prefix: the prefix to add to each name
            suffix: the suffix to add to each name
            process: the instance naming process
        """
        george.tv_instance_name(self.id, mode, prefix, suffix, process)
