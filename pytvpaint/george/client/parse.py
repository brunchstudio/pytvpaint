"""Parsing functions used to handle data coming from TVPaint and also preparing arguments for them to be sent.

The two main functions are `tv_parse_dict` and `tv_parse_list` which handle the return values of George functions.

George can either return a list of values or a list of key/value pairs which are consecutive.
"""

from __future__ import annotations

import re
import shlex
from collections.abc import MutableSequence, Sequence
from contextlib import suppress
from dataclasses import Field, fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    ClassVar,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from typing_extensions import Protocol, TypeAlias

T = TypeVar("T", bound=Any)
Value = Union[int, float, str, bool, None]
FieldTypes: TypeAlias = MutableSequence[tuple[Union[tuple[str, str], str], Any]]

TVP_DOUBLE_QUOTES_RE = re.compile(r'""(.*?)""', re.I)


class DataclassInstance(Protocol):
    """Protocol that describes a Dataclass instance."""

    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]


def tv_handle_string(s: str) -> str:
    """String handling for George arguments. It wraps the string into quotes if it has spaces.

    See an example here: https://www.tvpaint.com/doc/tvpaint-animation-11/george-commands#tv_projectnew

    Args:
        s (str): the input string

    Returns:
        the "escaped" string
    """
    if " " in s:
        return f'"{s}"'

    return s


def camel_to_pascal(s: str) -> str:
    """Convert a camel case string to pascal case.

    Example:
        `this_is_a_text -> ThisIsAText`

    Args:
        s: the input string

    Returns:
        the string in pascal case
    """
    return "".join([c.capitalize() for c in s.split("_")])


def _strip_safe(text: str) -> str:
    """Removes surrounding quotes ONLY if they form a single matching pair wrapping the entire string.

    Examples:
        '"a b c"'      -> 'a b c'       (Stripped: wrapper)
        '"a" "b"'      -> '"a" "b"'      (Kept: multiple items)
        '"file" 10'    -> '"file" 10'    (Kept: doesn't end in quote)
    'normal text'  -> 'normal text' (Kept)
    """
    if len(text) < 2:
        return text

    first = text[0]
    # Must start and end with the same quote style
    if first not in ('"', "'") or text[-1] != first:
        return text

    # use regex to ensure the FIRST quoted segment covers the WHOLE string.
    # This ensures we don't match '"a" "b"' as a single block.
    escaped_body = r"(?:[^\\" + first + r"]|\\.)*"
    pattern = re.compile(rf"^{first}({escaped_body}){first}$")

    match = pattern.match(text)
    if match:
        # Return the inner content (preserving internal escapes like \")
        return str(match.group(1))

    return text


def _guess_type(token: str) -> Any:
    """Guess the type of the string token (int, float, bool, string). Used when no specific type hint is provided."""
    # Try Integer (Strict, so 10.5 doesn't become 10)
    try:
        return int(token)
    except ValueError:
        pass

    # Try float
    try:
        return float(token)
    except ValueError:
        pass

    # Try Boolean
    lower_val = token.lower()
    if lower_val in ("true", "yes", "on"):
        return True
    if lower_val in ("false", "no", "off"):
        return False

    return token.strip("\"'")  # remove internal quotes if shlex didn't


def tv_cast_to_type(value: str, cast_type: type[T]) -> T:  # noqa: C901
    """Casts a string value to a specific Python type, supporting:
    - Primitives (int, float, bool, str)
    - Path objects
    - Enums (by name, value, index)
    - Collections (List[T], Tuple[T, ...], Tuple[A, B])
    """  # noqa: D205, D415
    # strip outer quotes to expose list content (e.g. "a b")
    #  BUT leave as is if it's a complex string (e.g. "a" "b")
    clean_val = _strip_safe(value.strip())
    origin_type = get_origin(cast_type)

    # check if Collections (List[T], Tuple[...])
    if cast_type in (list, tuple) or origin_type in (list, tuple):
        # Determine the base container type (list or tuple)
        container_cls = origin_type or cast_type

        # Tokenize the string (handling quotes: "1 '2 3' 4")
        try:
            tokens = shlex.split(clean_val, posix=False)
        except ValueError:
            tokens = clean_val.split()  # Fallback
        tokens = [t.strip("\"'") for t in tokens]

        # Get inner type arguments (e.g. [int] from List[int])
        type_args = get_args(cast_type)
        casted_items = []

        # Case A: Homogeneous (List[int] or Tuple[int, ...])
        # If args exist and (it's a list OR it's a tuple with Ellipsis)
        if type_args and (container_cls is list or (len(type_args) == 2 and type_args[1] is ...)):
            item_type = type_args[0]
            for token in tokens:
                casted_items.append(tv_cast_to_type(token, item_type))  # noqa: PERF401

        # Case B: Fixed-Size Tuple (Tuple[str, int])
        elif container_cls is tuple and type_args:
            if len(tokens) != len(type_args):
                raise ValueError(
                    f"Count mismatch for {cast_type}: expected {len(type_args)}, got {len(tokens)} ('{clean_val}')"
                )
            for token, sub_type in zip(tokens, type_args):
                casted_items.append(tv_cast_to_type(token, sub_type))

        # Case C: Raw Collection (list, tuple) - Infer or keep strings
        else:
            for token in tokens:
                # Recursive call with 'str' keeps it simple, or add auto-inference logic here
                casted_items.append(_guess_type(token))  # noqa: PERF401

        return cast(T, container_cls(casted_items))

    clean_val = clean_val.strip("\"'")
    # Basic Primitives
    if isinstance(cast_type, str):
        return clean_val
    if isinstance(cast_type, int):
        return int(float(clean_val))
    if isinstance(cast_type, float):
        return float(clean_val)
    if isinstance(cast_type, Path):
        return Path(clean_val)
    if isinstance(cast_type, bool):
        return clean_val.lower() in ("true", "1", "yes", "on")

    # Enums
    if isinstance(cast_type, type) and issubclass(cast_type, Enum):
        # By Name
        with suppress(KeyError):
            return cast_type[clean_val]
        with suppress(KeyError):
            return cast_type[clean_val.lower()]
        # By value
        with suppress(ValueError):
            return cast_type(clean_val)
        with suppress(ValueError):
            return cast_type(clean_val.lower())

        # Exhaustive case-insensitive search for names and string values
        clean_lower = clean_val.lower()
        for member in cast_type:
            if member.name.lower() == clean_lower:
                return member
            if isinstance(member.value, str) and member.value.lower() == clean_lower:
                return member

        # By int value (for "1" -> 1)
        with suppress(ValueError):
            return cast_type(int(float(clean_val)))
        # By Index (Position in definition)
        if clean_val.isdigit():
            with suppress(IndexError):
                return list(cast_type)[int(clean_val)]

        raise ValueError(f"'{clean_val}' is not a valid {cast_type.__name__}")

    return cast(T, cast_type(clean_val))


