"""Scene class."""

from __future__ import annotations

from collections.abc import Iterator

from pytvpaint import george, utils
from pytvpaint.clip import Clip
from pytvpaint.project import Project
from pytvpaint.utils import (
    Removable,
    set_as_current,
)


class Scene(Removable):
    """A Scene is a collection of clips. A Scene is inside a project."""

    def __init__(self, scene_id: int, project: Project) -> None:
        super().__init__()
        self._id: int = scene_id
        self._project = project

    def __repr__(self) -> str:
        """String representation of the scene."""
        return f"Scene()<id:{self.id}>"

    def __eq__(self, other: object) -> bool:
        """Two scenes are equal if their id is the same."""
        if not isinstance(other, Scene):
            return NotImplemented
        return self.id == other.id

    @staticmethod
    def current_scene_id() -> int:
        """Returns the current scene id (the current clip's scene)."""
        return george.tv_scene_current_id()

    @staticmethod
    def current_scene() -> Scene:
        """Returns the current scene of the current project."""
        return Scene(
            scene_id=george.tv_scene_current_id(),
            project=Project.current_project(),
        )

    @classmethod
    def new(cls, project: Project | None = None) -> Scene:
        """Creates a new scene in the provided project."""
        project = project or Project.current_project()
        project.make_current()
        george.tv_scene_new()
        return cls.current_scene()

    def make_current(self) -> None:
        """Make this scene the current one."""
        if self.is_current:
            return

        # In order to select the scene, we select any child clip inside of it
        first_clip_id = george.tv_clip_enum_id(self.id, 0)
        george.tv_clip_select(first_clip_id)

    @property
    def is_current(self) -> bool:
        """Returns `True` if the scene is the current one."""
        return self.id == self.current_scene_id()

    @property
    def id(self) -> int:
        """The scene id."""
        return self._id

    @property
    def project(self) -> Project:
        """The scene's project."""
        return self._project

    @property
    def position(self) -> int:
        """The scene's position in the project.

        Raises:
            ValueError: if scene cannot be found in the project
        """
        for pos, other_id in enumerate(self.project.current_scene_ids()):
            if other_id == self.id:
                return pos
        raise Exception("The scene doesn't exist anymore")

    @position.setter
    def position(self, value: int) -> None:
        value = max(0, value)
        george.tv_scene_move(self.id, value)

    @property
    @set_as_current
    def clip_ids(self) -> Iterator[int]:
        """Returns an iterator over the clip ids."""
        return utils.position_generator(
            lambda pos: george.tv_clip_enum_id(self.id, pos)
        )

    @property
    def clips(self) -> Iterator[Clip]:
        """Yields the scene clips."""
        for clip_id in self.clip_ids:
            yield Clip(clip_id, project=self._project)

    def get_clip(
        self,
        by_id: int | None = None,
        by_name: str | None = None,
    ) -> Clip | None:
        """Find a clip by id or by name."""
        for clip in self.clips:
            if (by_id and clip.id == by_id) or (by_name and clip.name == by_name):
                return clip

        return None

    @set_as_current
    def add_clip(self, clip_name: str) -> Clip:
        """Adds a new clip to the scene."""
        self.make_current()
        return Clip.new(name=clip_name, project=self.project)

    def duplicate(self) -> Scene:
        """Duplicate the scene and return it."""
        self.project.make_current()
        george.tv_scene_duplicate(self.id)
        dup_pos = self.position + 1
        dup_id = george.tv_scene_enum_id(dup_pos)
        return Scene(dup_id, self.project)

    def remove(self) -> None:
        """Remove the scene and all the clips inside.

        Warning:
            All `Clip` instances will be invalid after removing the scene.
            There's no protection mechanism to prevent accessing clip data that doesn't exist anymore.
        """
        george.tv_scene_close(self._id)
        self.mark_removed()
