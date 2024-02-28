from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Iterator

from fileseq.filesequence import FileSequence
from fileseq.frameset import FrameSet

from pytvpaint import george
from pytvpaint.camera import Camera
from pytvpaint.george import RGBColor
from pytvpaint.layer import Layer, LayerColor
from pytvpaint.sound import ClipSound
from pytvpaint.utils import (
    Removable,
    get_tvp_element,
    get_unique_name,
    position_generator,
    refreshed_property,
    render_context,
    set_as_current,
)

if TYPE_CHECKING:
    from pytvpaint.project import Project
    from pytvpaint.scene import Scene


class Clip(Removable):
    def __init__(
        self,
        clip_id: int,
        project: Project,
    ) -> None:
        super().__init__()
        self._id = clip_id
        self._project = project
        self._data = george.tv_clip_info(self.id)

    def __repr__(self) -> str:
        return f"Clip({self.name})<id:{self.id}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Clip):
            return NotImplemented
        return self.id == other.id

    @classmethod
    def new(
        cls,
        name: str,
        project: Project | None = None,
        scene: Scene | None = None,
    ) -> Clip:
        from pytvpaint.project import Project

        project = project or Project.current_project()
        scene = scene or project.current_scene

        scene.make_current()

        name = get_unique_name(project.clip_names, name)
        george.tv_clip_new(name)

        return Clip.current_clip()

    def refresh(self) -> None:
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = george.tv_clip_info(self._id)

    def make_current(self) -> None:
        if george.tv_clip_current_id() == self.id:
            return
        george.tv_clip_select(self.id)

    @property
    def id(self) -> int:
        return self._id

    @property
    def project(self) -> Project:
        return self._project

    @property
    def scene(self) -> Scene:
        for scene in self.project.scenes:
            for other_clip in scene.clips:
                if other_clip == self:
                    self.make_current()
                    return scene
        raise Exception("The clip's scene doesn't exist")

    @scene.setter
    def scene(self, value: Scene) -> None:
        george.tv_clip_move(self.id, value.id, self.position)

    @property
    def camera(self) -> Camera:
        return Camera(clip=self)

    @property
    def position(self) -> int:
        """The position of the clip in the scene"""
        for pos, clip_id in enumerate(self.scene.clip_ids):
            if clip_id == self.id:
                return pos
        raise ValueError(f"No clip found open with id : {self.id}")

    @position.setter
    def position(self, value: int) -> None:
        """Set the position of the clip in the scene"""
        george.tv_clip_move(self.id, self.scene.id, value)

    @property
    @set_as_current
    def name(self) -> str:
        return george.tv_clip_name_get(self.id)

    @name.setter
    def name(self, value: str) -> None:
        if self.name == value:
            return
        value = get_unique_name(self.project.clip_names, value)
        george.tv_clip_name_set(self.id, value)

    @refreshed_property
    def start(self) -> int:
        return self._data.first_frame + self.project.start_frame

    @refreshed_property
    def end(self) -> int:
        return self._data.last_frame + self.project.start_frame

    @refreshed_property
    def frame_count(self) -> int:
        return self._data.frame_count

    @property
    def is_selected(self) -> bool:
        return george.tv_clip_selection_get(self.id)

    @is_selected.setter
    def is_selected(self, value: bool) -> None:
        george.tv_clip_selection_set(self.id, value)

    @property
    def is_visible(self) -> bool:
        return not george.tv_clip_hidden_get(self.id)

    @is_visible.setter
    def is_visible(self, value: bool) -> None:
        george.tv_clip_hidden_set(self.id, not value)

    @property
    @set_as_current
    def background(
        self,
    ) -> tuple[RGBColor, RGBColor] | RGBColor | None:
        return george.tv_background_get()

    @set_as_current
    def clear_background(self) -> None:
        george.tv_background_set(george.BackgroundMode.NONE)

    @set_as_current
    def set_background_solid_color(self, color: RGBColor) -> None:
        george.tv_background_set(george.BackgroundMode.COLOR, color)

    @set_as_current
    def set_background_checker_colors(self, c1: RGBColor, c2: RGBColor) -> None:
        george.tv_background_set(george.BackgroundMode.CHECK, c1, c2)

    @property
    def color_index(self) -> int:
        return george.tv_clip_color_get(self.id)

    @color_index.setter
    def color_index(self, value: int) -> None:
        george.tv_clip_color_set(self.id, value)

    @property
    def action_text(self) -> str:
        return george.tv_clip_action_get(self.id)

    @action_text.setter
    def action_text(self, value: str) -> None:
        george.tv_clip_action_set(self.id, value)

    @property
    def dialog_text(self) -> str:
        return george.tv_clip_dialog_get(self.id)

    @dialog_text.setter
    def dialog_text(self, value: str) -> None:
        george.tv_clip_dialog_set(self.id, value)

    @property
    def note_text(self) -> str:
        return george.tv_clip_note_get(self.id)

    @note_text.setter
    def note_text(self, value: str) -> None:
        george.tv_clip_note_set(self.id, value)

    @refreshed_property
    def is_current(self) -> bool:
        return self._data.is_current

    @staticmethod
    def current_clip_id() -> int:
        """Returns the id of the current clip"""
        return george.tv_clip_current_id()

    @staticmethod
    def current_clip() -> Clip:
        from pytvpaint.project import Project

        return Clip(Clip.current_clip_id(), Project.current_project())

    @property
    @set_as_current
    def current_frame(self) -> int:
        return george.tv_layer_image_get() + self.project.start_frame

    @current_frame.setter
    @set_as_current
    def current_frame(self, value: int) -> None:
        george.tv_layer_image(value - self.project.start_frame)

    @set_as_current
    def duplicate(self) -> Clip:
        """Duplicate the clip and rename it"""
        george.tv_clip_duplicate(self.id)
        new_clip = self.project.current_clip
        new_clip.name = get_unique_name(self.project.clip_names, new_clip.name)
        return new_clip

    def remove(self) -> None:
        george.tv_clip_close(self.id)
        self.mark_removed()

    @property
    @set_as_current
    def layer_ids(self) -> Iterator[int]:
        return position_generator(lambda pos: george.tv_layer_get_id(pos))

    @property
    def layers(self) -> Iterator[Layer]:
        from pytvpaint.layer import Layer

        for layer_id in self.layer_ids:
            yield Layer(layer_id, clip=self)

    @property
    def layer_names(self) -> Iterator[str]:
        """Iterator over the clip's layer names"""
        for layer in self.layers:
            yield layer.name

    @property
    def current_layer(self) -> Layer:
        for layer in self.layers:
            if layer.is_current:
                return layer
        raise Exception("Couldn't find a current layer")

    def get_layer(
        self,
        by_id: int | None = None,
        by_name: str | None = None,
    ) -> Layer | None:
        return get_tvp_element(self.layers, by_id, by_name)

    @set_as_current
    def add_layer(self, layer_name: str) -> Layer:
        """Add a new layer in the layer stack"""
        return Layer.new(name=layer_name, clip=self)

    @property
    def selected_layers(self) -> Iterator[Layer]:
        yield from (layer for layer in self.layers if layer.is_selected)

    @property
    def visible_layers(self) -> Iterator[Layer]:
        yield from (layer for layer in self.layers if layer.is_visible)

    @set_as_current
    @george.undo
    def load_media(
        self,
        media_path: Path,
        start_count: tuple[int, int] | None = None,
        stretch: bool = False,
        time_stretch: bool = False,
        pre_load: bool = False,
        with_name: str = "",
        field_order: george.FieldOrder = george.FieldOrder.LOWER,
    ) -> Layer:
        media_path = Path(media_path)

        george.tv_load_sequence(
            media_path,
            start_count,
            field_order,
            stretch,
            time_stretch,
            pre_load,
        )

        new_layer = Layer.current_layer()
        new_layer.name = with_name or media_path.stem

        return new_layer

    @set_as_current
    def render(
        self,
        output_path: Path | str | FileSequence,
        start: int | None = None,
        end: int | None = None,
        use_camera: bool = False,
        layer_selection: list[Layer] | None = None,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        format_opts: list[str] | None = None,
    ) -> None:
        start = start or self.mark_in or self.start
        end = end or self.mark_out or self.end

        file_sequence = (
            output_path
            if isinstance(output_path, FileSequence)
            else FileSequence(Path(output_path).as_posix())
        )

        frame_set = file_sequence.frameSet()
        is_sequence = (frame_set and len(frame_set) > 1) or (
            not frame_set and file_sequence.padding()
        )

        frame_set = FrameSet(f"{start}-{end}")
        file_sequence.setFrameRange(frame_set)

        # get real frame numbers and clamp them with clip start frame
        project_start_frame = self.project.start_frame
        real_start = self.start - project_start_frame

        start = max(real_start, (start - project_start_frame))
        end = max(real_start, (end - project_start_frame))

        save_format = george.SaveFormat.from_extension(file_sequence.extension().lower())
        # render to output
        first_frame = Path(file_sequence.frame(file_sequence.start()))
        first_frame.parent.mkdir(exist_ok=True, parents=True)

        with render_context(alpha_mode, save_format, format_opts, layer_selection):
            if use_camera:
                george.tv_project_save_sequence(
                    first_frame,
                    start_end_frame=(start, end),
                    use_camera=True,
                )
            else:
                if start == end:
                    george.tv_save_display(first_frame)
                else:
                    george.tv_save_sequence(first_frame, mark_in_out=(start, end))

        # make sure the output exists otherwise raise an error
        if is_sequence:
            found_sequence = FileSequence.findSequenceOnDisk(str(file_sequence))
            frame_set = found_sequence.frameSet()

            if not frame_set:
                raise ValueError()

            # raises error if sequence not found
            if not frame_set.issuperset(file_sequence.frameSet()):
                # not all frames found
                missing_frames = frame_set.difference(found_sequence.frameSet())
                raise FileNotFoundError(
                    f"Not all frames found, missing frames ({missing_frames}) "
                    f"in sequence : {output_path}"
                )
        else:
            if not first_frame.exists():
                raise FileNotFoundError(
                    f"Could not find output at : {first_frame.as_posix()}"
                )

    @set_as_current
    def export_tvp(self, export_path: Path | str) -> None:
        """Exports the clip in .tvp format which can be imported again in TVPaint"""
        export_path = Path(export_path)

        if export_path.suffix != ".tvp":
            raise ValueError("The file extension must be .tvp")

        export_path.parent.mkdir(exist_ok=True, parents=True)
        george.tv_save_clip(export_path)

    @set_as_current
    def export_json(
        self,
        export_path: Path | str,
        save_format: george.SaveFormat,
        folder_pattern: str = r"[%3li] %ln",
        file_pattern: str = r"[%3ii] %ln",
        layers: list[Layer] | None = None,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        format_opts: list[str] | None = None,
        all_images: bool = False,
        ignore_duplicates: bool = False,
    ) -> None:
        """
        Exports the instances of layers in the clips
        and a JSON file describing the structure of the clip
        """
        export_path = Path(export_path)
        export_path.parent.mkdir(exist_ok=True, parents=True)

        with render_context(alpha_mode, save_format, format_opts, layers):
            george.tv_clip_save_structure_json(
                export_path,
                save_format,
                None,
                folder_pattern,
                file_pattern,
                all_images=all_images,
                ignore_duplicates=ignore_duplicates,
            )

    @set_as_current
    def export_psd(
        self,
        export_path: Path | str,
        mode: george.PSDSaveMode,
        start: int | None = None,
        end: int | None = None,
        layers: list[Layer] | None = None,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        format_opts: list[str] | None = None,
    ) -> None:
        start = start or self.mark_in or self.start
        end = end or self.mark_out or self.end

        export_path = Path(export_path)
        image = start if mode == george.PSDSaveMode.IMAGE else None

        with render_context(alpha_mode, george.SaveFormat.PSD, format_opts, layers):
            george.tv_clip_save_structure_psd(
                export_path,
                mode,
                image=image,
                mark_in=start,
                mark_out=end,
            )

    @set_as_current
    def export_csv(
        self,
        export_path: Path | str,
        save_format: george.SaveFormat,
        all_images: bool = False,
        exposure_label: str = "",
        layers: list[Layer] | None = None,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        format_opts: list[str] | None = None,
    ) -> None:
        export_path = Path(export_path)

        if export_path.suffix != ".csv":
            raise ValueError("Export path must have .csv extension")

        with render_context(alpha_mode, save_format, format_opts, layers):
            george.tv_clip_save_structure_csv(export_path, all_images, exposure_label)

    @set_as_current
    def export_sprites(
        self,
        export_path: Path | str,
        layout: george.SpriteLayout | None = None,
        space: int = 0,
        layers: list[Layer] | None = None,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        format_opts: list[str] | None = None,
    ) -> None:
        export_path = Path(export_path)
        save_format = george.SaveFormat.from_extension(export_path.suffix)

        with render_context(alpha_mode, save_format, format_opts, layers):
            george.tv_clip_save_structure_sprite(export_path, layout, space)

    @set_as_current
    def export_flix(
        self,
        export_path: Path | str,
        start: int | None = None,
        end: int | None = None,
        import_parameters: str = "",
        file_parameters: str = "",
        send: bool = False,
        layers: list[Layer] | None = None,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        format_opts: list[str] | None = None,
    ) -> None:
        export_path = Path(export_path)

        if export_path.suffix != ".xml":
            raise ValueError("Export path must have .xml extension")

        original_file = self.project.path
        import_parameters = (
            import_parameters
            or 'waitForSource="1" multipleSetups="1" replaceSelection="0"'
        )

        # The project needs to be saved
        self.project.save()

        # save alpha mode and save format values
        with render_context(alpha_mode, None, format_opts, layers):
            george.tv_clip_save_structure_flix(
                export_path,
                start,
                end,
                import_parameters,
                file_parameters,
                send,
                original_file,
            )

    @property
    @set_as_current
    def mark_in(self) -> int | None:
        frame, mark_action = george.tv_mark_in_get(reference=george.MarkReference.CLIP)
        if mark_action == george.MarkAction.CLEAR:
            return None
        return frame + self.project.start_frame

    @mark_in.setter
    @set_as_current
    def mark_in(self, value: int | None) -> None:
        action = george.MarkAction.CLEAR if value is None else george.MarkAction.SET
        frame = (
            ((self.mark_in or 0) - self.project.start_frame)
            if value is None
            else (value - self.project.start_frame)
        )
        george.tv_mark_in_set(
            reference=george.MarkReference.CLIP, frame=frame, action=action
        )

    @property
    @set_as_current
    def mark_out(self) -> int | None:
        frame, mark_action = george.tv_mark_out_get(reference=george.MarkReference.CLIP)
        if mark_action == george.MarkAction.CLEAR:
            return None
        return frame + self.project.start_frame

    @mark_out.setter
    @set_as_current
    def mark_out(self, value: int | None) -> None:
        value = (value or 0) - self.project.start_frame
        george.tv_mark_out_set(
            reference=george.MarkReference.CLIP,
            frame=value,
            action=george.MarkAction.SET,
        )

    @property
    def layer_colors(self) -> Iterator[LayerColor]:
        for color_index in range(26):
            yield LayerColor(color_index=color_index, clip=self)

    def set_layer_color(
        self,
        index: int,
        color: george.RGBColor,
        name: str | None = None,
    ) -> None:
        george.tv_layer_color_set_color(self.id, index, color, name)

    def get_layer_color(
        self,
        by_index: int | None = None,
        by_name: str | None = None,
    ) -> LayerColor:
        if not by_index and by_name:
            raise ValueError(
                "At least one value (by_index or by_name) must be provided"
            )

        if by_index is not None:
            return next(c for i, c in enumerate(self.layer_colors) if i == by_index)

        try:
            return next(c for c in self.layer_colors if c.name == by_name)
        except StopIteration:
            raise ValueError(
                f"No LayerColor found with name ({by_name}) in Clip ({self.name})"
            )

    @property
    def bookmarks(self) -> Iterator[int]:
        bookmarks_iter = position_generator(lambda pos: george.tv_bookmarks_enum(pos))
        project_start_frame = self.project.start_frame
        return (frame + project_start_frame for frame in bookmarks_iter)

    def add_bookmark(self, frame: int) -> None:
        george.tv_bookmark_set(frame - self.project.start_frame)

    def remove_bookmark(self, frame: int) -> None:
        george.tv_bookmark_clear(frame - self.project.start_frame)

    def clear_bookmarks(self) -> None:
        """Remove all the bookmarks"""
        bookmarks = list(self.bookmarks)
        for frame in bookmarks:
            self.remove_bookmark(frame)

    @set_as_current
    def go_to_previous_bookmark(self) -> None:
        george.tv_bookmark_prev()

    @set_as_current
    def go_to_next_bookmark(self) -> None:
        george.tv_bookmark_next()

    @property
    def sounds(self) -> Iterator[ClipSound]:
        """Iterates through the clip sound tracks"""
        sounds_data = position_generator(
            lambda pos: george.tv_sound_clip_info(self.id, pos)
        )

        for track_index, _ in enumerate(sounds_data):
            yield ClipSound(track_index, clip=self)

    def get_sound(
        self,
        by_id: int | None = None,
        by_path: Path | str | None = None,
    ) -> ClipSound | None:
        for sound in self.sounds:
            if (by_id and sound.id == by_id) or (by_path and sound.path == by_path):
                return sound
        raise ValueError("Can't find sound")

    def add_sound(self, sound_path: Path | str) -> ClipSound:
        """Adds a new clip sound track"""
        return ClipSound.new(sound_path, parent=self)
