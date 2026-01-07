"""Parsing functions used to handle data coming from TVPaint and also preparing arguments for them to be sent.

The two main functions are `tv_parse_dict` and `tv_parse_list` which handle the return values of George functions.

George can either return a list of values or a list of key/value pairs which are consecutive.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import Field, fields, is_dataclass
from enum import Enum
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


T = TypeVar("T", bound=Any)


def tv_cast_to_type(value: str, cast_type: type[T]) -> T:
    """Cast a value to the provided type using George's convention for values.

    Note:
        "1" and "on"/"ON" values are considered True when parsing a boolean

    Args:
        value: the input value
        cast_type: the type to cast to

    Raises:
        ValueError: if given an enum, and it can't find the value or the enum index is invalid

    Returns:
        the value cast to the provided type
    """
    if issubclass(cast_type, Enum):
        value = value.strip().strip('"')

        # Find all enum members that matche the value (lower case)
        matches = [m for m in cast_type if value.lower() == m.value.lower()]
        try:
            # If the unmodified value is in the enum, return that first
            return cast(T, next(m for m in matches if value == m.value))
        except StopIteration:
            # Otherwise return the first match
            if matches:
                return cast(T, matches[0])

        # if the above fails, then maybe the value is the index in the enum
        try:
            index = int(value)
        except ValueError:
            raise ValueError(f"{value} is not a valid Enum index since it can't be parsed as int")

        # get the enum member at the index
        enum_members = list(cast_type)
        if index < len(enum_members):
            return cast(T, enum_members[index])

        raise ValueError(f"Enum index {index} is out of bounds (max {len(enum_members) - 1})")

    if get_origin(cast_type) in (tuple, list):
        # Split by space and convert each member to the right type
        values_types = []
        sub_value_types = get_args(cast_type)
        for index, sub_value in enumerate(value.split()):
            sub_value_type = sub_value_types[index]
            cast_sub_value = tv_cast_to_type(sub_value, sub_value_type)
            values_types.append(cast_sub_value)

        origin_type = get_origin(cast_type)
        return cast(T, origin_type(values_types))  # type: ignore[misc]

    if cast_type == bool:
        return cast(T, value.lower() in ["1", "on", "true"])

    if cast_type == str:
        return cast(T, value.strip().strip('"'))

    return cast(T, cast_type(value))


FieldTypes: TypeAlias = list[tuple[tuple[str, str], Any]]


def get_dataclass_fields(
    datacls: DataclassInstance | type[DataclassInstance],
) -> FieldTypes:
    """Get the dataclass key/type pairs and filter those with the "parsed" metadata.

    Args:
        datacls: input dataclass

    Returns:
        the list of key/type tuple
    """
    type_hints = get_type_hints(datacls)
    return [
        ((f.name, f.metadata.get("alt_name", f.name)), type_hints[f.name])
        for f in fields(datacls)
        if f.metadata.get("parsed", True)
    ]


def tv_parse_dict(
    input_text: str,
    with_fields: FieldTypes | type[DataclassInstance],
) -> dict[str, Any]:
    """Parse a list of values as key value pairs returned from TVPaint commands.

    Cast the values to a provided dataclass type or list of key/types pairs.

    Args:
        input_text: the George string result
        with_fields: the field types (can be a dataclass)

    Returns:
        a dict with the values cast to the given types
    """
    # For dataclasses get the type hints and filter those with metadata
    if is_dataclass(with_fields):
        with_fields = get_dataclass_fields(with_fields)
    else:
        # Explicitly cast because we are sure now
        with_fields = cast(FieldTypes, with_fields)

    output_dict: dict[str, Any] = {}
    search_start = 0

    for i, (field_name, field_type) in enumerate(with_fields):
        # handle different naming schemes
        alt_field_name = field_name
        if isinstance(field_name, tuple):
            field_name, alt_field_name = field_name
        current_key_pascal = camel_to_pascal(alt_field_name)

        # Search for the key from the end
        search_text = input_text.lower()
        try:
            start = search_text.index(current_key_pascal.lower(), search_start)
        except ValueError:
            continue

        if i < (len(with_fields) - 1):
            # Search for the next key also from the end
            next_key = with_fields[i + 1][0]
            if isinstance(next_key, tuple):
                next_key = next_key[1]
            next_key_pascal = camel_to_pascal(next_key)
            end = search_text.rfind(" " + next_key_pascal.lower(), search_start)
        else:
            end = len(input_text)

        # Get the "key value" substring
        key_value = input_text[start:end]

        # Extract the value
        cut_at = len(current_key_pascal) + 1
        value = key_value[cut_at:].strip()

        # Cast it to the corresponding type
        value = tv_cast_to_type(value, field_type)

        output_dict[field_name] = value
        search_start = end

    return output_dict


def tv_parse_list(
    output: str,
    with_fields: FieldTypes | type[DataclassInstance],
    unused_indices: list[int] | None = None,
) -> dict[str, Any]:
    """Parse a list of values returned from TVPaint commands.

    Cast the values to a provided dataclass type or list of key/types pairs.

    You can specify unused indices to exclude positional values from being parsed.
    This is useful because some George commands have unused return values.

    Args:
        output: the input string
        with_fields: the field types (can be a dataclass)
        unused_indices: Some George functions return positional arguments that are unused. Defaults to None.

    Returns:
        a dict with the values cast to the given types
    """
    start = 0
    current = 0
    string_open = False
    tokens: list[str] = []

    while current < len(output):
        char = output[current]
        is_quote = char == '"'
        is_space = char == " "
        last_char = current == len(output) - 1

        if (is_space and not string_open) or last_char:
            last_cut = current if not last_char else current + 1
            token = output[start:last_cut]
            if start != last_cut and token != " ":
                tokens.append(token)
            start = current = current + 1
        elif is_quote:
            if string_open:
                tokens.append(output[start:current])

            start = current = current + 1
            string_open = not string_open
        else:
            current += 1

    # Get type annotations from the dataclass fields
    if is_dataclass(with_fields):
        with_fields = get_dataclass_fields(with_fields)
    else:
        # Explicitly cast because we are sure now
        with_fields = cast(FieldTypes, with_fields)

    # Remove any unused values
    if unused_indices:
        tokens = [t for i, t in enumerate(tokens) if i not in unused_indices]

    # Cast each token to a type and construct the dict
    tokens_dict: dict[str, Any] = {}
    for token, (field_name, field_type) in zip(tokens, with_fields):
        # handle different naming schemes
        if isinstance(field_name, tuple):
            field_name, _ = field_name

        token = tv_cast_to_type(token, field_type)
        tokens_dict[field_name] = token

    return tokens_dict


def args_dict_to_list(args: dict[str, Any]) -> list[Any]:
    """Converts a dict of named arguments to a flat list of key/values.

    It also filters pairs with None values

    Args:
        args: dict of arguments

    Returns:
        key/values list
    """
    args_filter = {k: v for k, v in args.items() if v is not None}
    # Flatten dictionnary key value pairs with zip
    return [item for kv in args_filter.items() for item in kv]


Value = Union[int, float, str, bool, None]


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

        # If it's a tuple they need to be defined
        if isinstance(arg, tuple):
            if any(a is None for a in arg):
                raise ValueError(f"You must pass all the parameters: {arg}")
            args.extend(arg)
        else:
            args.append(arg)

    return args
