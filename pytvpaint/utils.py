"""Utility functions and classes which are not specific to anything else in the codebase."""

from __future__ import annotations

import contextlib
import re
from abc import ABC, abstractmethod
from collections.abc import Generator, Iterable, Iterator
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    TypeVar,
    cast,
)

from typing_extensions import ParamSpec, Protocol

from pytvpaint import george
from pytvpaint.george.exceptions import GeorgeError

if TYPE_CHECKING:
    from pytvpaint.layer import Layer


class _CanRefresh(Protocol):
    def refresh(self) -> None:
        ...


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
            bool: wether if it was removed or not
        """
        self._is_removed = False
        with contextlib.suppress(Exception):
            self.refresh()
            self._is_removed = True
        return self._is_removed

    @abstractmethod
    def remove(self) -> None:
        """Removes the object in TVPaint."""
        raise NotImplementedError("Function refresh() needs to be implemented")

    def mark_removed(self) -> None:
        """Marks the object as removed and is therefor not usable."""
        self._is_removed = True


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
        Iterator[T]: an generator of the resulting values
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
    alpha_mode: george.AlphaSaveMode,
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
        format_opts: the custom format options as strings. Defaults to None.
        layer_selection: the layers to render. Defaults to None.
    """
    from pytvpaint.clip import Clip

    # Save the current state
    pre_alpha_save_mode = george.tv_alpha_save_mode_get()
    pre_save_format, pre_save_args = george.tv_save_mode_get()

    # Set the save mode values
    if save_format:
        george.tv_save_mode_set(save_format, *(format_opts or []))

    george.tv_alpha_save_mode_set(alpha_mode)

    clip = Clip.current_clip()

    layers_visibility = []
    if layer_selection:
        layers_visibility = [(layer, layer.is_visible) for layer in clip.layers]
        # Show and hide the clip layers to render
        for layer, _ in layers_visibility:
            should_be_visible = not layer_selection or layer in layer_selection
            layer.is_visible = should_be_visible

    # Do the render
    yield

    # Restore the previous values
    if save_format:
        george.tv_alpha_save_mode_set(pre_alpha_save_mode)

    george.tv_save_mode_set(pre_save_format, *pre_save_args)

    # Restore the layer visibility
    if layers_visibility:
        for layer, was_visible in layers_visibility:
            layer.is_visible = was_visible


class _TVPElement(Protocol):
    @property
    def id(self) -> int | str:
        ...

    @property
    def name(self) -> str:
        ...


TVPElementType = TypeVar("TVPElementType", bound=_TVPElement)


def get_tvp_element(
    tvp_elements: Iterator[TVPElementType],
    by_id: int | str | None = None,
    by_name: str | None = None,
    by_path: str | Path | None = None,
) -> TVPElementType | None:
    """Search for a TVPaint element by attributes.

    Args:
        tvp_elements: a collection of TVPaint objects
        by_id: search by id. Defaults to None.
        by_name: search by name, search is case-insensitive. Defaults to None.
        by_path: search by path. Defaults to None.

    Raises:
        ValueError: if bad arguments were given

    Returns:
        TVPElementType | None: the found element
    """
    if by_id is None and by_name is None:
        raise ValueError(
            "At least one of the values (id or name) must be provided, none found !"
        )

    for element in tvp_elements:
        if by_id is not None and element.id != by_id:
            continue
        if by_name is not None and element.name.lower() != by_name.lower():
            continue
        if by_path is not None and getattr(element, "path") != Path(by_path):
            continue
        return element

    return None
