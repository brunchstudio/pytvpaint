from __future__ import annotations

from dataclasses import Field, fields, is_dataclass
from enum import Enum
from typing import (
    Any,
    ClassVar,
    Sequence,
    TypeVar,
    Union,
    cast,
    get_type_hints,
)

from typing_extensions import Protocol, TypeAlias


# Might not work as expected for pyright, see
#   https://github.com/python/typeshed/pull/9362
#   https://github.com/microsoft/pyright/issues/4339
class DataclassInstance(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]


def tv_handle_string(s: str) -> str:
    """
    String handling for George arguments
    It wraps the string into quotes if it has spaces
    See an example here: https://www.tvpaint.com/doc/tvpaint-animation-11/george-commands#tv_projectnew
    """
    if " " in s:
        return f'"{s}"'

    return s


def camel_to_pascal(s: str) -> str:
    """
    Convert a camel case string to pascal case
    Example: this_is_a_text -> ThisIsAText
    """
    return "".join([c.capitalize() for c in s.split("_")])


T = TypeVar("T", bound=Any)


def tv_cast_to_type(value: str, cast_type: type[T]) -> T:
    """
    Cast a value to the provided type using George's convention for values.
    Note that "1" and "on"/"ON" values are considered True when parsing a boolean
    """
    if issubclass(cast_type, Enum):
        value = value.strip().strip('"')

        # Find the enum member that matches
        for member in cast_type:
            if value.lower() == member.value.lower():
                return cast(T, member)

        # It didn't work, it can be the enum index
        try:
            index = int(value)
        except ValueError:
            raise ValueError(
                f"{value} is not a valid Enum index since it can't be parsed as int"
            )

        # We get the enum member at that index
        enum_members = list(cast_type)
        if index < len(enum_members):
            return cast(T, enum_members[index])

        raise ValueError(
            f"Enum index {index} is out of bounds (max {len(enum_members) - 1})"
        )

    if cast_type == bool:
        return cast(T, value.lower() in ["1", "on", "true"])

    if cast_type == str:
        return cast(T, value.strip().strip('"'))

    return cast(T, cast_type(value))


FieldTypes: TypeAlias = "list[tuple[str, Any]]"


def _get_dataclass_fields(
    datacls: DataclassInstance | type[DataclassInstance],
) -> FieldTypes:
    """
    Get the dataclass key/type pairs and filter those with "parsed
    """
    type_hints = get_type_hints(datacls)
    return [
        (f.name, type_hints[f.name])
        for f in fields(datacls)
        if f.metadata.get("parsed", True)
    ]


def tv_parse_dict(
    output: str, with_fields: FieldTypes | type[DataclassInstance]
) -> dict[str, Any]:
    """
    Parse a list of values as key value pairs returned from TVPaint commands.
    Cast the values to a provided Data Class type or list of key/types pairs.
    """
    # For dataclasses get the type hints and filter those with metadata
    if is_dataclass(with_fields):
        with_fields = _get_dataclass_fields(with_fields)
    else:
        # Explicitly cast because we are sure now
        with_fields = cast(FieldTypes, with_fields)

    output_dict: dict[str, Any] = {}
    search_start = 0

    for i, (field_name, field_type) in enumerate(with_fields):
        current_key_pascal = camel_to_pascal(field_name)

        # Search for the key from the end
        search_text = output.lower()
        try:
            start = search_text.index(current_key_pascal.lower(), search_start)
        except ValueError:
            continue

        if i < (len(with_fields) - 1):
            # Search for the next key also from the end
            next_key_pascal = camel_to_pascal(with_fields[i + 1][0])
            end = search_text.rfind(" " + next_key_pascal.lower(), search_start)
        else:
            end = len(output)

        # Get the "key value" substring
        key_value = output[start:end]

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
    """
    Parse a list of values returned from TVPaint commands.
    Cast the values to a provided Data Class type or list of key/types pairs.

    You can specify unused indices to exclude positional values from being parsed.
    This is useful because some George commands have unused return values.
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
        with_fields = _get_dataclass_fields(with_fields)
    else:
        # Explicitly cast because we are sure now
        with_fields = cast(FieldTypes, with_fields)

    # Remove any unused values
    if unused_indices:
        tokens = [t for i, t in enumerate(tokens) if i not in unused_indices]

    # Cast each token to a type and construct the dict
    tokens_dict: dict[str, Any] = {}
    for token, (field_name, field_type) in zip(tokens, with_fields):
        token = tv_cast_to_type(token, field_type)
        tokens_dict[field_name] = token

    return tokens_dict


def args_dict_to_list(args: dict[str, Any]) -> list[Any]:
    """
    Converts a dict of named arguments to a flat list of key/values
    It also filters pairs with None values
    """
    args_filter = {k: v for k, v in args.items() if v is not None}
    # Flatten dictionnary key value pairs with zip
    return [item for kv in args_filter.items() for item in kv]


Value = Union[int, float, str, bool, None]


def consecutive_optional_args_to_list(
    optional_args: Sequence[Value | tuple[Value, ...]]
) -> list[Any]:
    """
    Some George functions accept optional arguments but consecutively it means that
    to set the last positional argument you need to give all the previous ones.

    This function allows you to give a list of argument or argument blocks (as tuples)
    and check that they are not None up to a point.

    For example, for tv_camerainfo [<iWidth> <iHeight> [<field_order>]]
    you can't give [500, None, "upper"] because <iHeight> is not defined
    """
    args: list[Any] = []

    for arg in optional_args:
        if arg is None or (type(arg) == tuple and all(a is None for a in arg)):
            break

        # If it's a tuple they need to be defined
        if type(arg) == tuple:
            if any(a is None for a in arg):
                raise ValueError(f"You must pass all the parameters: {arg}")
            args.extend(arg)
        else:
            args.append(arg)

    return args
