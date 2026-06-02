"""Utility functions and classes which are not specific to anything else in the codebase."""

from __future__ import annotations

import contextlib
import re
from abc import ABC, abstractmethod
from collections.abc import Generator, Iterable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast, runtime_checkable

from fileseq.filesequence import FileSequence
from fileseq.frameset import FrameSet
from typing_extensions import ParamSpec, Protocol

from pytvpaint import george, log
from pytvpaint.george.exceptions import GeorgeError

if TYPE_CHECKING:
    from pytvpaint.layer import Layer


class _CanRefresh(Protocol):
    def refresh(self) -> None: ...


if TYPE_CHECKING:
    refreshed_property = property
else:

    class RefreshedProperty(property):
        """Custom property that calls .refresh() before getting the actual value."""

        def __get__(self, __obj: _CanRefresh, __type: type | None = None) -> Any:
            """Calls .refresh() on the object before getting the value."""
            __obj.refresh()
            return super().__get__(__obj, __type)

    refreshed_property = RefreshedProperty


class Refreshable(ABC):
    """Abstract class that denotes an object that have data that can be refreshed (a TVPaint project for example)."""

    def __init__(self) -> None:
        self.refresh_on_call = True

    @abstractmethod
    def refresh(self) -> None:
        """Refreshes the object data."""
        raise NotImplementedError("Function refresh() needs to be implemented")


class Removable(Refreshable):
    """Abstract class that denotes an object that can be removed from TVPaint (a Layer for example)."""

    def __init__(self) -> None:
        super().__init__()
        self._is_removed: bool = False

    def __getattribute__(self, name: str) -> Any:
        """For each attribute access, we check if the object was marked removed."""
        if not name.startswith("_") and self._is_removed:
            if name in ["_is_removed", "is_removed"]:
                return self._is_removed
            raise ValueError(f"{self.__class__.__name__} has been removed!")

        return super().__getattribute__(name)

    def refresh(self) -> None:
        """Does a refresh of the object data.

        Raises:
            ValueError: if the object has been mark removed
        """
        if self._is_removed:
            raise ValueError(f"{self.__class__.__name__} has been removed!")

    @property
    def is_removed(self) -> bool:
        """Checks if the object is removed by trying to refresh its data.

        Returns:
            bool: whether if it was removed or not
        """
        is_removed = True
        with contextlib.suppress(Exception):
            self.refresh()
            is_removed = False
        self._is_removed = is_removed
        return self._is_removed

    @abstractmethod
    def remove(self) -> None:
        """Removes the object in TVPaint."""
        raise NotImplementedError("Function refresh() needs to be implemented")

    def mark_removed(self) -> None:
        """Marks the object as removed and is therefor not usable."""
        self._is_removed = True


