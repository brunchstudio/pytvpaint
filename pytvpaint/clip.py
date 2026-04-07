"""Clip object class module."""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, cast

from fileseq.filesequence import FileSequence
from fileseq.frameset import FrameSet

from pytvpaint import george, log, utils
from pytvpaint.camera import Camera
from pytvpaint.george.client import parse
from pytvpaint.layer import CameraLayer, CTGLayer, Layer, LayerColor, LayerFolder
from pytvpaint.sound import ClipSound
from pytvpaint.utils import (
    Removable,
    Renderable,
    refreshed_property,
    set_as_current,
)

if TYPE_CHECKING:
    from pytvpaint.project import Project
    from pytvpaint.scene import Scene


class Clip(Removable, Renderable):
    """A Clip is a container for layers and is part of a Scene."""

    def __init__(
        self,
        clip_id: int,
        project: Project | None = None,
    ) -> None:
        """Constructs a Clip from an existing TVPaint clip (giving its id).

        Note:
            You should use `Clip.new` to create a new clip

        Args:
            clip_id: an existing clip id
            project: the project or the current one if None
        """
        from pytvpaint.project import Project

        super().__init__()
        self._id = clip_id
        self._project = project or Project.current_project()
        self._data = george.tv_clip_info(self.id)

    def __repr__(self) -> str:
        """The string representation of the clip."""
        return f"Clip({self.name})<id:{self.id}>"

    def __eq__(self, other: object) -> bool:
        """Two clips are equal if their id is the same."""
        if not isinstance(other, Clip):
            return NotImplemented
        return self.id == other.id

    @classmethod
    def new(
        cls,
        name: str,
        scene: Scene | None = None,
        project: Project | None = None,
    ) -> Clip:
        """Creates a new clip.

        Args:
            name: the new clip name
            scene: the scene or the current one if None. Defaults to None.
            project: the project or the current one if None. Defaults to None.

        Returns:
            Clip: the newly created clip
        """
        from pytvpaint.project import Project

        project = project or Project.current_project()
        project.make_current()

        scene = scene or project.current_scene
        scene.make_current()

        name = utils.get_unique_name(project.clip_names, name)
        george.tv_clip_new(name)

        return Clip.current_clip()

    def refresh(self) -> None:
        """Refreshes the clip data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_clip_info(self._id)

    def make_current(self) -> None:
        """Make the clip the current one."""
        self.project.make_current()
        if george.tv_clip_current_id() == self.id:
            return
        george.tv_clip_select(self.id)

    @property
    def id(self) -> int:
        """The clip id."""
        return self._id

    @property
    def project(self) -> Project:
        """The clip's project."""
        return self._project

    @property
    def scene(self) -> Scene:
        """The clip's scene.

        Raises:
            ValueError: if no current scene in the project
        """
        for scene in self.project.scenes:
            for other_clip in scene.clips:
                if other_clip == self:
                    self.make_current()
                    return scene
        raise Exception("The clip's scene doesn't exist")

    @scene.setter
    def scene(self, value: Scene) -> None:
        """Moves the clip to another scene."""
        george.tv_clip_move(self.id, value.id, self.position)

    @property
    def camera(self) -> Camera:
        """The clip camera."""
        return Camera(clip=self)

    @property
    def position(self) -> int:
        """The position of the clip in the scene.

        Raises:
            ValueError: if clip cannot be found in the project
        """
        for pos, clip_id in enumerate(self.scene.clip_ids):
            if clip_id == self.id:
                return pos
        raise ValueError(f"No clip found open with id : {self.id}")

    @position.setter
    def position(self, value: int) -> None:
        """Set the position of the clip in the scene."""
        value = max(0, value)
        george.tv_clip_move(self.id, self.scene.id, value)

    @property
    @set_as_current
    def name(self) -> str:
        """The clip name."""
        return george.tv_clip_name_get(self.id)

    @name.setter
    def name(self, value: str) -> None:
        """Set the clip name."""
        if self.name == value:
            return

        clip_names = [clip.name for clip in self.project.clips if clip != clip]
        value = utils.get_unique_name(clip_names, value)
        george.tv_clip_name_set(self.id, value)

    @refreshed_property
    def start(self) -> int:
        """The start frame of the clip."""
        return self._data.first_frame + self.project.start_frame

    @refreshed_property
    def end(self) -> int:
        """The end frame of the clip."""
        return self._data.last_frame + self.project.start_frame

    @property
    def duration(self) -> int:
        """The duration of the clip in frames. Takes into account the mark in/out of the clip."""
        return (self.mark_out or self.end) - (self.mark_in or self.start) + 1

    @refreshed_property
    def timeline_start(self) -> int:
        """The start frame of the clip relative to the project's timeline."""
        # get clip real start in project timeline
        clip_real_start = 0
        for clip in self.project.clips:
            if clip == self:
                break
            clip_start = clip.mark_in or clip.start
            clip_end = clip.mark_out or clip.end
            clip_duration = (clip_end - clip_start) + 1
            clip_real_start += clip_duration

        return clip_real_start + self.project.start_frame

    @refreshed_property
    def timeline_end(self) -> int:
        """The end frame of the clip relative to the project's timeline."""
        clip_start = self.mark_in or self.start
        clip_end = self.mark_out or self.end
        clip_duration = clip_end - clip_start
        return self.timeline_start + clip_duration

    @refreshed_property
    def frame_count(self) -> int:
        """The clip's frame count."""
        return self._data.frame_count

    @property
    def is_selected(self) -> bool:
        """Returns True if the clip is selected."""
        return george.tv_clip_selection_get(self.id)

    @is_selected.setter
    def is_selected(self, value: bool) -> None:
        """Select or deselect the clip."""
        george.tv_clip_selection_set(self.id, value)

    @property
    def is_visible(self) -> bool:
        """Returns True if the clip is visible."""
        return not george.tv_clip_hidden_get(self.id)

    @is_visible.setter
    def is_visible(self, value: bool) -> None:
        """Show or hide the clip."""
        george.tv_clip_hidden_set(self.id, not value)

    @property
    def color_index(self) -> int:
        """Get the clip color index."""
        return george.tv_clip_color_get(self.id)

    @color_index.setter
    def color_index(self, value: int) -> None:
        """Set the clip color index."""
        george.tv_clip_color_set(self.id, value)

    @property
    def action_text(self) -> str:
        """Get the action text of the clip."""
        return parse.unescape_everything_safely(george.tv_clip_action_get(self.id))

    @action_text.setter
    def action_text(self, value: str) -> None:
        """Set the action text of the clip."""
        george.tv_clip_action_set(self.id, value)

    @property
    def dialog_text(self) -> str:
        """Get the dialog text of the clip."""
        return parse.unescape_everything_safely(george.tv_clip_dialog_get(self.id))

    @dialog_text.setter
    def dialog_text(self, value: str) -> None:
        """Set the dialog text of the clip."""
        george.tv_clip_dialog_set(self.id, value)

    @property
    def note_text(self) -> str:
        """Get the note text of the clip."""
        return parse.unescape_everything_safely(george.tv_clip_note_get(self.id))

    @note_text.setter
    def note_text(self, value: str) -> None:
        """Set the note text of the clip."""
        george.tv_clip_note_set(self.id, value)

    @refreshed_property
    def is_current(self) -> bool:
        """Returns True if the clip is the current one."""
        return Clip.current_clip_id() == self.id

    @staticmethod
    def current_clip_id() -> int:
        """Returns the id of the current clip."""
        return george.tv_clip_current_id()

    @staticmethod
    def current_clip() -> Clip:
        """Returns the current clip object."""
        from pytvpaint.project import Project

        return Clip(Clip.current_clip_id(), Project.current_project())

    @property
    @set_as_current
    def current_frame(self) -> int:
        """Returns the current frame in the clip (timeline) relative to the project start frame."""
        return george.tv_layer_image_get() + self.project.start_frame

    @current_frame.setter
    @set_as_current
    def current_frame(self, value: int) -> None:
        """Set the current frame of the clip."""
        george.tv_layer_image(value - self.project.start_frame)

    @set_as_current
    def duplicate(self) -> Clip:
        """Duplicates the clip.

        Note:
            a new unique name is choosen for the duplicated clip with `get_unique_name`.
        """
        current_clips = list(self.project.clips)
        george.tv_clip_duplicate(self.id)
        new_clip = [clip for clip in self.project.clips if clip not in current_clips][0]  # noqa: RUF015

        clip_names = [clip.name for clip in current_clips]
        new_name = utils.get_unique_name(clip_names, self.name)
        new_clip.name = new_name

        return new_clip

    def remove(self) -> None:
        """Removes the clip.

        Warning:
            the instance is not usable after that call because it's marked as removed.
        """
        george.tv_clip_close(self.id)
        self.mark_removed()

    @property
    @set_as_current
    def layer_ids(self) -> Iterator[int]:
        """Returns an iterator over the layer ids."""
        return utils.position_generator(lambda pos: george.tv_layer_get_id(pos))

    def get_layers(
        self,
        filter_types: tuple[type, ...] | None = None,
        ignore_types: tuple[type, ...] | None = None,
    ) -> Iterator[Layer]:
        """Returns an iterator over the clip's layers.

        Args:
            filter_types: list of layer types to return, default is None, meaning all.
            ignore_types: list of layer types to ignore, default is None, meaning all.

        Note:
            Since TVP12 have introduced multiple layer types, this function will replace Clip.layers.
        """
        for layer_id in self.layer_ids:
            layer_data = george.tv_layer_info(layer_id)

            layer_class = Layer
            if layer_data.type == george.LayerType.FOLDER:
                layer_class = LayerFolder
            elif layer_data.type == george.LayerType.CAMERA:
                layer_class = CameraLayer
            # handle CTG layers like regular layers in TVP versions < 12
            elif not george.is_tvp_version_below_12() and layer_data.type is george.LayerType.SCRIBBLES:
                layer_class = CTGLayer

            if filter_types and layer_class not in filter_types:
                continue
            if ignore_types and layer_class in ignore_types:
                continue

            yield layer_class(layer_id, clip=self, data=layer_data)

    @property
    @george.deprecated_warning(msg="use `Clip.get_layers()` instead.")
    def layers(self) -> Iterator[Layer]:
        """Returns an iterator over the clip's animation layers, excluding all Folder, Camera and CTG layers.

        Warning:
            DEPRECATED: use `Clip.get_layers()` instead.
        """
        yield from self.get_layers(ignore_types=(LayerFolder, CameraLayer, CTGLayer))

    @property
    def anim_layers(self) -> Iterator[Layer]:
        """Returns an iterator over the clip's animation layers, excluding all Folder, Camera and CTG layers."""
        yield from self.get_layers(ignore_types=(LayerFolder, CameraLayer, CTGLayer))

    @property
    @george.min_version_compatible(min_version="12")
    def ctg_layers(self) -> Iterator[CTGLayer]:
        """Returns an iterator over the clip's CTG layers.

        Note:
            This function is only available in TVPaint version 12 and above.

        Raises:
            NotImplemented: if used in tvpaint version inferior to 12
        """
        for layer in self.get_layers(filter_types=(CTGLayer,)):
            yield cast(CTGLayer, layer)

    @property
    @george.min_version_compatible(min_version="12")
    def folders(self) -> Iterator[LayerFolder]:
        """Returns an iterator over the clip's Folder layers.

        Note:
            This function is only available in TVPaint version 12 and above.

        Raises:
            NotImplemented: if used in tvpaint version inferior to 12
        """
        for layer in self.get_layers(filter_types=(LayerFolder,)):
            yield cast(LayerFolder, layer)

    @property
    @george.min_version_compatible(min_version="12")
    def camera_layer(self) -> CameraLayer | None:
        """Returns the clip's Camera layer.

        Note:
            This function is only available in TVPaint version 12 and above.

        Raises:
            NotImplemented: if used in tvpaint version inferior to 12
        """
        camera_layer = next(self.get_layers(filter_types=(CameraLayer,)), None)
        if camera_layer:
            return cast(CameraLayer, camera_layer)

        # if we're here then the camera layer has probably been deleted, let's recreate it by switching to the camera.
        george.tv_set_active_shape(george.TVPShape.CAMERA)
        return cast(CameraLayer, next(self.get_layers(filter_types=(CameraLayer,)), None))

    @property
    @set_as_current
    def layer_names(self) -> Iterator[str]:
        """Returns an iterator over the clip's layer names."""
        for layer in self.get_layers():
            yield layer.name

    @property
    def current_layer(self) -> Layer:
        """Get the current layer in the clip.

        Raises:
            ValueError: if no current layer in clip
        """
        for layer in self.get_layers():
            if layer.is_current:
                return layer
        raise ValueError("Couldn't find a current layer")

    def get_layer(
        self,
        by_id: int | None = None,
        by_name: str | None = None,
        by_regex: re.Pattern[str] | None = None,
    ) -> Layer | None:
        """Get a specific layer by id or name.

        Args:
            by_id: search by id. Defaults to None.
            by_name: search by name, search is case-insensitive. Defaults to None.
            by_regex: search by name using a compiled regex, case-sensitivity is left to the regex. Defaults to None.

        Raises:
            ValueError: if none of the search arguments where provided

        Returns:
            Layer | None: the searched element or None if search was unsuccessful
        """
        return utils.get_tvp_element(self.get_layers(), by_id=by_id, by_name=by_name, by_regex=by_regex)

    @set_as_current
    def add_layer(self, layer_name: str) -> Layer:
        """Add a new layer in the layer stack."""
        return Layer.new(name=layer_name, clip=self)

    @george.min_version_compatible(min_version="12")
    @set_as_current
    def add_layer_folder(self, folder_name: str) -> LayerFolder:
        """Add a new layer in the layer stack.

        Note:
            This function is only available in TVPaint version 12 and above.

        Raises:
            NotImplemented: if used in tvpaint version inferior to 12
        """
        return cast(LayerFolder, LayerFolder.new(name=folder_name, clip=self))

    @property
    def selected_layers(self) -> Iterator[Layer]:
        """Returns an iterator over the selected layers."""
        yield from (layer for layer in self.get_layers() if layer.is_selected)

    @property
    def visible_layers(self) -> Iterator[Layer]:
        """Returns an iterator over the visible layers."""
        yield from (layer for layer in self.get_layers() if layer.is_visible)

    @set_as_current
    @george.undoable
    def load_media(
        self,
        media_path: Path,
        start_count: tuple[int, int] | None = None,
        stretch: bool = False,
        time_stretch: bool = False,
        preload: bool = False,
        with_name: str = "",
        field_order: george.FieldOrder = george.FieldOrder.LOWER,
    ) -> Layer:
        """Loads a media (single frame, video, ...) into a new Layer in the clip.

        Args:
            media_path: the path of the media. If it's a file sequence, give the path of the first image.
            start_count: the start and number of image of sequence to load. Defaults to None.
            stretch: Stretch each image to the size of the layer. Defaults to None.
            time_stretch: Once loaded, the layer will have a new number of image corresponding to the project framerate. Defaults to None.
            preload: Load all the images in memory, no more reference on the files. Defaults to None.
            with_name: the name of the new layer
            field_order: the field order. Defaults to None.

        Returns:
            Layer: the new layer created
        """
        media_path = Path(media_path)

        george.tv_load_sequence(
            media_path,
            start_count,
            field_order,
            stretch,
            time_stretch,
            preload,
        )

        new_layer = Layer.current_layer()
        new_layer.name = with_name or media_path.stem

        return new_layer

    def _validate_range(self, start: int, end: int) -> None:
        clip_start = self.start
        clip_end = self.end
        clip_mark_in = self.mark_in
        clip_mark_out = self.mark_out

        clip_full_range = (
            (clip_mark_in if clip_mark_in else clip_start),
            (clip_mark_out if clip_mark_out else clip_end),
        )
        if start < clip_full_range[0] or end > clip_full_range[1]:
            raise ValueError(f"Render ({start}-{end}) not in clip range ({clip_full_range})")

    def _get_real_range(self, start: int, end: int, frame_set: FrameSet | None = None) -> tuple[int, int, FrameSet]:
        # get project start to get real values
        project_start_frame = self.project.start_frame
        # get clip real start in project timeline
        clip_real_start = self.timeline_start - project_start_frame
        # get real mark_in since we'll also need to subtract it from the range
        real_mark_in = (self.mark_in - project_start_frame) if self.mark_in else 0

        def convert_range(x: int) -> int:
            return (x - project_start_frame - real_mark_in) + clip_real_start

        start = convert_range(start)
        end = convert_range(end)

        # clamp values to clip start
        start = max(clip_real_start, start)
        end = max(clip_real_start, end)

        if frame_set is not None:
            start = max(start, convert_range(int(frame_set.start())))
            end = min(end, convert_range(int(frame_set.end())))
            if frame_set.isConsecutive():
                frame_set = FrameSet(f"{start}-{end}")
            else:
                frames = [convert_range(int(f)) for f in frame_set.items if start <= convert_range(int(f)) <= end]
                frame_set = FrameSet(frames)
        else:
            frame_set = FrameSet(f"{start}-{end}")

        return start, end, frame_set

    @set_as_current
    def render(
        self,
        output_path: Path | str | FileSequence,
        start: int | None = None,
        end: int | None = None,
        frame_set: FrameSet | None = None,
        use_camera: bool = False,
        layer_selection: list[Layer] | None = None,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        background_mode: george.BackgroundMode | None = None,
        format_opts: list[str] | None = None,
    ) -> Path | FileSequence:
        """Render the clip to a single frame or frame sequence or movie.

        Args:
            output_path: a single file or file sequence pattern
            start: the start frame to render or the mark in or the clip's start if None. Defaults to None.
            end: the end frame to render or the mark out or the clip's end if None. Defaults to None.
            frame_set: a FrameSet with the frames/range to render. Defaults to None.
            use_camera: use the camera for rendering, otherwise render the whole canvas. Defaults to False.
            layer_selection: list of layers to render, if None render all of them. Defaults to None.
            alpha_mode: the alpha mode for rendering. Defaults to george.AlphaSaveMode.PREMULTIPLY.
            background_mode: the background mode for rendering. Defaults to None.
            format_opts: custom format options. Defaults to None.

        Raises:
            ValueError: if requested range (start-end) not in clip range/bounds
            ValueError: if output is a movie, and it's duration is equal to 1 frame
            FileNotFoundError: if the render failed and no files were found on disk or missing frames

        Note:
            This function uses the clip's range as a basis (start-end). This  is different from the project range, which
            uses the project timeline. For more details on the differences in frame ranges and the timeline in TVPaint,
            please check the `Usage/Rendering` section of the documentation.

        Warning:
            Even though pytvpaint does a pretty good job of correcting the frame ranges for rendering, we're still
            encountering some weird edge cases where TVPaint will consider the range invalid for seemingly no reason.

        Returns:
            the output file path or sequence
        """
        default_start = self.mark_in or self.start
        default_end = self.mark_out or self.end

        return self._render(
            output_path=output_path,
            default_start=default_start,
            default_end=default_end,
            start=start,
            end=end,
            frame_set=frame_set,
            use_camera=use_camera,
            layer_selection=layer_selection,
            alpha_mode=alpha_mode,
            background_mode=background_mode,
            format_opts=format_opts,
        )

    @set_as_current
    def export_tvp(self, export_path: Path | str) -> None:
        """Exports the clip in .tvp format which can be imported as a project in TVPaint.

        Raises:
            ValueError: if output extension is not (.tvp)
            FileNotFoundError: if the render failed and no files were found on disk
        """
        export_path = Path(export_path)

        if export_path.suffix != ".tvp":
            raise ValueError("The file extension must be .tvp")

        export_path.parent.mkdir(exist_ok=True, parents=True)
        george.tv_save_clip(export_path)

        if not export_path.exists():
            raise FileNotFoundError(f"Could not find output at : {export_path.as_posix()}")

    @set_as_current
    def export_json(
        self,
        export_path: Path | str,
        save_format: george.SaveFormat,
        folder_pattern: str = r"[%3li] %ln",
        file_pattern: str = r"[%3ii] %ln",
        layer_selection: list[Layer] | None = None,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        background_mode: george.BackgroundMode | None = None,
        format_opts: list[str] | None = None,
        all_images: bool = False,
        ignore_duplicates: bool = False,
    ) -> None:
        """Exports the instances (or all the images) of layers in the clip and a JSON file describing the structure of that clip.

        Args:
            export_path: the JSON export path
            save_format: file format to use for rendering
            folder_pattern: the folder name pattern (%li: layer index, %ln: layer name, %fi: file index (added in 11.0.8)). Defaults to None.
            file_pattern: the file name pattern (%li: layer index, %ln: layer name, %ii: image index, %in: image name, %fi: file index (added in 11.0.8)). Defaults to None.
            layer_selection: list of layers to render or all if None. Defaults to None.
            alpha_mode: the export alpha mode. Defaults to george.AlphaSaveMode.PREMULTIPLY.
            background_mode: the export background mode. Defaults to None.
            format_opts: custom format options. Defaults to None.
            all_images: export all images (not only the instances). Defaults to False.
            ignore_duplicates: Ignore duplicates images. Defaults to None.

        Raises:
            FileNotFoundError: if the export failed and no files were found on disk
        """
        export_path = Path(export_path)
        export_path.parent.mkdir(exist_ok=True, parents=True)

        fill_background = bool(background_mode not in [None, george.BackgroundMode.NONE])

        with utils.render_context(alpha_mode, background_mode, save_format, format_opts, layer_selection):
            george.tv_clip_save_structure_json(
                export_path,
                save_format,
                fill_background=fill_background,
                folder_pattern=folder_pattern,
                file_pattern=file_pattern,
                visible_layers_only=True,
                all_images=all_images,
                ignore_duplicates=ignore_duplicates,
            )

        if not export_path.exists():
            raise FileNotFoundError(f"Could not find output at : {export_path.as_posix()}")

    @set_as_current
    def export_psd(
        self,
        export_path: Path | str,
        mode: george.PSDSaveMode,
        start: int | None = None,
        end: int | None = None,
        layer_selection: list[Layer] | None = None,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        background_mode: george.BackgroundMode | None = None,
        format_opts: list[str] | None = None,
    ) -> None:
        """Save the current clip as a PSD.

        Args:
            export_path: the PSD save path
            mode: whether to save all the images, only the instances or inside the markin
            start: the start frame. Defaults to None.
            end: the end frame. Defaults to None.
            layer_selection: layers to render. Defaults to None (render all the layers).
            alpha_mode: the alpha save mode. Defaults to george.AlphaSaveMode.PREMULTIPLY.
            background_mode: the export background mode. Defaults to None.
            format_opts: custom format options. Defaults to None.

        Raises:
            FileNotFoundError: if the export failed and no files were found on disk
        """
        start = start or self.mark_in or self.start
        end = end or self.mark_out or self.end

        export_path = Path(export_path)
        image = start if mode == george.PSDSaveMode.IMAGE else None

        with utils.render_context(
            alpha_mode,
            background_mode,
            george.SaveFormat.PSD,
            format_opts,
            layer_selection,
        ):
            george.tv_clip_save_structure_psd(
                export_path,
                mode,
                image=image,
                mark_in=start,
                mark_out=end,
            )

        if mode == george.PSDSaveMode.MARKIN:
            # raises error if sequence not found
            check_path = export_path.with_suffix(f".#{export_path.suffix}").as_posix()
            assert FileSequence.findSequenceOnDisk(check_path)
        else:
            if not export_path.exists():
                raise FileNotFoundError(f"Could not find output at : {export_path.as_posix()}")

    @set_as_current
    def export_csv(
        self,
        export_path: Path | str,
        save_format: george.SaveFormat,
        all_images: bool = False,
        exposure_label: str = "",
        layer_selection: list[Layer] | None = None,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        background_mode: george.BackgroundMode | None = None,
        format_opts: list[str] | None = None,
    ) -> None:
        """Save the current clip as a CSV.

        Args:
            export_path: the .csv export path
            save_format: file format to use for rendering
            all_images: export all images or only instances. Defaults to None.
            exposure_label: give a label when the image is an exposure. Defaults to None.
            layer_selection: layers to render. Defaults to None (render all the layers).
            alpha_mode: the alpha save mode. Defaults to george.AlphaSaveMode.PREMULTIPLY.
            background_mode: the export background mode. Defaults to None.
            format_opts: custom format options. Defaults to None.

        Raises:
            ValueError: if the extension is not .csv
            FileNotFoundError: if the render failed and no files were found on disk
        """
        export_path = Path(export_path)

        if export_path.suffix != ".csv":
            raise ValueError("Export path must have .csv extension")

        with utils.render_context(alpha_mode, background_mode, save_format, format_opts, layer_selection):
            george.tv_clip_save_structure_csv(export_path, all_images, exposure_label)

        if not export_path.exists():
            raise FileNotFoundError(f"Could not find output at : {export_path.as_posix()}")

    @set_as_current
    def export_sprites(
        self,
        export_path: Path | str,
        layout: george.SpriteLayout | None = None,
        space: int = 0,
        layer_selection: list[Layer] | None = None,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        background_mode: george.BackgroundMode | None = None,
        format_opts: list[str] | None = None,
    ) -> None:
        """Save the current clip as sprites in one image.

        Args:
            export_path (Path | str): _description_
            layout: the sprite layout. Defaults to None.
            space: the space between each sprite in the image. Defaults to None.
            layer_selection: layers to render. Defaults to None (render all the layers).
            alpha_mode: the alpha save mode. Defaults to george.AlphaSaveMode.PREMULTIPLY.
            background_mode: the export background mode. Defaults to None.
            format_opts: custom format options. Defaults to None.

        Raises:
            FileNotFoundError: if the export failed and no files were found on disk
        """
        export_path = Path(export_path)
        save_format = george.SaveFormat.from_extension(export_path.suffix)

        with utils.render_context(alpha_mode, background_mode, save_format, format_opts, layer_selection):
            george.tv_clip_save_structure_sprite(export_path, layout, space)

        if not export_path.exists():
            raise FileNotFoundError(f"Could not find output at : {export_path.as_posix()}")

    @set_as_current
    def export_flix(
        self,
        export_path: Path | str,
        start: int | None = None,
        end: int | None = None,
        import_parameters: str = "",
        file_parameters: str = "",
        send: bool = False,
        layer_selection: list[Layer] | None = None,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        background_mode: george.BackgroundMode | None = None,
        format_opts: list[str] | None = None,
    ) -> None:
        """Save the current clip for Flix.

        Args:
            export_path: the .xml export path
            start: the start frame. Defaults to None.
            end: the end frame. Defaults to None.
            import_parameters: the attribute(s) of the global <flixImport> tag (waitForSource/...). Defaults to None.
            file_parameters: the attribute(s) of each <image> (file) tag (dialogue/...). Defaults to None.
            send: open a browser with the prefilled url. Defaults to None.
            layer_selection: layers to render. Defaults to None (render all the layers).
            alpha_mode: the alpha save mode. Defaults to george.AlphaSaveMode.PREMULTIPLY.
            background_mode: the export background mode. Defaults to None.
            format_opts: custom format options. Defaults to None.

        Raises:
            ValueError: if the extension is not .xml
            FileNotFoundError: if the export failed and no files were found on disk
        """
        export_path = Path(export_path)

        if export_path.suffix != ".xml":
            raise ValueError("Export path must have .xml extension")

        original_file = self.project.path
        import_parameters = import_parameters or 'waitForSource="1" multipleSetups="1" replaceSelection="0"'

        # The project needs to be saved
        self.project.save()

        # save alpha mode and save format values
        with utils.render_context(alpha_mode, background_mode, None, format_opts, layer_selection):
            george.tv_clip_save_structure_flix(
                export_path,
                start,
                end,
                import_parameters,
                file_parameters,
                send,
                original_file,
            )

        if not export_path.exists():
            raise FileNotFoundError(f"Could not find output at : {export_path.as_posix()}")

    @property
    @set_as_current
    def mark_in(self) -> int | None:
        """Get the mark in of the clip."""
        frame, mark_action = george.tv_mark_in_get(reference=george.MarkReference.CLIP)
        if mark_action == george.MarkAction.CLEAR:
            return None
        return frame + self.project.start_frame

    @mark_in.setter
    @set_as_current
    def mark_in(self, value: int | None) -> None:
        """Set the mark int value of the clip or None to clear it."""
        if value is None:
            action = george.MarkAction.CLEAR
            value = self.mark_in or 0
        else:
            action = george.MarkAction.SET
            value = value

        frame = value - self.project.start_frame
        george.tv_mark_in_set(reference=george.MarkReference.CLIP, frame=frame, action=action)

    @property
    @set_as_current
    def mark_out(self) -> int | None:
        """Get the mark out of the clip."""
        frame, mark_action = george.tv_mark_out_get(reference=george.MarkReference.CLIP)
        if mark_action == george.MarkAction.CLEAR:
            return None
        return frame + self.project.start_frame

    @mark_out.setter
    @set_as_current
    def mark_out(self, value: int | None) -> None:
        """Set the mark in of the clip or None to clear it."""
        if value is None:
            action = george.MarkAction.CLEAR
            value = self.mark_out or 0
        else:
            action = george.MarkAction.SET
            value = value

        frame = value - self.project.start_frame
        george.tv_mark_out_set(
            reference=george.MarkReference.CLIP,
            frame=frame,
            action=action,
        )

    @property
    def layer_colors(self) -> Iterator[LayerColor]:
        """Returns an iterator over the layer colors."""
        for color_index in range(26):
            yield LayerColor(color_index=color_index, clip=self)

    def set_layer_color(self, layer_color: LayerColor) -> None:
        """Set the layer color at the provided index.

        Args:
            layer_color: the layer color instance.
        """
        if not george.is_tvp_version_below_12():
            log.warning("this function currently does not work properly in tvpaint 12")
        george.tv_layer_color_set_color(self.id, layer_color.index, layer_color.color, layer_color.name)

    def get_layer_color(
        self,
        by_index: int | None = None,
        by_name: str | None = None,
        by_regex: re.Pattern[str] | None = None,
    ) -> LayerColor | None:
        """Get a layer color by index or name.

        Args:
            by_index: search by color index. Defaults to None.
            by_name: search by name, search is case-insensitive. Defaults to None.
            by_regex: search by name using a compiled regex, case-sensitivity is left to the regex. Defaults to None.

        Raises:
            ValueError: if none of the search arguments where provided
        """
        values = (by_index, by_name, by_regex)
        if not any(v is not None for v in values):
            raise ValueError(f"At least one value ({' or '.join(str(v) for v in values)} must be provided")

        if by_index is not None:
            return next(c for i, c in enumerate(self.layer_colors) if i == by_index)

        if by_name is not None:
            try:
                return next(c for c in self.layer_colors if c.name.lower() == by_name.lower())
            except StopIteration:
                return None

        if by_regex is not None:
            try:
                return next(c for c in self.layer_colors if by_regex.search(c.name))
            except StopIteration:
                return None

        return None

    @property
    def bookmarks(self) -> Iterator[int]:
        """Returns an iterator over the clip bookmarks."""
        bookmarks_iter = utils.position_generator(lambda pos: george.tv_bookmarks_enum(pos))
        project_start_frame = self.project.start_frame
        return (frame + project_start_frame for frame in bookmarks_iter)

    def add_bookmark(self, frame: int) -> None:
        """Add a bookmark at that frame."""
        george.tv_bookmark_set(frame - self.project.start_frame)

    def remove_bookmark(self, frame: int) -> None:
        """Remove a bookmark at that frame."""
        george.tv_bookmark_clear(frame - self.project.start_frame)

    def clear_bookmarks(self) -> None:
        """Remove all the bookmarks."""
        bookmarks = list(self.bookmarks)
        for frame in bookmarks:
            self.remove_bookmark(frame)

    @set_as_current
    def go_to_previous_bookmark(self) -> None:
        """Go to the previous bookmarks frame."""
        george.tv_bookmark_prev()

    @set_as_current
    def go_to_next_bookmark(self) -> None:
        """Go to the next bookmarks frame."""
        george.tv_bookmark_next()

    @property
    def sounds(self) -> Iterator[ClipSound]:
        """Iterates through the clip's soundtracks."""
        sounds_data = utils.position_generator(lambda pos: george.tv_sound_clip_info(self.id, pos))

        for track_index, _ in enumerate(sounds_data):
            yield ClipSound(track_index, clip=self)

    def get_sound(
        self,
        by_track_index: int | None = None,
        by_path: Path | str | None = None,
    ) -> ClipSound | None:
        """Get a clip sound by track index or path.

        Args:
            by_track_index: search by track index. Defaults to None.
            by_path: search by path. Defaults to None.

        Raises:
            ValueError: if none of the search arguments where provided

        Returns:
            ClipSound | None: the searched element or None if search was unsuccessful
        """
        values = (by_track_index, by_path)
        if not any(v is not None for v in values):
            raise ValueError(f"At least one value ({' or '.join(str(v) for v in values)} must be provided")

        for sound in self.sounds:
            if by_track_index is not None and sound.by_track_index != by_track_index:
                continue
            if by_path is not None and sound.path != Path(by_path):
                continue
            return sound

        return None

    def add_sound(self, sound_path: Path | str) -> ClipSound:
        """Adds a new clip soundtrack."""
        return ClipSound.new(sound_path, parent=self)