def get_dataclass_fields(datacls: DataclassInstance | type[DataclassInstance], alt_names: bool = False) -> FieldTypes:
    """Get the dataclass key/type pairs and filter those with the "parsed" metadata.

    Args:
        datacls: input dataclass
        alt_names: get alt names, if no alt_name field name will be used

    Returns:
        the list of key/type tuple
    """
    with_fields: FieldTypes = []
    type_hints = get_type_hints(datacls)

    for f in fields(datacls):
        if not f.metadata.get("parsed", True):
            continue

        if not alt_names:
            with_fields.append((f.name, type_hints[f.name]))
            continue

        alt_name = f.metadata.get("alt_name", f.name)
        with_fields.append(((f.name, alt_name), type_hints[f.name]))

    return with_fields


def tv_parse_list(
    text: str,
    with_fields: FieldTypes | type[DataclassInstance],
    unused_indices: list[int] | None = None,
) -> dict[str, Any]:
    """Parses a positional string into typed arguments.

    Args:
        text: The raw input string.
        with_fields: A list of tuples [('name', Type), ...].
        unused_indices: Some George functions return positional arguments that are unused. Defaults to None.

    Returns:
        a dict with the provided fields and the values cast to the given types
    """
    if is_dataclass(with_fields):
        with_fields = get_dataclass_fields(with_fields, alt_names=False)

    if len(with_fields) == 1:
        name_entry, type_cls = with_fields[0]
        name = name_entry[0] if isinstance(name_entry, tuple) else name_entry
        return {name: tv_cast_to_type(text, type_cls)}

    text = TVP_DOUBLE_QUOTES_RE.sub(r'"\1"', text)
    try:
        tokens = shlex.split(text, posix=False)  # posix=False preserves Windows backslashes
    except ValueError as e:
        raise ValueError(f"Parsing error (unbalanced quotes?): {e}")

    if unused_indices:
        tokens = [t for i, t in enumerate(tokens) if i not in unused_indices]

    parsed_args: dict[str, Any] = {}
    for (field_name, type_cls), token in zip(with_fields, tokens):
        if isinstance(field_name, tuple):
            field_name, _ = field_name
        parsed_args[field_name] = tv_cast_to_type(token, type_cls)

    return parsed_args


def tv_parse_dict(text: str, with_fields: FieldTypes | type[DataclassInstance]) -> dict[str, T]:
    """Parse a list of values as key value pairs returned from TVPaint commands.

    Cast the values to a provided dataclass type or list of key/types pairs.

    Args:
        text: The input string (e.g. 'X 10 y 20 TAGS "a b"')
        with_fields: A list of tuples [('name', Type), ...].

    Returns:
        a dict with the provided fields and the values cast to the given types
    """
    if is_dataclass(with_fields):
        with_fields = get_dataclass_fields(with_fields, alt_names=True)

    normalized_map: dict[str, tuple[str, type[T]]] = {}
    for field_name, type_cls in with_fields:
        # handle different naming schemes
        alt_field_name = str(field_name)
        if isinstance(field_name, tuple):
            field_name, alt_field_name = field_name

        pascal_name = camel_to_pascal(alt_field_name).lower()
        normalized_map[pascal_name] = (field_name, type_cls)

    # Sort keys by length (descending) to prevent partial matching (ex: prevent 'x' from matching inside 'x_pos')
    sorted_keys = sorted(normalized_map.keys(), key=len, reverse=True)

    joined_keys = "|".join(map(re.escape, sorted_keys))  # use re.escape for keys with symbols
    pattern = re.compile(rf"({joined_keys})\s+(.*?)(?=\s+(?:{joined_keys})|$)", re.IGNORECASE)
    parsed_data = {}

    text = TVP_DOUBLE_QUOTES_RE.sub(r'"\1"', text)
    for match_key, match_val in pattern.findall(text):
        clean_val = match_val.strip()
        lookup = normalized_map.get(match_key.lower())

        if lookup:
            original_key, target_type = lookup
            parsed_data[original_key] = tv_cast_to_type(clean_val, target_type)

    return parsed_data