class Renderable(ABC):
    """Abstract class that denotes an object that can be removed from TVPaint (a Layer for example)."""

    def __init__(self) -> None:
        super().__init__()

    @property
    @abstractmethod
    def current_frame(self) -> int:
        """Gives the current frame."""
        pass

    @current_frame.setter
    @abstractmethod
    def current_frame(self, frame: int) -> None:
        """Set the current frame."""
        pass

    def _get_real_range(self, start: int, end: int, frame_set: FrameSet | None = None) -> tuple[int, int, FrameSet]:
        """Removes the object in TVPaint."""
        raise NotImplementedError("Function refresh() needs to be implemented")

    def _validate_range(self, start: int, end: int) -> None:
        """Raises an exception if given range is invalid."""
        raise NotImplementedError("Function refresh() needs to be implemented")

    def _render(  # noqa: C901
        self,
        output_path: Path | str | FileSequence,
        default_start: int,
        default_end: int,
        start: int | None = None,
        end: int | None = None,
        frame_set: FrameSet | None = None,
        use_camera: bool = False,
        layer_selection: list[Layer] | None = None,
        alpha_mode: george.AlphaSaveMode = george.AlphaSaveMode.PREMULTIPLY,
        background_mode: george.BackgroundMode | None = None,
        format_opts: list[str] | None = None,
    ) -> Path | FileSequence:
        if (start or end) and not frame_set:
            log.warning("Use of `start` and `end` is deprecated, prefer using `fileseq.FrameSet()` instead.")
        if start and end and frame_set and any(f not in frame_set for f in (start, end)):
            log.warning("`start` and/or `end` outside of `frame_set` range, will prioritize FrameSet.")

        if frame_set is not None and not (start and end):
            frames = sorted(frame_set.items)
            start = start if start is not None or not frames else int(frames[0])
            end = end if end is not None or not frames else int(frames[-1])

        # finds range if none provided or in path and clamps it to the correct context
        file_sequence, start, end, is_sequence, is_image = handle_output_range(
            output_path, default_start, default_end, start, end
        )
        self._validate_range(start, end)

        # we should have a range by now, let's apply/save it
        if frame_set is not None:
            file_sequence.setFrameSet(frame_set)
        else:
            frame_set = file_sequence.frameSet()

        start, end, frame_set = self._get_real_range(start, end, frame_set)
        if not is_image and start == end:
            raise ValueError("TVPaint will not render a movie that contains a single frame")

        if is_sequence or (
            not is_sequence and FileSequence(str(output_path)).padding()
        ):  # get first frame, tvp doesn't understand vfx padding `#`
            first_frame = (
                sorted(file_sequence.frameSet().items)[0]  # type: ignore[union-attr]
                if file_sequence.frameSet() and len(file_sequence.frameSet()) >= 1  # type: ignore[arg-type]
                else file_sequence.start()
            )
            first_frame_file = Path(file_sequence.frame(first_frame))
        else:  # if movie or single image
            first_frame_file = Path(str(output_path))
        first_frame_file.parent.mkdir(exist_ok=True, parents=True)

        save_format = george.SaveFormat.from_extension(file_sequence.extension().lower())

        # render to output
        # not using tv_save_sequence since it doesn't handle camera and would require different range math
        with render_context(alpha_mode, background_mode, save_format, format_opts, layer_selection):
            if frame_set.isConsecutive():
                george.tv_project_save_sequence(
                    first_frame_file,
                    start=start,
                    end=end,
                    use_camera=use_camera,
                )
            else:
                frame_items = sorted(list(file_sequence.frameSet().items))  # type: ignore[union-attr]
                real_frame_items = sorted(frame_set.items)
                for frame_nb, real_frame_nb in zip(frame_items, real_frame_items):
                    frame_path = Path(file_sequence.frame(frame_nb))
                    george.tv_project_save_sequence(
                        export_path=frame_path,
                        start=int(real_frame_nb),
                        end=int(real_frame_nb),
                        use_camera=use_camera,
                    )

        # make sure the output exists otherwise raise an error
        if is_sequence:
            # raises error if sequence not found
            found_sequence = FileSequence.findSequenceOnDisk(str(file_sequence))
            frame_set = found_sequence.frameSet()
            file_sequence_frame_set = file_sequence.frameSet()

            if file_sequence_frame_set is None or frame_set is None:
                raise Exception("Sequence Should have a frame set !")

            if not frame_set.issuperset(file_sequence_frame_set):
                # not all frames found
                missing_frames = file_sequence_frame_set.difference(frame_set)
                raise FileNotFoundError(
                    f"Not all frames found, missing frames ({missing_frames}) in sequence : {output_path}"
                )
            return file_sequence
        if not first_frame_file.exists():
            raise FileNotFoundError(f"Could not find output at : {first_frame_file.as_posix()}")
        return first_frame_file


def get_unique_name(names: Iterable[str], stub: str) -> str:
    """Get a unique name from a list of names and a stub prefix. It does auto increment it.

    Args:
        names (Iterable[str]): existing names
        stub (str): the base name

    Raises:
        ValueError: if the stub is empty

    Returns:
        str: a unique name with the stub prefix
    """
    if not stub:
        raise ValueError("Stub is empty")

    number_re = re.compile(r"(?P<number>\d+)$", re.I)

    stub_without_number = number_re.sub("", stub)
    max_number = 0
    padding_length = 1

    for name in names:
        without_number = number_re.sub("", name)

        if without_number != stub_without_number:
            continue

        res = number_re.search(name)
        number = res.group("number") if res else "1"

        padding_length = max(padding_length, len(number))
        max_number = max(max_number, int(number))

    if max_number == 0:
        return stub

    next_number = max_number + 1
    return f"{stub_without_number}{next_number:0{padding_length}}"


T = TypeVar("T")


