"""Project class."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Iterator

from fileseq.filesequence import FileSequence

from pytvpaint import george
from pytvpaint.george.exceptions import GeorgeError
from pytvpaint.sound import ProjectSound
from pytvpaint.utils import (
    Refreshable,
    position_generator,
    refreshed_property,
    set_as_current,
)

if TYPE_CHECKING:
    from pytvpaint.clip import Clip
    from pytvpaint.layer import Layer
    from pytvpaint.scene import Scene


class Project(Refreshable):
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
        """Refreshed the project data."""
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
        """The project position in the project tabs.

        Note:
            the indices are visually increasing from right to left in the interface
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
        """Checks if the project exists on disk"""
        return self.path.is_file() and self.path.suffix in [".tvpp", ".tvp"]

    @property
    def is_current(self) -> bool:
        """Returns `True` if the project is current in the UI."""
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
            overwrite: ovewrite the original project, default is to create a new project
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
        """The project framerate."""
        project_fps, _ = george.tv_frame_rate_get()
        return project_fps

    @property
    @set_as_current
    def playback_fps(self) -> float:
        """The project playback framerate."""
        _, playback_fps = george.tv_frame_rate_get()
        return playback_fps

    @set_as_current
    def set_fps(
        self,
        fps: float,
        time_stretch: bool = False,
        preview: bool = False,
    ) -> None:
        """Set the project framerate."""
        george.tv_frame_rate_set(fps, time_stretch, preview)

    @property
    def field_order(self) -> george.FieldOrder:
        """The field order."""
        return george.tv_get_field()

    @refreshed_property
    @set_as_current
    def pixel_aspect_ratio(self) -> float:
        """The project pixel aspect ratio."""
        return self._data.pixel_aspect_ratio

    @property
    @set_as_current
    def start_frame(self) -> int:
        """The project start frame."""
        return george.tv_start_frame_get()

    @start_frame.setter
    @set_as_current
    def start_frame(self, value: int) -> None:
        george.tv_start_frame_set(value)

    @property
    @set_as_current
    def current_frame(self) -> int:
        """Get the current frame relative to the clip mark in or the start frame."""
        mark_in = self.current_clip.mark_in or self.start_frame
        return george.tv_project_current_frame_get() + mark_in

    @current_frame.setter
    @set_as_current
    def current_frame(self, value: int) -> None:
        start = self.current_clip.mark_in or self.start_frame
        george.tv_project_current_frame_set(value - start)

    @property
    def header_info(self) -> str:
        """The project header info."""
        return george.tv_project_header_info_get(self.id)

    @header_info.setter
    def header_info(self, value: str) -> None:
        george.tv_project_header_info_set(self.id, value)

    @property
    def author(self) -> str:
        """The project author info."""
        return george.tv_project_header_author_get(self.id)

    @author.setter
    def author(self, value: str) -> None:
        george.tv_project_header_author_set(self.id, value)

    @property
    def notes(self) -> str:
        """The project notes text."""
        return george.tv_project_header_notes_get(self.id)

    @notes.setter
    def notes(self, value: str) -> None:
        george.tv_project_header_notes_set(self.id, value)

    @classmethod
    def get_project(
        cls,
        by_id: str | None = None,
        by_name: str | None = None,
    ) -> Project:
        """Find a project by id or by name."""
        for project in Project.opened_projects():
            if (by_id and project.id == by_id) or (by_name and project.name == by_name):
                return project
        raise ValueError(f"Can't find a project with id: {by_id} and name: {by_name}")

    @staticmethod
    def current_scene_ids() -> Iterator[int]:
        """Yields the current project scene ids."""
        return position_generator(lambda pos: george.tv_scene_enum_id(pos))

    @property
    def current_scene(self) -> Scene:
        """Get the current scene of the project."""
        for scene in self.scenes:
            if scene.is_current:
                return scene
        raise ValueError(f"Could not find current scene in Project {Project}")

    @property
    @set_as_current
    def scenes(self) -> Iterator[Scene]:
        """Yields the project scenes."""
        from pytvpaint.scene import Scene

        for scene_id in self.current_scene_ids():
            yield Scene(scene_id, self)

    def get_scene(
        self,
        by_id: int | None = None,
        by_name: str | None = None,
    ) -> Scene:
        """Find a scene in that project by id or by name."""
        for scene in self.scenes:
            if (by_id and scene.id == by_id) or (by_name and scene.name == by_name):
                return scene
        raise ValueError("Scene not found")

    @set_as_current
    def add_scene(self) -> Scene:
        """Add a new scene in that project."""
        from pytvpaint.scene import Scene

        return Scene.new(project=self)

    @property
    def current_clip(self) -> Clip:
        """Returns the project's current clip."""
        for clip in self.clips:
            if clip.is_current:
                return clip
        raise ValueError(f"Could not find current clip in Project {Project}")

    @property
    def clips(self) -> Iterator[Clip]:
        """Iterates over all the clips in the project's scenes."""
        for scene in self.scenes:
            yield from scene.clips

    @set_as_current
    def _clip_names(self) -> Iterator[str]:
        """Optimized way to get the clip names. Useful for `get_unique_name`."""
        for scene_id in self.current_scene_ids():
            clip_ids = position_generator(
                lambda pos: george.tv_clip_enum_id(scene_id, pos)
            )
            for clip_id in clip_ids:
                yield george.tv_clip_name_get(clip_id)

    def get_clip(
        self,
        by_id: int | None = None,
        by_name: str | None = None,
        scene_id: int | None = None,
    ) -> Clip:
        """Find a clip by id, name or scene_id."""
        clips = self.get_scene(by_id=scene_id).clips if scene_id else self.clips

        for clip in clips:
            if (by_id and clip.id == by_id) or (by_name and clip.name == by_name):
                return clip

        raise ValueError("Clip not found")

    def add_clip(self, clip_name: str, scene: Scene | None = None) -> Clip:
        """Add a new clip in the given scene or the current one."""
        scene = scene or self.current_scene
        return scene.add_clip(clip_name)

    @property
    def sounds(self) -> Iterator[ProjectSound]:
        """Iterator over the project sounds."""
        sounds_data_iter = position_generator(
            lambda pos: george.tv_sound_project_info(self.id, pos)
        )

        for track_index, _ in enumerate(sounds_data_iter):
            yield ProjectSound(track_index, project=self)

    def add_sound(self, sound_path: Path | str) -> ProjectSound:
        """Add a new sound clip to the project."""
        return ProjectSound.new(sound_path, parent=self)

    @set_as_current
    def render(
        self,
        export_path: Path | str | FileSequence,
        clip: Clip | None = None,
        start: int | None = None,
        end: int | None = None,
        use_camera: bool = False,
        layers: list[Layer] | None = None,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        format_opts: list[str] | None = None,
    ) -> None:
        """Render the given clip or the current one. See the `Clip.render` method."""
        clip = clip or self.current_clip
        clip.render(
            export_path,
            start,
            end,
            use_camera,
            layers,
            alpha_mode,
            format_opts,
        )

    @staticmethod
    def current_project_id() -> str:
        """Returns the current project id."""
        return george.tv_project_current_id()

    @staticmethod
    def current_project() -> Project:
        """Returns the current project object."""
        return Project(project_id=Project.current_project_id())

    @staticmethod
    def open_projects_ids() -> Iterator[str]:
        """Yields the ids of the currently opened projects"""
        return position_generator(lambda pos: george.tv_project_enum_id(pos))

    @classmethod
    def open_projects(cls) -> Iterator[Project]:
        """Iterator over the currently opened projects"""
        for project_id in Project.open_projects_ids():
            yield Project(project_id)

    @property
    @set_as_current
    def mark_in(self) -> int | None:
        """Get the project mark in or None if no mark."""
        frame, mark_action = george.tv_mark_in_get(
            reference=george.MarkReference.PROJECT
        )

        if mark_action == george.MarkAction.CLEAR:
            return None

        return frame + self.start_frame

    @mark_in.setter
    @set_as_current
    def mark_in(self, value: int | None) -> None:
        if value:
            action = george.MarkAction.SET
            frame = value - self.start_frame
        else:
            action = george.MarkAction.CLEAR
            frame = (self.mark_in or 0) - self.start_frame

        george.tv_mark_in_set(
            reference=george.MarkReference.PROJECT, frame=frame, action=action
        )

    @property
    @set_as_current
    def mark_out(self) -> int | None:
        """Get the project mark out or None if no mark."""
        frame, mark_action = george.tv_mark_out_get(
            reference=george.MarkReference.PROJECT
        )
        if mark_action == george.MarkAction.CLEAR:
            return None
        return frame

    @mark_out.setter
    @set_as_current
    def mark_out(self, value: int | None) -> None:
        george.tv_mark_out_set(
            reference=george.MarkReference.PROJECT,
            frame=value,
            action=george.MarkAction.SET,
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

        duplicated_name = f"{self.name}Copy"
        for project in Project.open_projects():
            if project.name == duplicated_name:
                return project

        raise Exception(f"Couldn't find project {duplicated_name}")

    def close(self) -> None:
        """Closes the project."""
        self._is_closed = True
        george.tv_project_close(self._id)

    @classmethod
    def close_all(cls) -> None:
        projects = list(cls.open_projects())
        for project in projects:
            project.close()

    @classmethod
    def load(cls, project_path: Path | str, silent: bool = True) -> Project:
        """Load an existing .tvpp/.tvp project or .tvpx extension."""
        project_path = Path(project_path)

        # Check if project not already open, if so, return it
        for project in cls.open_projects():
            if project.path == project_path:
                return project

        george.tv_load_project(project_path, silent)
        return cls.current_project()

    def save(self, save_path: Path | str | None = None) -> None:
        """Saves the project on disk"""
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
