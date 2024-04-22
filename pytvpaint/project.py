"""Project class."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

from fileseq.filesequence import FileSequence

from pytvpaint import george, utils
from pytvpaint.george.exceptions import GeorgeError
from pytvpaint.sound import ProjectSound
from pytvpaint.utils import (
    Refreshable,
    Renderable,
    refreshed_property,
    set_as_current,
)

if TYPE_CHECKING:
    from pytvpaint.clip import Clip
    from pytvpaint.scene import Scene


class Project(Refreshable, Renderable):
    """A TVPaint project is the highest object that contains everything in the data hierarchy.

    It looks like this: Project -> Scene -> Clip -> Layer -> LayerInstance
    """

    def __init__(self, project_id: str) -> None:
        super().__init__()
        self._id = project_id
        self._is_closed = False
        self._data = george.tv_project_info(self._id)

    def __repr__(self) -> str:
        """String representation of the project."""
        return f"Project({self.name})<id:{self.id}>"

    def __eq__(self, other: object) -> bool:
        """Two projects are equal if their id are the same."""
        if not isinstance(other, Project):
            return NotImplemented
        return self.id == other.id

    def refresh(self) -> None:
        """Refreshed the project data.

        Raises:
            ValueError: if project has been closed
        """
        if self._is_closed:
            msg = "Project already closed, load the project again to get data"
            raise ValueError(msg)
        if not self.refresh_on_call and self._data:
            return

        self._data = george.tv_project_info(self._id)

    @property
    def id(self) -> str:
        """The project id.

        Note:
            the id is persistent on project load/close.
        """
        return self._id

    @property
    def position(self) -> int:
        """The project's position in the project tabs.

        Raises:
            ValueError: if project cannot be found in open projects

        Note:
            the indices go from right to left in the UI
        """
        for pos, project_id in enumerate(self.open_projects_ids()):
            if project_id == self.id:
                return pos
        raise ValueError(f"No project found open with id: {self.id}")

    @property
    def is_closed(self) -> bool:
        """Returns `True` if the project is closed."""
        try:
            george.tv_project_info(self._id)
            self._is_closed = False
        except GeorgeError:
            self._is_closed = True

        return self._is_closed

    @property
    def exists(self) -> bool:
        """Checks if the project exists on disk."""
        return self.path.is_file() and self.path.suffix in [".tvpp", ".tvp"]

    @property
    def is_current(self) -> bool:
        """Returns `True` if the project is the current selected one in the UI."""
        return self.id == Project.current_project_id()

    def make_current(self) -> None:
        """Make the project the current one."""
        if self.is_current:
            return
        george.tv_project_select(self.id)

    @refreshed_property
    def path(self) -> Path:
        """The project path on disk."""
        return self._data.path

    @property
    def name(self) -> str:
        """The name of the project which is the filename without the extension."""
        return self.path.stem

    @property
    @set_as_current
    def width(self) -> int:
        """The width of the canvas."""
        return george.tv_get_width()

    @property
    @set_as_current
    def height(self) -> int:
        """The height of the canvas."""
        return george.tv_get_height()

    @set_as_current
    def resize(
        self,
        width: int,
        height: int,
        overwrite: bool = False,
        resize_opt: george.ResizeOption | None = None,
    ) -> Project:
        """Resize the current project and returns a new one.

        Args:
            width: the new width
            height: the new height
            overwrite: overwrite the original project, default is to create a new project
            resize_opt: how to resize the project

        Returns:
            the newly resized project
        """
        if (width, height) == (self.width, self.height):
            return self

        origin_position = self.position
        origin_path = self.path

        if resize_opt:
            george.tv_resize_page(width, height, resize_opt)
        else:
            george.tv_resize_project(width, height)

        # The resized project is at the same position and replaced the original one
        resized_id = george.tv_project_enum_id(origin_position)
        resized_project = Project(resized_id)

        if overwrite:
            resized_project.save(origin_path)

        return resized_project

    @property
    @set_as_current
    def fps(self) -> float:
        """The project's framerate."""
        project_fps, _ = george.tv_frame_rate_get()
        return project_fps

    @property
    @set_as_current
    def playback_fps(self) -> float:
        """The project's playback framerate."""
        _, playback_fps = george.tv_frame_rate_get()
        return playback_fps

    @set_as_current
    def set_fps(
        self,
        fps: float,
        time_stretch: bool = False,
        preview: bool = False,
    ) -> None:
        """Set the project's framerate."""
        george.tv_frame_rate_set(fps, time_stretch, preview)

    @property
    def field_order(self) -> george.FieldOrder:
        """The field order."""
        return george.tv_get_field()

    @refreshed_property
    @set_as_current
    def pixel_aspect_ratio(self) -> float:
        """The project's pixel aspect ratio."""
        return self._data.pixel_aspect_ratio

    @property
    @set_as_current
    def start_frame(self) -> int:
        """The project's start frame."""
        return george.tv_start_frame_get()

    @start_frame.setter
    @set_as_current
    def start_frame(self, value: int) -> None:
        george.tv_start_frame_set(value)

    @property
    @set_as_current
    def end_frame(self) -> int:
        """The project's end frame, meaning the last frame of the last clip in the project's timeline."""
        clips_duration = sum(clip.duration for clip in self.clips)
        return self.start_frame + clips_duration - 1

    @property
    @set_as_current
    def current_frame(self) -> int:
        """Get the current frame relative to the timeline."""
        return george.tv_project_current_frame_get() + self.start_frame

    @current_frame.setter
    @set_as_current
    def current_frame(self, value: int) -> None:
        # when setting the current frame, if it is outside the current clip's range, TVP will switch to the clip but not
        # the required frame. So we need to set it twice, one to switch the clip, and once again to set the frame
        set_twice = not (
            self.current_clip.timeline_start <= value <= self.current_clip.timeline_end
        )

        real_frame = value - self.start_frame
        george.tv_project_current_frame_set(real_frame)
        if set_twice:
            george.tv_project_current_frame_set(real_frame)

    @property
    @set_as_current
    def background_mode(self) -> george.BackgroundMode:
        """Get/Set the background mode."""
        return george.tv_background_get()[0]

    @background_mode.setter
    @set_as_current
    def background_mode(self, mode: george.BackgroundMode) -> None:
        george.tv_background_set(mode)

    @property
    @set_as_current
    def background_colors(
        self,
    ) -> tuple[george.RGBColor, george.RGBColor] | george.RGBColor | None:
        """Get/Set the background color(s).

        Returns:
            a tuple of two colors if checker, a single color if solid or None if empty
        """
        return george.tv_background_get()[1]

    @background_colors.setter
    @set_as_current
    def background_colors(
        self,
        colors: tuple[george.RGBColor, george.RGBColor] | george.RGBColor,
    ) -> None:
        george.tv_background_set(self.background_mode, colors)

    @set_as_current
    def clear_background(self) -> None:
        """Clear the background color and set it to None."""
        self.background_mode = george.BackgroundMode.NONE
        self.background_colors = (
            george.RGBColor(255, 255, 255),
            george.RGBColor(0, 0, 0),
        )

    @property
    def header_info(self) -> str:
        """The project's header info."""
        return george.tv_project_header_info_get(self.id)

    @header_info.setter
    def header_info(self, value: str) -> None:
        george.tv_project_header_info_set(self.id, value)

    @property
    def author(self) -> str:
        """The project's author info."""
        return george.tv_project_header_author_get(self.id)

    @author.setter
    def author(self, value: str) -> None:
        george.tv_project_header_author_set(self.id, value)

    @property
    def notes(self) -> str:
        """The project's notes text."""
        return george.tv_project_header_notes_get(self.id)

    @notes.setter
    def notes(self, value: str) -> None:
        george.tv_project_header_notes_set(self.id, value)

    @classmethod
    def get_project(
        cls,
        by_id: str | None = None,
        by_name: str | None = None,
    ) -> Project | None:
        """Find a project by id or by name."""
        for project in Project.open_projects():
            if (by_id and project.id == by_id) or (by_name and project.name == by_name):
                return project

        return None

    @staticmethod
    def current_scene_ids() -> Iterator[int]:
        """Yields the current project's scene ids."""
        return utils.position_generator(lambda pos: george.tv_scene_enum_id(pos))

    @property
    def current_scene(self) -> Scene:
        """Get the current scene of the project.

        Raises:
            ValueError: if scene cannot be found in project
        """
        for scene in self.scenes:
            if scene.is_current:
                return scene
        raise ValueError(f"Could not find current scene in Project {Project}")

    @property
    @set_as_current
    def scenes(self) -> Iterator[Scene]:
        """Yields the project's scenes."""
        from pytvpaint.scene import Scene

        for scene_id in self.current_scene_ids():
            yield Scene(scene_id, self)

    def get_scene(
        self,
        by_id: int | None = None,
        by_name: str | None = None,
    ) -> Scene | None:
        """Find a scene in the project by id or name."""
        for scene in self.scenes:
            if (by_id and scene.id == by_id) or (by_name and scene.name == by_name):
                return scene

        return None

    @set_as_current
    def add_scene(self) -> Scene:
        """Add a new scene in the project."""
        from pytvpaint.scene import Scene

        return Scene.new(project=self)

    @property
    @set_as_current
    def current_clip(self) -> Clip:
        """Returns the project's current clip."""
        from pytvpaint.clip import Clip

        return Clip.current_clip()

    @property
    def clips(self) -> Iterator[Clip]:
        """Iterates over all the clips in the project's scenes."""
        for scene in self.scenes:
            yield from scene.clips

    @property
    @set_as_current
    def clip_names(self) -> Iterator[str]:
        """Optimized way to get the clip names. Useful for `get_unique_name`."""
        for scene_id in self.current_scene_ids():
            clip_ids = utils.position_generator(
                lambda pos: george.tv_clip_enum_id(scene_id, pos)
            )
            for clip_id in clip_ids:
                yield george.tv_clip_name_get(clip_id)

    def get_clip(
        self,
        by_id: int | None = None,
        by_name: str | None = None,
        scene_id: int | None = None,
    ) -> Clip | None:
        """Find a clip by id, name or scene_id."""
        clips = self.clips
        if scene_id:
            selected_scene = self.get_scene(by_id=scene_id)
            clips = selected_scene.clips if selected_scene else clips

        for clip in clips:
            if (by_id and clip.id == by_id) or (by_name and clip.name == by_name):
                return clip

        return None

    def add_clip(self, clip_name: str, scene: Scene | None = None) -> Clip:
        """Add a new clip in the given scene or the current one if no scene provided."""
        scene = scene or self.current_scene
        return scene.add_clip(clip_name)

    @property
    def sounds(self) -> Iterator[ProjectSound]:
        """Iterator over the project sounds."""
        sounds_data_iter = utils.position_generator(
            lambda pos: george.tv_sound_project_info(self.id, pos)
        )

        for track_index, _ in enumerate(sounds_data_iter):
            yield ProjectSound(track_index, project=self)

    def add_sound(self, sound_path: Path | str) -> ProjectSound:
        """Add a new sound clip to the project."""
        return ProjectSound.new(sound_path, parent=self)

    def _validate_range(self, start: int, end: int) -> None:
        project_start_frame = self.start_frame
        project_end_frame = self.end_frame
        project_mark_in = self.mark_in
        project_mark_out = self.mark_out

        proj_full_range = (
            min(project_mark_in or project_start_frame, project_start_frame),
            max(project_mark_out or project_end_frame, project_end_frame),
        )
        if start < proj_full_range[0] or end > proj_full_range[1]:
            raise ValueError(
                f"Range ({start}-{end}) outside of project bounds ({proj_full_range})"
            )

    def _get_real_range(self, start: int, end: int) -> tuple[int, int]:
        project_start_frame = self.start_frame
        start -= project_start_frame
        end -= project_start_frame

        return start, end

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
        """Render the project to a single frame or frame sequence or movie.

        Args:
            output_path: a single file or file sequence pattern
            start: the start frame to render or the mark in or the project's start frame if None. Defaults to None.
            end: the end frame to render or the mark out or the project's end frame if None. Defaults to None.
            use_camera: use the camera for rendering, otherwise render the whole canvas. Defaults to False.
            alpha_mode: the alpha mode for rendering. Defaults to george.AlphaSaveMode.PREMULTIPLY.
            background_mode: the background mode for rendering. Defaults to george.BackgroundMode.NONE.
            format_opts: custom format options. Defaults to None.

        Raises:
            ValueError: if requested range (start-end) not in project range/bounds
            ValueError: if output is a movie, and it's duration is equal to 1 frame
            FileNotFoundError: if the render failed and no files were found on disk or missing frames

        Note:
            This functions uses the project's timeline as a basis for the range (start-end). This timeline includes all
            the project's clips and is different from a clip range. For more details on the differences in frame ranges
            and the timeline in TVPaint, please check the `Usage/Rendering` section of the documentation.

        Warning:
            Even tough pytvpaint does a pretty good job of correcting the frame ranges for rendering, we're still
            encountering some weird edge cases where TVPaint will consider the range invalid for seemingly no reason.
        """
        default_start = self.mark_in or self.start_frame
        default_end = self.mark_out or self.end_frame

        self._render(
            output_path,
            default_start,
            default_end,
            start,
            end,
            use_camera,
            layer_selection=None,
            alpha_mode=alpha_mode,
            background_mode=background_mode,
            format_opts=format_opts,
        )

    @set_as_current
    def render_clips(
        self,
        clips: list[Clip],
        output_path: Path | str | FileSequence,
        use_camera: bool = False,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        background_mode: george.BackgroundMode | None = None,
        format_opts: list[str] | None = None,
    ) -> None:
        """Render sequential clips as a single output."""
        clips = sorted(clips, key=lambda c: c.position)
        start = clips[0].timeline_start
        end = clips[-1].timeline_end
        self.render(
            output_path,
            start,
            end,
            use_camera,
            alpha_mode,
            background_mode,
            format_opts,
        )

    @staticmethod
    def current_project_id() -> str:
        """Returns the current project id."""
        return george.tv_project_current_id()

    @staticmethod
    def current_project() -> Project:
        """Returns the current project."""
        return Project(project_id=Project.current_project_id())

    @staticmethod
    def open_projects_ids() -> Iterator[str]:
        """Yields the ids of the currently open projects."""
        return utils.position_generator(lambda pos: george.tv_project_enum_id(pos))

    @classmethod
    def open_projects(cls) -> Iterator[Project]:
        """Iterator over the currently open projects."""
        for project_id in Project.open_projects_ids():
            yield Project(project_id)

    @property
    @set_as_current
    def mark_in(self) -> int | None:
        """Get the project mark in or None if no mark in set."""
        frame, mark_action = george.tv_mark_in_get(
            reference=george.MarkReference.PROJECT
        )
        if mark_action == george.MarkAction.CLEAR:
            return None
        return frame + self.start_frame

    @mark_in.setter
    @set_as_current
    def mark_in(self, value: int | None) -> None:
        if value is None:
            action = george.MarkAction.CLEAR
            value = self.mark_in or 0
        else:
            action = george.MarkAction.SET
            value = value

        frame = value - self.start_frame
        george.tv_mark_in_set(
            reference=george.MarkReference.PROJECT, frame=frame, action=action
        )

    @property
    @set_as_current
    def mark_out(self) -> int | None:
        """Get the project mark out or None if no mark out set."""
        frame, mark_action = george.tv_mark_out_get(
            reference=george.MarkReference.PROJECT
        )
        if mark_action == george.MarkAction.CLEAR:
            return None
        return frame

    @mark_out.setter
    @set_as_current
    def mark_out(self, value: int | None) -> None:
        if value is None:
            action = george.MarkAction.CLEAR
            value = self.mark_out or 0
        else:
            action = george.MarkAction.SET
            value = value

        frame = value - self.start_frame
        george.tv_mark_out_set(
            reference=george.MarkReference.CLIP,
            frame=frame,
            action=action,
        )

    @classmethod
    def new(
        cls,
        project_path: Path | str,
        width: int = 1920,
        height: int = 1080,
        pixel_aspect_ratio: float = 1.0,
        frame_rate: float = 24.0,
        field_order: george.FieldOrder = george.FieldOrder.NONE,
        start_frame: int = 1,
    ) -> Project:
        """Create a new project."""
        george.tv_project_new(
            Path(project_path).resolve().as_posix(),
            width,
            height,
            pixel_aspect_ratio,
            frame_rate,
            field_order,
            start_frame,
        )
        return cls.current_project()

    @set_as_current
    def new_from_camera(self, export_path: Path | str | None = None) -> Project:
        """Create a new cropped project from the camera view."""
        cam_project_id = george.tv_project_render_camera(self.id)
        cam_project = Project(cam_project_id)

        if export_path:
            export_path = Path(export_path)
            export_path.mkdir(exist_ok=True, parents=True)
            cam_project.save(export_path)

        return cam_project

    @set_as_current
    def duplicate(self) -> Project:
        """Duplicate the project and return the new one."""
        george.tv_project_duplicate()
        duplicated = Project.current_project()
        self.make_current()
        return duplicated

    def close(self) -> None:
        """Closes the project."""
        self._is_closed = True
        george.tv_project_close(self._id)

    @classmethod
    def close_all(cls, close_tvp: bool = False) -> None:
        """Closes all open projects.

        Args:
            close_tvp: close the TVPaint instance as well
        """
        for project in list(cls.open_projects()):
            project.close()

        if close_tvp:
            george.tv_quit()

    @classmethod
    def load(cls, project_path: Path | str, silent: bool = True) -> Project:
        """Load an existing .tvpp/.tvp project or .tvpx file."""
        project_path = Path(project_path)

        # Check if project not already open, if so, return it
        for project in cls.open_projects():
            if project.path == project_path:
                return project

        george.tv_load_project(project_path, silent)
        return cls.current_project()

    def save(self, save_path: Path | str | None = None) -> None:
        """Saves the project on disk."""
        save_path = Path(save_path or self.path).resolve()
        george.tv_save_project(save_path.as_posix())

    @set_as_current
    def load_panel(self, panel_path: Path | str) -> None:
        """Load an external TVPaint panel."""
        george.tv_load_project(panel_path, silent=True)

    @set_as_current
    def load_palette(self, palette_path: Path | str) -> None:
        """Load a palette."""
        george.tv_save_palette(palette_path)

    @set_as_current
    def save_palette(self, save_path: Path | str | None = None) -> None:
        """Save a palette to the given path."""
        save_path = Path(save_path or self.path)
        george.tv_save_project(save_path)

    @set_as_current
    def save_video_dependencies(self) -> None:
        """Saves the video dependencies."""
        george.tv_project_save_video_dependencies()

    @set_as_current
    def save_audio_dependencies(self) -> None:
        """Saves audio dependencies."""
        george.tv_project_save_audio_dependencies()