def args_dict_to_list(args: dict[str, Any]) -> list[Any]:
    """Converts a dict of named arguments to a flat list of key/values.

    It also filters pairs with None values

    Args:
        args: dict of arguments

    Returns:
        key/values list
    """
    args_filter = {k: v for k, v in args.items() if v is not None}
    return [item for kv in args_filter.items() for item in kv]


def validate_args_list(optional_args: Sequence[Value | tuple[Value, ...]]) -> list[Any]:
    """Validates *args equivalent for tvpaint.

    Some George functions only accept a list of values and not key:value pairs. If for instance, you need to set the
    last positional argument for a function call, you need to provide all the preceding arguments.
    This function, given a list of arguments or key:value pairs (as tuples) checks that they are valid/not None.

    For example, for `tv_camerainfo [<iWidth> <iHeight> [<field_order>]]`
    you can't pass `[500, None, "upper"]` because `<iHeight>` is not defined.

    Args:
        optional_args: list of values or tuple of values (args block)

    Raises:
        ValueError: if not all the parameters were given

    Returns:
        the list of parameters
    """
    args: list[Any] = []

    for arg in optional_args:
        if arg is None or (isinstance(arg, tuple) and all(a is None for a in arg)):
            break

        if isinstance(arg, tuple):
            if any(a is None for a in arg):
                raise ValueError(f"You must pass all the parameters: {arg}")
            args.extend(arg)
        else:
            args.append(arg)

    return args


def normalize_windows_paths(text: str) -> str:
    r"""Identifies Windows-style file paths and converts backslashes to forward slashes.

    Supports:
    1. Drive Roots:   C:\\Folder
    2. Relative:      .\\Folder or ..\\Folder
    3. Root Relative: \\.\\Folder or \\..\\Folder  <-- NEW
    4. UNC Paths:      \\\\Server\\Share\\File
    """
    # Valid characters for a filename (excludes forbidden chars and newlines)
    valid_chars = r'(?:(?!\s[a-zA-Z]:)[^\\/:*?"<>|\r\n])+'
    # A Path Segment is a backslash followed by valid chars: "\Folder"
    segment = rf"\\{valid_chars}"

    # Standard Starts
    #    Matches: "C:" OR "\.." OR ".." OR "\." OR "."
    #    Logic:
    #      [a-zA-Z]:      -> Drive Letter
    #      |
    #      \\\.\.?        -> Root Relative (\. or \..) - SAFE (Dot is not an escape)
    #      |
    #      \.\.?          -> Relative (. or ..)
    #
    #    use \.\.? (greedy) to match ".." before "."
    start_standard = r"(?:[a-zA-Z]:|\\\.\.?|\.\.?)"
    pattern_standard = rf"(?:{start_standard})(?:{segment})+"

    # UNC Start. Matches: "\\Server" (Backslash-Backslash-Hostname)
    start_unc = rf"\\\\{valid_chars}"
    pattern_unc = rf"(?:{start_unc})(?:{segment})+"

    full_pattern = rf"({pattern_standard}|{pattern_unc})"

    def _to_posix(match: re.Match[str]) -> str:
        return str(match.group(1)).replace("\\", "/")

    return re.sub(full_pattern, _to_posix, text)


def unescape_everything_safely(text: str) -> str:
    """Unescapes a raw/non-formatted tvpaint string while trying to preserve Windows file paths and filenames.

    Args:
        text: raw string.

    Returns:
        str: unescaped string.
    """
    text = normalize_windows_paths(text)
    pattern = r"\\([rntbfva]|x[0-9a-fA-F]{2}|[0-7]{1,3})"
    simple_escapes = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v", "a": "\a"}

    def _replace_match(match: re.Match[str]) -> str:
        code = match.group(1)

        if code in simple_escapes:
            return simple_escapes[code]

        # Hex/Octal check
        full_match = match.group(0)
        end_idx = match.end()

        # Check if we are at the end of the string
        if end_idx < len(match.string):
            next_char = match.string[end_idx]
            # If followed by . or _, treat it as a filename, NOT an escape.
            if next_char in (".", "_"):
                return str(full_match)

        if code.startswith("x"):
            return chr(int(code[1:], 16))
        return chr(int(code, 8))

    text = re.sub(pattern, _replace_match, text)
    return text.replace("\r\n", "\n").replace("\r", "\n")
