"""Sound related classes (Clip and Project sounds)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from typing_extensions import Self

from pytvpaint import george, utils
from pytvpaint.utils import (
    CanMakeCurrent,
    Removable,
    refreshed_property,
    set_as_current,
)

if TYPE_CHECKING:
    from pytvpaint.clip import Clip
    from pytvpaint.project import Project

P = TypeVar("P", bound=CanMakeCurrent)


class BaseSound(Removable, ABC, Generic[P]):
    """Base sound class for project and clip sounds."""

    def __init__(
        self,
        track_index: int,
        parent: P,
    ) -> None:
        super().__init__()
        self._parent = parent
        self._data: george.TVPSound = self._info(self._parent.id, track_index)

    @staticmethod
    @abstractmethod
    def _new(sound_path: Path) -> None:
        """Create a new sound."""
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def _info(parent_id: str | int, track_index: int) -> george.TVPSound:
        """Get the sound data based on the track index."""
        raise NotImplementedError()

    @abstractmethod
    def _adjust(self, **kwargs: Any) -> None:
        """Modify the sound data."""
        raise NotImplementedError()

    @abstractmethod
    def remove(self) -> None:
        """Remove the sound."""
        raise NotImplementedError()

    @abstractmethod
    def reload(self) -> None:
        """Reload the sound element from source."""
        raise NotImplementedError()

    @classmethod
    def iter_sounds_data(cls, parent_id: str | int) -> Iterator[george.TVPSound]:
        """Iterator over the sound's data."""
        return utils.position_generator(
            lambda track_index: cls._info(parent_id, track_index)
        )

    def make_current(self) -> None:
        """Make the parent object current (there's no way to make a sound current)."""
        raise NotImplementedError()

    @classmethod
    def new(cls: type[Self], sound_path: Path | str, parent: P) -> Self:
        """Create a new sound from the sound path."""
        parent.make_current()
        cls._new(Path(sound_path))
        last_index = len(list(cls.iter_sounds_data(parent.id))) - 1
        return cls(last_index, parent)

    def refresh(self) -> None:
        """Refreshes the sound data."""
        super().refresh()
        if not self.refresh_on_call and self._data:
            return
        self._data = self._info(self.parent.id, self.track_index)

    @property
    def track_index(self) -> int:
        """Get the soundtrack index in the sound stack.

        Raises:
            ValueError: if sound object no longer exists
        """
        # Recomputes the track_index each time because some track
        # can be deleted in the meantime
        for index, data in enumerate(self.iter_sounds_data(self._parent.id)):
            if data == self._data:
                return index
        raise ValueError("The sound doesn't exist anymore")

    @refreshed_property
    def offset(self) -> float:
        """The sound offset in the timeline."""
        return self._data.offset

    @offset.setter
    def offset(self, value: float) -> None:
        self._adjust(offset=value)

    @refreshed_property
    def volume(self) -> float:
        """The volume of the sound."""
        return self._data.volume

    @volume.setter
    @set_as_current
    def volume(self, value: float) -> None:
        self._adjust(volume=value)

    @refreshed_property
    def is_muted(self) -> bool:
        """Returns `True` if the sound is muted."""
        return self._data.mute

    @is_muted.setter
    @set_as_current
    def is_muted(self, value: bool) -> None:
        self._adjust(mute=value)

    @refreshed_property
    def fade_in_start(self) -> float:
        """The fade in start time."""
        return self._data.fade_in_start

    @fade_in_start.setter
    @set_as_current
    def fade_in_start(self, value: float) -> None:
        self._adjust(fade_in_start=value)

    @refreshed_property
    def fade_in_stop(self) -> float:
        """The fade in stop time."""
        return self._data.fade_in_stop

    @fade_in_stop.setter
    @set_as_current
    def fade_in_stop(self, value: float) -> None:
        self._adjust(fade_in_stop=value)

    @refreshed_property
    def fade_out_start(self) -> float:
        """The fade out start time."""
        return self._data.fade_out_start

    @fade_out_start.setter
    @set_as_current
    def fade_out_start(self, value: float) -> None:
        self._adjust(fade_out_start=value)

    @refreshed_property
    def fade_out_stop(self) -> float:
        """The fade out stop time."""
        return self._data.fade_out_stop

    @fade_out_stop.setter
    @set_as_current
    def fade_out_stop(self, value: float) -> None:
        self._adjust(fade_out_stop=value)

    @refreshed_property
    def path(self) -> Path:
        """The sound source file path."""
        return self._data.path

    @refreshed_property
    def sound_in(self) -> float:
        """The start time of the sound."""
        return self._data.sound_in

    @refreshed_property
    def sound_out(self) -> float:
        """The end time of the sound."""
        return self._data.sound_out

    @refreshed_property
    def color_index(self) -> int:
        """The sound color index."""
        return self._data.color_index

    @color_index.setter
    @set_as_current
    def color_index(self, value: int) -> None:
        self._adjust(color_index=value)


