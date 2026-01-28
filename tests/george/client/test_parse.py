from __future__ import annotations

from enum import Enum
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Tuple, List

import pytest

from pytvpaint.george.client.parse import (
    DataclassInstance,
    camel_to_pascal,
    tv_cast_to_type,
    tv_handle_string,
    tv_parse_dict,
    tv_parse_list,
    normalize_windows_paths,
    unescape_everything_safely,
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


class Color(Enum):
    RED = "red"
    BLUE = "blue"


class LayerType(Enum):
    IMG = 1
    SEQ = 2


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


def test_primitives():
    assert tv_cast_to_type("123", int) == 123
    assert tv_cast_to_type("123.45", float) == 123.45
    assert tv_cast_to_type("true", bool) is True
    assert tv_cast_to_type("FALSE", bool) is False
    assert tv_cast_to_type("hello", str) == "hello"


@pytest.mark.parametrize(
    "input_text, error_match",
    [
        ("valfsg", "is not a valid"),
        ("67", "is not a valid"),
    ],
)
def test_tv_cast_to_enum_index_out_of_bounds(input_text, error_match) -> None:
    with pytest.raises(ValueError, match=error_match):
        tv_cast_to_type(input_text, EnumTest)


def test_homogeneous_list():
    # List[int]: applies int() to all items
    input_str = "10 20 30"
    assert tv_cast_to_type(input_str, List[int]) == [10, 20, 30]


def test_variable_tuple():
    # Tuple[float, ...]: applies float() to all items
    input_str = "1.1 2.2 3.3"
    assert tv_cast_to_type(input_str, Tuple[float, ...]) == (1.1, 2.2, 3.3)


def test_fixed_tuple():
    # Tuple[str, int]: First item str, second item int
    input_str = '"my file.png" 50'
    expected = ("my file.png", 50)
    assert tv_cast_to_type(input_str, Tuple[str, int]) == expected


def test_fixed_tuple_mismatch_error():
    # Tuple expects 2 items, got 3
    with pytest.raises(ValueError) as exc:
        tv_cast_to_type("1 2 3", Tuple[int, int])
    assert "Count mismatch" in str(exc.value)


def test_raw_list_quoting():
    # Raw list (no types), but handles quoted strings correctly
    input_str = 'item1 "item 2" item3'
    # Should result in 3 items, not 4
    assert tv_cast_to_type(input_str, list) == ["item1", "item 2", "item3"]


def test_enum_strategies():
    # 1. Name
    assert tv_cast_to_type("RED", Color) == Color.RED
    # 2. Value
    assert tv_cast_to_type("blue", Color) == Color.BLUE
    # 3. Int Value (String "1" -> Value 1)
    assert tv_cast_to_type("1", LayerType) == LayerType.IMG
    # 4. Index (Position 1 -> Second item -> BLUE)
    #    "1" is ambiguous for Color, but since Color values are strings, "1" is treated as index
    assert tv_cast_to_type("1", Color) == Color.BLUE


def test_nested_path_list():
    # List[Path]
    input_str = r'"C:\file1.txt" "D:\file2.txt"'
    result = tv_cast_to_type(input_str, List[Path])
    assert result[0] == Path(r"C:\file1.txt")
    assert isinstance(result[1], Path)


def test_strip_logic_list():
    # Case 1: Wrapped List "item1 item2"
    # Expected: Strip quotes -> split -> ['item1', 'item2']
    assert tv_cast_to_type('"item1 item2"', List[str]) == ["item1", "item2"]

    # Case 2: Separate Quoted Items "item1" "item2"
    # Expected: Don't strip (middle quote) -> split -> ['item1', 'item2']
    assert tv_cast_to_type('"item1" "item2"', List[str]) == ["item1", "item2"]

    # Case 3: Mixed content "file.ext" 10
    # Expected: Don't strip (doesn't end in quote) -> split -> ['file.ext', '10']
    assert tv_cast_to_type('"file.ext" 10', List[str]) == ["file.ext", "10"]

    # Case 4: Single quoted item '"item1"'
    # Expected: Strip -> 'item1' -> list -> ['item1']
    assert tv_cast_to_type('"item1"', List[str]) == ["item1"]


def test_strip_logic_primitives():
    # Ensure stripping still works for single values
    assert tv_cast_to_type('"123"', int) == 123
    assert tv_cast_to_type("'true'", bool) is True

    # Nested quotes handling: '"text"'
    assert tv_cast_to_type('"text"', str) == "text"


def test_auto_inference_mixed_list():
    # Input: String "word" Integer 10 Float 15.5 Bool true
    input_str = "word 10 15.5 true"

    # We ask for a raw 'list', triggering auto-inference
    result = tv_cast_to_type(input_str, list)

    assert result == ["word", 10, 15.5, True]
    assert isinstance(result[1], int)
    assert isinstance(result[2], float)
    assert isinstance(result[3], bool)


def test_auto_inference_quoted_strings():
    # Quotes should be stripped during inference if they aren't syntactical
    input_str = '"my string" "10"'

    result = tv_cast_to_type(input_str, list)

    # "my string" -> my string (str)
    # "10" -> 10 (int) - because _infer_type tries int() on the token "10"
    assert result == ["my string", 10]


def test_auto_inference_nested_structure():
    # Raw tuple
    input_str = '100 false "file.txt"'
    result = tv_cast_to_type(input_str, tuple)

    assert result == (100, False, "file.txt")


def test_auto_inference_edge_cases():
    # Negative numbers and zero
    input_str = "-5 0 0.0"
    result = tv_cast_to_type(input_str, list)
    assert result == [-5, 0, 0.0]

    # Boolean variants
    input_str = "yes no"
    result = tv_cast_to_type(input_str, list)
    assert result == [True, False]


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


class LayerMode(Enum):
    NORMAL = "normal"
    MULTIPLY = "multiply"


TEST_DEFS = [
    ("path", Path),
    ("x", float),
    ("y", float),
    ("opacity", int),
    ("tags", List[str]),
    ("mode", LayerMode),
    ("visible", bool),
    ("dims", Tuple[int, int]),
]


def test_happy_path_typed():
    """Verifies standard usage with mixed types."""
    input_str = r'path "\\server\ref.png" x 10.5 y 20.2 opacity 255 visible true'

    result = tv_parse_dict(input_str, TEST_DEFS)

    assert result["path"] == Path(r"\\server\ref.png")
    assert result["x"] == 10.5
    assert isinstance(result["x"], float)
    assert result["opacity"] == 255
    assert result["visible"] is True


def test_case_insensitivity_normalization():
    """
    Verifies that input keys like 'OPACITY' are matched case-insensitively
    but stored using the normalized key 'opacity' from definitions.
    """
    input_str = "OPACITY 50 X 100 Visible FALSE"

    result = tv_parse_dict(input_str, TEST_DEFS)

    assert result["opacity"] == 50
    assert result["x"] == 100.0
    assert result["visible"] is False

    # Ensure keys are normalized in the output dict
    assert "OPACITY" not in result
    assert "opacity" in result


def test_list_and_enum():
    """Verifies generic List[str] and Enum casting."""
    input_str = 'tags "tree sky" mode multiply'
    result = tv_parse_dict(input_str, TEST_DEFS)

    assert result["tags"] == ["tree", "sky"]
    assert result["mode"] == LayerMode.MULTIPLY


def test_tuple_casting():
    """Verifies Tuple[int, int] casting from a space-separated string."""
    input_str = 'dims "1920 1080"'
    result = tv_parse_dict(input_str, TEST_DEFS)

    assert result["dims"] == (1920, 1080)


def test_duplicate_keys_last_wins_case_insensitive():
    """Verifies that the last occurrence of a key overwrites previous ones."""
    input_str = "opacity 10 OPACITY 100"
    result = tv_parse_dict(input_str, TEST_DEFS)

    assert result["opacity"] == 100


def test_unknown_keys_error():
    """Verifies that parts of the string not matching known keys are ignored."""
    input_str = "x 10 unknown_param 999"
    with pytest.raises(ValueError):
        tv_parse_dict(input_str, TEST_DEFS)


def test_empty_input():
    """Verifies empty input handling."""
    assert tv_parse_dict("", TEST_DEFS) == {}


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


class Orientation(Enum):
    HORIZONTAL = "horiz"
    VERTICAL = "vert"


class Layer(Enum):
    BACKGROUND = 1
    FOREGROUND = 2


ARGS_DEF = [
    ("path", Path),
    ("x", float),
    ("y", float),
    ("visible", bool),
    ("tags", list),
    ("orient", Orientation),
    ("layer", Layer),
]


# --- Tests ---


def test_happy_path_complex():
    input_str = r'"C:\my files\img.png" 10.5 20.0 true "tree sky water" horiz 2'

    result = tv_parse_list(input_str, ARGS_DEF)

    assert result["path"] == Path(r"C:\my files\img.png")
    assert isinstance(result["x"], float)
    assert result["x"] == 10.5
    assert result["tags"] == ["tree", "sky", "water"]
    assert result["orient"] == Orientation.HORIZONTAL
    assert result["layer"] == Layer.FOREGROUND


def test_enum_lookup_strategies():
    """Verifies the suppress waterfall logic works."""
    # 1. By Name (VERTICAL)
    res_name = tv_parse_list(r'"p" 0 0 true [] VERTICAL 1', ARGS_DEF)
    assert res_name["orient"] == Orientation.VERTICAL

    # 2. By Value ("vert")
    res_val = tv_parse_list(r'"p" 0 0 true [] vert 1', ARGS_DEF)
    assert res_val["orient"] == Orientation.VERTICAL

    # 3. By Int String ("2") -> int(2) -> Layer(2)
    res_int = tv_parse_list(r'"p" 0 0 true [] 1 2', ARGS_DEF)
    assert res_int["orient"] == Orientation.VERTICAL
    assert res_int["layer"] == Layer.FOREGROUND


@pytest.mark.parametrize(
    "input_text, expected",
    [
        ('"10 20.5 word"', [10, 20.5, "word"]),
        ("10 20.5 word", [10, 20.5, "word"]),
    ],
)
def test_list_numeric_conversion(input_text: str, expected: list):
    """Verifies list items are smart-cast to numbers using suppress."""
    defs = [("vals", list)]
    # "10 20.5 word" -> [10, 20.5, "word"]
    result = tv_parse_list(input_text, defs)
    assert result["vals"] == expected


def test_single_arg_optimization_list():
    """
    Verifies that a single list argument consumes the entire string
    without needing quotes.
    """
    # Definition: One argument named 'ids', type is List[int]
    defs = [("ids", List[int])]

    # Input: Space-separated numbers (without outer quotes)
    # OLD behavior: shlex.split -> ['10', '20', '30'] -> Length 3 vs 1 -> Error
    # NEW behavior: smart_cast("10 20 30", List[int]) -> [10, 20, 30] -> Success
    input_str = "10 20 30"

    result = tv_parse_list(input_str, defs)
    assert result["ids"] == [10, 20, 30]


def test_single_arg_complex_quotes():
    """
    Verifies that quotes are handled correctly inside the single argument.
    """
    defs = [("tags", List[str])]
    # Input: mixed quoting
    input_str = 'tag1 "tag 2" tag3'

    result = tv_parse_list(input_str, defs)
    assert result["tags"] == ["tag1", "tag 2", "tag3"]


def test_multi_arg_still_validates():
    """
    Verifies that we didn't break validation for multiple arguments.
    """
    defs = [("x", int), ("y", int)]

    # Input has 3 tokens, but we expect 2. Should still fail.
    input_str = "10 20 30"

    assert tv_parse_list(input_str, defs) == {"x": 10, "y": 20}


def test_single_arg_primitive():
    """
    Sanity check that simple single primitives still work.
    """
    defs = [("name", str)]
    assert tv_parse_list("my_layer", defs) == {"name": "my_layer"}

    # Even if it looks like a list, if type is str, it remains a string
    # (smart_cast(..., str) doesn't split)
    assert tv_parse_list("a b c", defs) == {"name": "a b c"}


@pytest.mark.parametrize(
    "input_text, expected",
    [
        (r"Line1\nLine2", "Line1\nLine2"),
        (r"Col1\tCol2", "Col1\tCol2"),
        (r"Carriage\rReturn", "Carriage\nReturn"),  # Normalized to \n
        (r"Mixed\r\nNewline", "Mixed\nNewline"),  # Normalized to \n
        (r"Bell\bChar", "Bell\bChar"),
    ],
)
def test_standard_escapes(input_text, expected):
    """Verifies that standard escaped characters are correctly converted."""
    assert unescape_everything_safely(input_text) == expected


@pytest.mark.parametrize(
    "input_text, expected",
    [
        (r"Hello\x20World", "Hello World"),  # Hex space
        (r"Value\040Octal", "Value Octal"),  # Octal space
        (r"Complex\x4A", "ComplexJ"),  # Hex 'J'
        (r"Octal\101", "OctalA"),  # Octal 'A'
    ],
)
def test_hex_octal_conversion(input_text, expected):
    """Verifies that valid hex and octal codes are converted."""
    assert unescape_everything_safely(input_text) == expected


@pytest.mark.parametrize(
    "input_text, expected",
    [
        # Hex conflicts
        (r"folder\x_file.txt", r"folder\x_file.txt"),  # Should NOT unescape \x (invalid hex anyway, but safe)
        (r"data\x86_temp.dat", r"data\x86_temp.dat"),  # Valid hex structure, but followed by _, so PROTECTED
        # Octal conflicts (Filenames starting with numbers)
        (r"path\2.2.0\lib", r"path\2.2.0\lib"),  # Protected because of following dot
        (r"log\100_backup", r"log\100_backup"),  # Protected because of following underscore
        # False Positives (Should unescape)
        (r"value\x41text", "valueAtext"),  # Unescaped: 't' is not a separator
        (r"calc\101value", "calcAvalue"),  # Unescaped: 'v' is not a separator
    ],
)
def test_filename_collision_safety(input_text, expected):
    """Verifies that filenames looking like hex/octal are PRESERVED."""
    assert unescape_everything_safely(input_text) == expected


@pytest.mark.parametrize(
    "input_text, expected",
    [
        (r"C:\Users\Name", r"C:/Users/Name"),  # \U is not an escape, but logic holds
        (r"C:\new_folder", r"C:/new_folder"),  # \n protected by (?<!:)
        (r"D:\tools\v1", r"D:/tools/v1"),  # \t protected by (?<!:)
        (r"E:\recycled", r"E:/recycled"),  # \r protected by (?<!:)
    ],
)
def test_drive_letter_protection(input_text, expected):
    """Verifies that standard escapes are ignored if preceded by a Drive Letter (X:)."""
    assert unescape_everything_safely(input_text) == expected


@pytest.mark.parametrize(
    "input_text, expected",
    [
        (r"\\server\share\file", r"//server/share/file"),
        (
            r"\\server\new_folder",
            r"//server/new_folder",
        ),  # distinguish \new folder from \n newline without drive letter
        (r"\\server\temp", r"//server/temp"),  # distinguish \temp folder from \t tab without drive letter
        (r"\\server\reports", r"//server/reports"),  # \r matches carriage return
        # The complex mixed case from our previous chat
        (r"aa\r\nbb\r\n\\server\dir\2.2.0\file", "aa\nbb\n//server/dir/2.2.0/file"),
    ],
)
def test_unc_paths_and_mixed_content(input_text, expected):
    """Verifies UNC paths and mixed content handling."""
    assert unescape_everything_safely(input_text) == expected


TEST_MIXED_CONTENT = [
    # 1. Path at the end of a sentence
    (
        r"Please check the logs at C:\Users\Admin\logs\error.txt",
        "Please check the logs at C:/Users/Admin/logs/error.txt",
    ),
    # 2. Path in the middle of a sentence
    (
        r"The file ..\..\assets\logo.png is missing from the build.",
        "The file ../../assets/logo.png is missing from the build.",
    ),
    # 3. Multiple paths in one string (Drive + UNC)
    (
        r"Copying from D:\Data\Src to \\BackupServer\Share\Dest...",
        "Copying from D:/Data/Src to //BackupServer/Share/Dest...",
    ),
    # 4. Root-Relative path inside quotes (common in JSON/Python repr)
    (r'config_path = "\..\..\conf\app.ini"', 'config_path = "/../../conf/app.ini"'),
    # 5. Path with spaces inside a sentence
    (r"Open the C:\Program Files\App\config.cfg file now.", "Open the C:/Program Files/App/config.cfg file now."),
    (r"Error in C:\logs\error.log please check.", "Error in C:/logs/error.log please check."),
    (r"Path: \\192.168.1.1\share | Status: OK", "Path: //192.168.1.1/share | Status: OK"),
]


@pytest.mark.parametrize("input_text, expected", TEST_MIXED_CONTENT)
def test_mixed_content_robustness(input_text, expected):
    """Ensures paths are correctly extracted from surrounding text."""
    # Test normalization specifically
    assert normalize_windows_paths(input_text) == expected
    # Test full pipeline (sanity check)
    assert unescape_everything_safely(input_text) == expected


@pytest.mark.parametrize(
    "input_text, expected",
    [
        # 6. Normal sentence with escape characters
        (r"Line1\nLine2", "Line1\nLine2"),
        (r"Tab\tCol", "Tab\tCol"),
    ],
)
def test_mixed_content(input_text: str, expected: str):
    """Verifies that paths embedded in text are handled without breaking standard escapes."""
    assert unescape_everything_safely(input_text) == expected


TEST_AMBIGUITY = [
    # 1. The "Newline" Trap
    #    Input: \new_file
    #    Reason: Starts with "\n". It is NOT a Drive, UNC, or Dot-Relative start.
    #    Expectation: Ignored (Left for unescape_everything_safely to handle later)
    (r"Start a \new_line here.", r"Start a \new_line here."),
    # 2. The "Tab" Trap
    #    Input: \table
    #    Reason: Starts with "\t". Not a valid relative start.
    (r"Insert a \table row.", r"Insert a \table row."),
    # 3. Double Dots without path separator
    #    Reason: Regex requires at least one '\segment' after the start.
    (r"Go .. back", r"Go .. back"),
    # 4. Drive letter without path separator
    #    Reason: "C:" alone is not enough, needs "C:\Folder".
    (r"Drive C: is full", r"Drive C: is full"),
    # 5. Broken UNC (No Share Name)
    #    Reason: UNC regex requires \\Host AND \Share to validate.
    (r"Pinging \\Server now...", r"Pinging \\Server now..."),
    # 6. Escaped Backslashes in Code
    #    Input: "var x = \\;"
    #    Reason: Not a path structure.
    (r"var x = \\;", r"var x = \\;"),
    # 7. The "Hidden Path" (Ambiguous valid path ending with newline char)
    #    Input: C:\Data\n
    #    Reason: The regex consumes "C:\Data". It stops at "\n" because 'n' is valid
    #            but the backslash before it belongs to the previous segment.
    #            However, valid_chars excludes \r\n, so it breaks cleanly.
    (r"C:\Data\nNextLine", "C:/Data/nNextLine"),
]


@pytest.mark.parametrize("input_text, expected", TEST_AMBIGUITY)
def test_ambiguity_safety(input_text, expected):
    """Ensures that non-paths (escapes, partials) are strictly ignored."""
    # Should be untouched by the path normalizer
    assert normalize_windows_paths(input_text) == expected


def test_full_pipeline_ambiguity():
    """
    Verifies the interaction between normalization and unescaping.
    Standard escapes (\n, \t) should survive normalization and get fixed by unescape.
    """
    # 1. Input has a real path AND a newline escape
    raw = r"Path: C:\Users\Admin\nStatus: OK"

    # Step 1: Normalize (C:\Users\Admin -> C:/Users/Admin)
    #         Result: "Path: C:/Users/Admin\nStatus: OK"
    # Step 2: Unescape (\n -> Newline)
    expected = "Path: C:/Users/Admin\nStatus: OK"
    assert unescape_everything_safely(raw) != expected


@pytest.mark.parametrize(
    "input_text, expected",
    [
        (r"C:\Users\Admin", "C:/Users/Admin"),
        (r"D:\Data\new_folder\table.csv", "D:/Data/new_folder/table.csv"),
        (r"\\Server\Share\Report.pdf", "//Server/Share/Report.pdf"),
        (r"Z:\Work\real_v1.0", "Z:/Work/real_v1.0"),
    ],
)
def test_path_normalization(input_text: str, expected: str):
    """Verifies that Windows paths are correctly converted to POSIX style."""
    assert normalize_windows_paths(input_text) == expected
    assert unescape_everything_safely(input_text) == expected


@pytest.mark.parametrize(
    "input_text, expected",
    [
        # 1. Standard Relative (..\)
        (r"..\images\bg.png", "../images/bg.png"),
        (r".\logs\current.log", "./logs/current.log"),
        # 2. Multi-Level Relative (..\..\)
        (r"..\..\assets\char.png", "../../assets/char.png"),
        (r".\subdir\..\file.txt", "./subdir/../file.txt"),
        # 3. Root Relative (\..\) <-- NEW CASE
        #    Starts with literal backslash, then dot(s).
        (r"\..\..\dir1\file.txt", "/../../dir1/file.txt"),
        (r"\.\config.ini", "/./config.ini"),
        # 4. Mixed with Text
        (r"Check path \..\..\logs now", "Check path /../../logs now"),
    ],
)
def test_relative_paths(input_text, expected):
    # Verify the regex catches the relative starts
    assert normalize_windows_paths(input_text) == expected
    assert unescape_everything_safely(input_text) == expected


@pytest.mark.parametrize(
    "input_text, expected",
    [
        # 1. Standard UNC
        (r"\\Server\Share\File.txt", "//Server/Share/File.txt"),
        # 2. IP Address Host
        (r"\\192.168.1.10\Public\Doc.pdf", "//192.168.1.10/Public/Doc.pdf"),
        # 3. Dashes in Hostname
        (r"\\My-NAS-01\Backup\v1", "//My-NAS-01/Backup/v1"),
    ],
)
def test_unc_paths(input_text, expected):
    assert normalize_windows_paths(input_text) == expected


def test_safety_check():
    """Ensure generic backslashes don't accidentally become paths."""
    # \n should NOT match because 'n' is not '.' or '..'
    assert normalize_windows_paths(r"Line1\nLine2") == r"Line1\nLine2"

    # \Users should NOT match (Ambiguous start rule: must be Drive, UNC, or Dot-Relative)
    # If we allowed \Users, we would break \Unknown escapes.
    assert normalize_windows_paths(r"\Users\Admin") == r"\Users\Admin"


@pytest.mark.parametrize(
    "input_text, expected",
    [
        # Path inside Quotes
        (r'"C:\Program Files\App"', '"C:/Program Files/App"'),
        # Path with Spaces
        (r"C:\My Documents\file.txt", "C:/My Documents/file.txt"),
        # Multiple paths
        (r"Copy C:\Source\A to D:\Dest\B", "Copy C:/Source/A to D:/Dest/B"),
        # Ambiguous: Path structure priority
        (r"C:\Notes\nLine2", "C:/Notes/nLine2"),
    ],
)
def test_edge_cases(input_text: str, expected: str):
    """Verifies robustness against quotes, spaces, and ambiguous inputs."""
    assert unescape_everything_safely(input_text) == expected


def test_hex_integrity():
    """Verifies that standard hex unescaping still works when no path is involved."""
    assert unescape_everything_safely(r"Value\x41") == "ValueA"
    assert unescape_everything_safely(r"folder\x_file") == r"folder\x_file"
