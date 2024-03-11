# Wrapping George commands

This guide explains how to wrap a George command. The first step is to look at the [George command documentation](https://www.tvpaint.com/doc/tvpaint-animation-11/george-commands) and pick the one you want to implement.

## Simple command without arguments

This one is simple because we don't have any arguments and return value:

!!! Example

    ```
    tv_lockuser

    Disable interaction of the user with the interface
    ```

Use the [`send_cmd`](../api/client/communication.md#pytvpaint.george.client.send_cmd) function to send a George command:

```python
from pytvpaint import send_cmd

def tv_lock_user() -> None: # (1)!
    send_cmd("tv_LockUser") # (2)!
```

1. We use Camel case for functions so we break words in George commands. So `tv_lockuser` becomes `tv_lock_user`.
2. We use Pascal case for the George command strings because it's case insensitive and has better readability than `tv_lockuser`.

## Command with arguments

!!! Example

    ```
    tv_libraryimagecopy

    Copy an object

    [PARAMETERS]
    "id" iId    string    The id

    [RETURN]
    0    int    Object copied

    [ERROR]
    -2    int    No project/no library
    -3    int    No param/invalid param
    ```

```python
from pytvpaint import send_cmd

def tv_library_image_copy(image_id: str) -> None:
    send_cmd("tv_LibraryImageCopy", image_id, error_values=[-2, -3]) # (1)!
```

1. Note that we provide the error values that George returns. If `send_cmd` get those values it raises a `GeorgeError` exception.

Notes:

- `send_cmd` accepts any number of arguments to send to the George command.
- You can provide custom values for the error that should be raised.

## Command with complex arguments and return values

This command is more tricky. It has:

- Multiple arguments
- Optional arguments (more than one sometimes)
- A dict-like return string value

!!! Example

    ```
    tv_pegholesset ["w" iWidth] ["h" iHeight] ["c1" iCenterX1 iCenterY1] ["c2" iCenterX2 iCenterY2] ["sw" iWidth] ["sh" iHeight] ["so1" iOffsetX1 iOffsetY1] ["so2" iOffsetX2 iOffsetY2]

    Manage pegholes

    [PARAMETERS]
    "w" iWidth                   int              The width of boxes
    "h" iHeight                  int              The height of boxes
    "c1" iCenterX1 iCenterY1     double double    The center of box 1
    "c2" iCenterX2 iCenterY2     double double    The center of box 2
    "sw" iWidth                  int              The additional width of for search boxes (added in 11.0.8)
    "sh" iHeight                 int              The additional height of for search boxes (added in 11.0.8)
    "so1" iOffsetX1 iOffsetY1    double double    The offset of search box 1 (added in 11.0.8)
    "so2" iOffsetX2 iOffsetY2    double double    The offset of search box 2 (added in 11.0.8)

    [RETURN]
    "w" oWidth "h" oHeight "c1" oCenterX1 oCenterY1 "c2" oCenterX2 oCenterY2 "sw" oWidth "sh" oHeight "so1" oOffsetX1 oOffsetY1 "so2" oOffsetX2 oOffsetY2

    "w" oWidth                   int              The current/previous width of boxes
    "h" oHeight                  int              The current/previous height of boxes
    "c1" oCenterX1 oCenterY1     double double    The current/previous center of box 1
    "c2" oCenterX2 oCenterY2     double double    The current/previous center of box 2
    "sw" oWidth                  int              The current/previous additional width of for search boxes (added in 11.0.8)
    "sh" oHeight                 int              The current/previous additional height of for search boxes (added in 11.0.8)
    "so1" oOffsetX1 oOffsetY1    double double    The current/previous offset of search box 1 (added in 11.0.8)
    "so2" oOffsetX2 oOffsetY2    double double    The current/previous offset of search box 2 (added in 11.0.8)

    [ERROR]
    "ERROR"    string    No peghole
    ```

```python
from dataclasses import dataclass

from pytvpaint import send_cmd
from pytvpaint.george.client.parse import args_dict_to_list, tv_parse_dict


@dataclass(frozen=True) # (1)!
class PegHole:
    w: int
    h: int
    c1: tuple[float, float]
    c2: tuple[float, float]
    sw: int
    sh: int
    so1: tuple[float, float]
    so2: tuple[float, float]


def tv_peg_hole_set(
    w: int | None = None,
    h: int | None = None,
    c1: tuple[float, float] | None = None,
    c2: tuple[float, float] | None = None,
    sw: int | None = None,
    sh: int | None = None,
    so1: tuple[float, float] | None = None,
    so2: tuple[float, float] | None = None,
) -> PegHole:
    params_dict = {
        "w": w,
        "h": h,
        "c1": c1,
        "c2": c2,
        "sw": sw,
        "sh": sh,
        "so1": so1,
        "so2": so2,
    }

    args = args_dict_to_list(params_dict)

    result = send_cmd("tv_PegHolesSet", *args)
    result_dict = tv_parse_dict(result, with_fields=PegHole)

    return PegHole(**result_dict)
```

1. Use `frozen=True` to prevent the dataclass attributes from being modified. Since the state of our objects in Python is not directly synchronized with TVPaint's state, we constrain the potentiel bugs.

Notes:

- We use dataclasses to describe the data types of complex objects return from TVPaint. It's similar to [Pydantic's models](https://docs.pydantic.dev/latest/concepts/models/). We then use [`tv_parse_dict`](../api/client/parsing.md#pytvpaint.george.client.parse.tv_parse_dict) to parse the key/value list of values returned from TVPaint to the dataclass types.

- In the George documentation, optional arguments are written with brackets around them like `["w" iWidth] ["h" iHeight]`. In this function all the arguments are optional so we make them optional with `None` as a default value.

- We use `args_dict_to_list` to get a list of key/value pair arguments that only include non `None` values, since it's not necessary to send them to George. For example:
  ```python
  args_dict_to_list({ "w": 5, "h": None, "m": "t" }) == ["w", 5, "m", "t"]
  ```

!!! Success

    Everything is now correctly type-hinted and easy to use!

    ```python
    print(tv_peg_hole_set(w=50, h=100))
    # => PegHole(w=50, h=100, c1=(25.0, 200.0), c2=(25.0, 200.0), sw=10, sh=10, so1=(5.0, 5.0), so2=(5.0, 3.0))
    ```

## Command that get and set a value

Some George commands are a getter and a setter at the same time. In Pytvpaint, we split the command in two separate functions with `_get` and `_set` suffix.

!!! Example

    ```
    tv_notelock [0|1|"on"|"off"|"lock"|"unlock"|"toggle"]

    Manage lock state of timeline note

    [PARAMETERS]
    0|1|"on"|"off"|"lock"|"unlock"|"toggle"    enum    The new lock state

    [RETURN]
    "on"|"off"    enum    The previous/current lock state
    ```

```python
from pytvpaint.george.client import send_cmd


def tv_note_lock_get() -> bool:
    return send_cmd("tv_NoteLock") == "on"


def tv_note_lock_set(state: bool) -> None:
    send_cmd("tv_NoteLock", int(state))
```