class ClipSound(BaseSound["Clip"]):
    """A clip sound."""

    def __init__(
        self,
        track_index: int,
        clip: Clip | None = None,
    ) -> None:
        from pytvpaint.clip import Clip

        clip = clip or Clip.current_clip()
        super().__init__(track_index, clip)

    def __eq__(self, other: object) -> bool:
        """Two clip sounds are equal if their track index is the same."""
        if not isinstance(other, ClipSound):
            return NotImplemented
        return self.track_index == other.track_index

    @staticmethod
    def _info(parent_id: str | int, track_index: int) -> george.TVPSound:
        return george.tv_sound_clip_info(int(parent_id), track_index)

    @set_as_current
    def _adjust(self, **kwargs: Any) -> None:
        return george.tv_sound_clip_adjust(self.track_index, **kwargs)

    @staticmethod
    def _new(sound_path: Path) -> None:
        george.tv_sound_clip_new(sound_path)

    @property
    def clip(self) -> Clip:
        """The sound's clip."""
        return self._parent

    def make_current(self) -> None:
        """Makes the sound clip current."""
        self.clip.make_current()

    @set_as_current
    def remove(self) -> None:
        """Remove the sound from the clip."""
        george.tv_sound_clip_remove(self.track_index)
        self.mark_removed()

    @set_as_current
    def reload(self) -> None:
        """Reload the sound from file."""
        george.tv_sound_clip_reload(self._parent.id, self.track_index)


class ProjectSound(BaseSound["Project"]):
    """A Project sound."""

    def __init__(
        self,
        track_index: int,
        project: Project | None = None,
    ) -> None:
        from pytvpaint.project import Project

        project = project or Project.current_project()
        super().__init__(track_index, project)

    def __eq__(self, other: object) -> bool:
        """Two project sounds are equal if their track index is the same."""
        if not isinstance(other, ProjectSound):
            return NotImplemented
        return self.track_index == other.track_index

    @staticmethod
    def _new(sound_path: Path) -> None:
        george.tv_sound_project_new(sound_path)

    @staticmethod
    def _info(parent_id: str | int, track_index: int) -> george.TVPSound:
        return george.tv_sound_project_info(str(parent_id), track_index)

    @set_as_current
    def _adjust(self, **kwargs: Any) -> None:
        return george.tv_sound_project_adjust(self.track_index, **kwargs)

    @property
    def project(self) -> Project:
        """The sound's project."""
        return self._parent

    @set_as_current
    def remove(self) -> None:
        """Remove the sound from the project."""
        george.tv_sound_project_remove(self.track_index)
        self.mark_removed()

    def reload(self) -> None:
        """Reload the sound from file."""
        george.tv_sound_project_reload(self.project.id, self.track_index)

    def make_current(self) -> None:
        """Makes the sound project current."""
        self.project.make_current()
