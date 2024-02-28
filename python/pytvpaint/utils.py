from __future__ import annotations

import contextlib
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generator,
    Iterable,
    Iterator,
    ParamSpec,
    TypeVar,
)

from typing_extensions import Protocol, Self

from pytvpaint import george
from pytvpaint.george.exceptions import GeorgeError

if TYPE_CHECKING:
    from pytvpaint.layer import Layer


class CanRefresh(Protocol):
    def refresh(self) -> None:
        ...


if TYPE_CHECKING:
    refreshed_property = property
else:

    class RefreshedProperty(property):
        def __get__(self, __obj: CanRefresh, __type: type | None = None) -> Any:
            __obj.refresh()
            return super().__get__(__obj, __type)

    refreshed_property = RefreshedProperty


class Refreshable(ABC):
    def __init__(self) -> None:
        self.refresh_on_call = True

    @abstractmethod
    def refresh(self) -> None:
        raise NotImplementedError("Function refresh() needs to be implemented")


class Removable(Refreshable):
    def __init__(self) -> None:
        super().__init__()
        self._is_removed: bool = False

    def __getattribute__(self, name: str) -> Any:
        if not name.startswith("_") and self._is_removed:
            raise ValueError(f"{self.__class__.__name__} has been removed!")

        return super().__getattribute__(name)

    def refresh(self) -> None:
        if self._is_removed:
            raise ValueError(f"{self.__class__.__name__} has been removed!")

    @property
    def is_removed(self) -> bool:
        self._is_removed = False
        with contextlib.suppress(Exception):
            self.refresh()
            self._is_removed = True
        return self._is_removed

    @abstractmethod
    def remove(self) -> None:
        raise NotImplementedError("Function refresh() needs to be implemented")

    def mark_removed(self) -> None:
        """Marks the object as removed and is therefor not usable"""
        self._is_removed = True


class HasName(Protocol):
    @property
    def name(self) -> str:
        ...


def get_unique_name(names: Iterable[str], stub: str) -> str:
    """
    Get a unique name with a list of names and auto increment it
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
    """Utility generator that yields the result of a function according to a position

    Yields:
        Iterator[tuple[int, T]]: the position and the result of the function
    """
    pos = 0

    while True:
        try:
            yield fn(pos)
        except stop_when:
            break
        pos += 1


class CanMakeCurrent(Protocol):
    @property
    def id(self) -> str | int:
        ...

    def make_current(self) -> None:
        ...


# See: https://stackoverflow.com/questions/47060133/python-3-type-hinting-for-decorator
Param = ParamSpec("Param")
ReturnType = TypeVar("ReturnType")


def set_as_current(func: Callable[..., ReturnType]) -> Callable[..., ReturnType]:
    """
    Set the current TVPaint object as 'current'.
    Useful when George functions only apply on the current project, clip, layer or scene
    """

    def wrapper(self: CanMakeCurrent, *args: Any, **kwargs: Any) -> ReturnType:
        self.make_current()
        return func(self, *args, **kwargs)

    return wrapper


@contextlib.contextmanager
def render_context(
    alpha_mode: george.AlphaSaveMode,
    save_format: george.SaveFormat | None = None,
    format_opts: list[str] | None = None,
    layers_to_render: list[Layer] | None = None,
) -> Generator[None, None, None]:
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
    if layers_to_render:
        layers_visibility = [(layer, layer.is_visible) for layer in clip.layers]
        # Show and hide the clip layers to render
        for layer, _ in layers_visibility:
            should_be_visible = layers_to_render is None or layer in layers_to_render
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


class TVPElement(Protocol):
    @property
    def id(self) -> int | str:
        ...

    @property
    def name(self) -> str:
        ...


TVPElementType = TypeVar("TVPElementType", bound=TVPElement)


def get_tvp_element(
    tvp_elements: Iterator[TVPElementType],
    by_id: int | str | None = None,
    by_name: str | None = None,
    by_path: str | Path | None = None,
) -> TVPElementType | None:
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
