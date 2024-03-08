from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import pytest
from pytvpaint.george.client.parse import (
    DataclassInstance,
    camel_to_pascal,
    tv_cast_to_type,
    tv_handle_string,
    tv_parse_dict,
    tv_parse_list,
)


@pytest.mark.parametrize(
    "string, expected",
    [
        ("StringWithoutSpaces", "StringWithoutSpaces"),
        ("with spaces", '"with spaces"'),
        (" ", '" "'),
    ],
)
def test_tv_handle_string(string: str, expected: str) -> None:
    assert tv_handle_string(string) == expected


@pytest.mark.parametrize(
    "string, expected",
    [
        ("a", "A"),
        ("this_is_a_function_name", "ThisIsAFunctionName"),
        ("FLUO_SH410_CL_v001.tvpp", "FluoSh410ClV001.tvpp"),
    ],
)
def test_camel_to_pascal(string: str, expected: str) -> None:
    assert camel_to_pascal(string) == expected


class EnumTest(Enum):
    A = "aa"
    B = "cc"
    C = "Cc"


@pytest.mark.parametrize(
    "value, cast, result",
    [
        ("hello", str, "hello"),
        ("1", bool, True),
        ("0", bool, False),
        ("ON", bool, True),
        ("on", bool, True),
        ("OFF", bool, False),
        ("/hello", Path, Path("/hello")),
        ("7382", int, 7382),
        ("7.3", float, 7.3),
        ("aa", EnumTest, EnumTest.A),
        ("cc", EnumTest, EnumTest.B),
        ("1", EnumTest, EnumTest.B),
        ('"aa"', EnumTest, EnumTest.A),
        ('"cc"', EnumTest, EnumTest.B),
        ("Cc", EnumTest, EnumTest.C),
        ("0.5 0.5", tuple[float, float], (0.5, 0.5)),
        ("hel 0.5 C:/test", tuple[str, float, Path], ("hel", 0.5, Path("C:/test"))),
    ],
)
def test_tv_cast_to_type(value: str, cast: Any, result: str) -> None:
    assert tv_cast_to_type(value, cast) == result


def test_tv_cast_to_enum_index_parse_error() -> None:
    with pytest.raises(ValueError, match="can't be parsed as int"):
        tv_cast_to_type("valfsg", EnumTest)


def test_tv_cast_to_enum_index_out_of_bounds() -> None:
    with pytest.raises(ValueError, match="out of bounds"):
        tv_cast_to_type("67", EnumTest)


@dataclass
class Person:
    name: str
    age: int


@dataclass
class Empty:
    pass


@dataclass
class Size:
    size: float


@dataclass
class Version:
    full_version: float


@dataclass
class MixedCase:
    lower: str
    camel: int


@dataclass
class SubString:
    size: int
    arg: int
    maxsize: str


class DrawingModeTest(Enum):
    COLOR = "color"
    BEH = "behind"
    ERR = "erase"


@dataclass
class TVPPenBrush:
    mode: DrawingModeTest
    size: float
    power: int
    opacity: int
    dry: bool
    aaliasing: bool
    gradient: bool
    csize: str
    cpower: str


@pytest.mark.parametrize(
    "dict_str, with_type, check_keys",
    [
        ("Name Paul Age 43", Person, {"name": "Paul", "age": 43}),
        ("Name MyName Age 43", Person, {"name": "MyName", "age": 43}),
        ("Name P a u l Age 43", Person, {"name": "P a u l", "age": 43}),
        ("Empty", Empty, {}),
        ("size 3.5", Size, {"size": 3.5}),
        ("full_version 2.43", Version, {}),
        (
            "lower myString camel -1",
            MixedCase,
            {"lower": "myString", "camel": -1},
        ),
        ("FullVersion 2.43", Version, {"full_version": 2.43}),
        (
            'size -23 arg 0 maxsize "hello   p"',
            SubString,
            {"size": -23, "arg": 0, "maxsize": "hello   p"},
        ),
        (
            'mode "color" size 3.000000 power 100 opacity 100 dry 0 aaliasing 1 gradient 0 csize "10;2 0 1 0 0 1 1 " cpower "0;2 0 1 0 0 1 1 "',
            TVPPenBrush,
            {
                "mode": DrawingModeTest.COLOR,
                "size": 3.0,
                "power": 100,
                "opacity": 100,
                "dry": False,
                "aaliasing": True,
                "gradient": False,
                "csize": "10;2 0 1 0 0 1 1 ",
                "cpower": "0;2 0 1 0 0 1 1 ",
            },
        ),
        ('lower "text" camel 4', MixedCase, {"lower": "text", "camel": 4}),
    ],
)
def test_tv_parse_dict(
    dict_str: str,
    with_type: type[DataclassInstance],
    check_keys: dict[str, Any],
) -> None:
    result_dict = tv_parse_dict(dict_str, with_fields=with_type)
    assert result_dict == check_keys


@dataclass
class Project:
    name: str
    id: int
    frame_rate: float
    path: Path


@dataclass
class Truth:
    true: bool
    false: bool


@pytest.mark.parametrize(
    "list_str, with_type, check_keys",
    [
        (
            "MyProject   ",
            Project,
            {
                "name": "MyProject",
            },
        ),
        (
            "MyProject 56783 4.555 c:/my/path",
            Project,
            {
                "name": "MyProject",
                "id": 56783,
                "frame_rate": 4.555,
                "path": Path("c:/my/path"),
            },
        ),
        ('"ON" 0', Truth, {"true": True, "false": False}),
        ("OFF 1", Truth, {"true": False, "false": True}),
    ],
)
def test_tv_parse_list(
    list_str: str,
    with_type: type[DataclassInstance],
    check_keys: dict[str, Any],
) -> None:
    result_dict = tv_parse_list(list_str, with_fields=with_type)
    assert result_dict == check_keys