def position_generator(
    fn: Callable[[int], T],
    stop_when: type[GeorgeError] = GeorgeError,
) -> Iterator[T]:
    """Utility generator that yields the result of a function according to a position.

    Args:
        fn (Callable[[int], T]): the function to run at each iteration
        stop_when (Type[GeorgeError], optional): exception at which we stop. Defaults to GeorgeError.

    Yields:
        Iterator[T]: a generator of the resulting values
    """
    pos = 0

    while True:
        try:
            yield fn(pos)
        except stop_when:
            break
        pos += 1


class CanMakeCurrent(Protocol):
    """Describes an object that can do `make_current` and has an id."""

    @property
    def id(self) -> str | int:  # noqa: D102
        ...

    def make_current(self) -> None:  # noqa: D102
        ...


# See: https://stackoverflow.com/questions/47060133/python-3-type-hinting-for-decorator
Params = ParamSpec("Params")
ReturnType = TypeVar("ReturnType")


def set_as_current(func: Callable[Params, ReturnType]) -> Callable[Params, ReturnType]:
    """Decorator to apply on object methods.

    Sets the current TVPaint object as 'current'.
    Useful when George functions only apply on the current project, clip, layer or scene.

    Args:
        func (Callable[Params, ReturnType]): the method apply on

    Returns:
        Callable[Params, ReturnType]: the wrapped method
    """

    def wrapper(*args: Params.args, **kwargs: Params.kwargs) -> ReturnType:
        self = cast(CanMakeCurrent, args[0])
        self.make_current()
        return func(*args, **kwargs)

    return wrapper


@contextlib.contextmanager
def render_context(
    alpha_mode: george.AlphaSaveMode | None = None,
    background_mode: george.BackgroundMode | None = None,
    save_format: george.SaveFormat | None = None,
    format_opts: list[str] | None = None,
    layer_selection: list[Layer] | None = None,
) -> Generator[None, None, None]:
    """Context used to do renders in TVPaint.

    It does the following things:

    - Set the alpha mode and save format (with custom options)
    - Hide / Show the given layers (some render functions only render by visibility)
    - Restore the previous values after rendering

    Args:
        alpha_mode: the render alpha save mode
        save_format: the render format to use. Defaults to None.
        background_mode: the render background mode
        format_opts: the custom format options as strings. Defaults to None.
        layer_selection: the layers to render. Defaults to None.
    """
    # Save the current state
    pre_alpha_save_mode = george.tv_alpha_save_mode_get()
    pre_save_format, pre_save_args = george.tv_save_mode_get()
    pre_background_mode, pre_background_colors = george.tv_background_get()

    # Set the save mode values
    if alpha_mode:
        george.tv_alpha_save_mode_set(alpha_mode)
    if background_mode:
        george.tv_background_set(background_mode)
    if save_format:
        george.tv_save_mode_set(save_format, *(format_opts or []))

    layers_visibility = []
    if layer_selection:
        clip = layer_selection[0].clip
        layers_visibility = [(layer, layer.is_visible) for layer in clip.get_layers()]
        # Show and hide the clip layers to render
        for layer, _ in layers_visibility:
            should_be_visible = not layer_selection or layer in layer_selection
            layer.is_visible = should_be_visible

    # Do the rendering
    yield

    # Restore the previous values
    if alpha_mode:
        george.tv_alpha_save_mode_set(pre_alpha_save_mode)
    if save_format:
        george.tv_save_mode_set(pre_save_format, *pre_save_args)
    if background_mode:
        george.tv_background_set(pre_background_mode, pre_background_colors)

    # Restore the layer visibility
    if layers_visibility:
        for layer, was_visible in layers_visibility:
            layer.is_visible = was_visible


class HasCurrentFrame(Protocol):
    """Class that has a current frame property."""

    @property
    def current_frame(self) -> int:
        """The current frame, clip or project."""
        ...

    @current_frame.setter
    def current_frame(self, value: int) -> None: ...


@contextlib.contextmanager
def restore_current_frame(tvp_element: HasCurrentFrame, frame: int) -> Generator[None, None, None]:
    """Context that temporarily changes the current frame to the one provided and restores it when done.

    Args:
        tvp_element: clip to change
        frame: frame to set. Defaults to None.
    """
    previous_frame = tvp_element.current_frame

    if frame != previous_frame:
        tvp_element.current_frame = frame

    yield

    if tvp_element.current_frame != previous_frame:
        tvp_element.current_frame = previous_frame


@runtime_checkable
class _TVPElement(Protocol):
    @property
    def id(self) -> int | str: ...
    @property
    def name(self) -> str: ...


# We define a single TypeVar bound to the base protocol
TVPElementType = TypeVar("TVPElementType", bound=_TVPElement)


def get_tvp_element(
    tvp_elements: Iterator[TVPElementType],
    by_id: int | str | None = None,
    by_name: str | None = None,
    by_regex: re.Pattern[str] | None = None,
    by_path: str | Path | None = None,
) -> TVPElementType | None:
    """Search for a TVPaint element by attributes.

    Args:
        tvp_elements: a collection of TVPaint objects
        by_id: search by id. Defaults to None.
        by_name: search by name, search is case-insensitive. Defaults to None.
        by_regex: search by name using a compiled regex, case-sensitivity is left to the regex. Defaults to None.
        by_path: search by path. Defaults to None.

    Raises:
        ValueError: if none of the search arguments where provided

    Returns:
        _TVPElementType | None: the searched element or None if search was unsuccessful
    """
    values = (by_id, by_name, by_regex, by_path)
    if not any(v is not None for v in values):
        raise ValueError(f"At least one value ({' or '.join(str(v) for v in values)} must be provided")

    for element in tvp_elements:
        if by_id is not None and element.id != by_id:
            continue
        if by_name is not None and element.name.lower() != by_name.lower():
            continue
        if by_regex is not None and not by_regex.search(element.name):
            continue
        if by_path is not None and getattr(element, "path") != Path(by_path):
            continue
        return element

    return None


def handle_output_range(
    output_path: Path | str | FileSequence,
    default_start: int,
    default_end: int,
    start: int | None = None,
    end: int | None = None,
) -> tuple[FileSequence, int, int, bool, bool]:
    """Handle the different options for output paths and range.

    Whether the user provides a range (start-end) or a frame set or a filesequence with a range or not, this functions
    ensures we always end up with a valid range to render

    Args:
        output_path: user provided output path
        default_start: the default start to use if none provided or found in the file sequence object
        default_end: the default end to use if none provided or found in the file sequence object
        start: user provided start frame or None
        end: user provided end frame or None

    Returns:
        file_sequence: output path as a FileSequence object
        start: computed start frame
        end: computed end frame
        is_sequence: whether the output is a sequence or not
        is_image: whether the output is an image or not (a movie)
    """
    # we handle all outputs as a FileSequence, makes it a bit easier to handle ranges and padding
    if not isinstance(output_path, FileSequence):
        file_sequence = FileSequence(Path(output_path).as_posix())
    else:
        file_sequence = output_path

    frame_set = file_sequence.frameSet()
    is_image = george.SaveFormat.is_image(file_sequence.extension())

    # if the provided sequence has a range, and we don't, use the sequence range
    if frame_set and len(frame_set) >= 1 and is_image:
        frames = sorted(frame_set.items)
        start = start or int(frames[0])
        end = end or int(frames[-1])

    # check characteristics of file sequence
    fseq_has_range = frame_set and len(frame_set) > 1
    fseq_is_single_image = frame_set and len(frame_set) == 1
    fseq_no_range_padding = not frame_set and file_sequence.padding()
    range_is_seq = start is not None and end is not None and start != end
    range_is_single_image = start is not None and end is not None and start == end

    is_single_image = bool(is_image and (fseq_is_single_image or not frame_set) and range_is_single_image)
    is_sequence = bool(is_image and (fseq_has_range or fseq_no_range_padding or range_is_seq))

    # if no range provided, use clip mark in/out, if none, use clip start/end
    if start is None:
        start = default_start
    if is_single_image and not end:
        end = start
    else:
        if end is None:
            end = default_end

    frame_set = FrameSet(f"{start}-{end}")

    if not file_sequence.padding() and is_image and len(frame_set) > 1:
        file_sequence.setPadding("#")
        if not is_sequence and "#" not in str(file_sequence):
            is_sequence = True

    # we should have a range by now, set it in the sequence
    if (is_image and not is_single_image) or file_sequence.padding():
        file_sequence.setFrameSet(frame_set)

    return file_sequence, start, end, is_sequence, is_image
