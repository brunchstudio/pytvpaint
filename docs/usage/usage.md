# Usage

PyTVPaint offers **two ways** to interact with TVPaint.

The recommended one is to use the [**object-oriented API**](#object-oriented-api) which handles all the nitty-gritty details of George
and provides an extra layer of features. The classes can be imported from `pytvpaint.*`

The other way is to use the [**wrapped George functions**](#george-functions) in Python which behave almost exactly as
their George counterparts. These can be imported from `pytvpaint.george.*`.

## Environment variables

PyTVPaint can be configured using these variables:

| Name                           | Default value    | Description                                                                                                                    |
| :----------------------------- | :--------------- | :----------------------------------------------------------------------------------------------------------------------------- |
| `PYTVPAINT_LOG_LEVEL`          | `INFO`           | Changes the log level of PyTVPaint. Use the `DEBUG` value to see the RPC requests and responses for debugging George commands. |
| `PYTVPAINT_WS_HOST`            | `ws://localhost` | The hostname of the RPC over WebSocket server ([tvpaint-rpc](https://github.com/brunchstudio/tvpaint-rpc) plugin).             |
| `PYTVPAINT_WS_PORT`            | `3000`           | The port of the RPC over WebSocket server ([tvpaint-rpc](https://github.com/brunchstudio/tvpaint-rpc) plugin).                 |
| `PYTVPAINT_WS_STARTUP_CONNECT` | `1`              | Whether or not PyTVPaint should automatically connect to the WebSocket server at startup (module import). Accepts 0 or 1.      |
| `PYTVPAINT_WS_TIMEOUT`         | `60` seconds     | The timeout after which we stop reconnecting at startup or if the connection was lost.                                         |

## Automatic client connection

When you first import `pytvpaint`, a WebSocket client is automatically created and tries to connect to the server run by the [C++ plugin you installed](../installation.md).

For example in an interactive Python shell:

```console
>>> from pytvpaint.layer import Layer
[2024-02-26 12:39:00,634] pytvpaint / INFO -- Connected to TVPaint on port 3000
```

!!! tip

    Set the `PYTVPAINT_LOG_LEVEL` environment variable to `INFO` to see the log above.

!!! tip

    You can disable this automatic behavior by setting the `PYTVPAINT_WS_STARTUP_CONNECT` variable to `0`.

## Object-oriented API

PyTVPaint provides an object-oriented API that handles the George calls behind the scenes. Most objects in TVPaint have
their own implementation (`Project`, `Scene`, `Clip`, `Layer`...).

### Getting the current data in TVPaint

Most of the classes provide a way to get the **current** element in TVPaint because the current state of the open
TVPaint instance matters when querying data from TVPaint.

For example to get the current clip:

```python
from pytvpaint.clip import Clip

clip = Clip.current_clip()

# You can also get the current layer
layer = clip.current_layer
```

### Structure

The API follows the structure of TVPaint projects in this order: `Project -> Scene -> Clip -> Layer`.

In practice you can do this:

```python
from pytvpaint import Project

project = Project.current_project()

for scene in project.scenes:
    for clip in scene.clips:
        for layer in clip.layers:
            print(layer)
```

### Generators

Since George commands are time expensive to run, most of the properties that returns objects are in fact generators of objects.

For example:

```python
for layer in clip.layers:
    # Do something with layer, consumes it

# To get the list of layers you need to consume the whole generator
layers = list(clip.layers)
```

### Data refreshing

To keep an up-to-date state of the objects in TVPaint (since changes can happen through both the code and the UI),
The library "refreshes" the objects any time a property or method is called by querying TVPaint before running some commands.
This sometime means jumping from element to element (projects, clips, etc...) in the UI.

For example getting the project path:

```python
from pytvpaint import Layer

layer = Layer.current_layer()

# Gets the layer name
layer_name = layer.name

# The user changes the layer name in the interface...

# The name property gives the right value
refreshed_name = layer.name
```

### Invalid and removable objects

Another issue we are facing is that if you have a Python object instance representing a layer and you remove that layer in TVPaint, then the Python object is no longer _valid_.
Another issue we are facing is objet deletions. Let's say you have a Python `Layer` object, and you remove it in the TVPaint UI,
that the Python object is no longer _valid_.

There's two ways an object can be considered invalid:

1. The programmer explicitly removed the object by calling the `.remove()` method.
2. The object itself was removed from the TVPaint interface.

In this example we remove a layer and try to access it afterward:

```python
from pytvpaint import Layer

layer = Layer.current_layer()
layer.remove()

# Will raise a ValueError: Layer has been removed!
print(layer.name)
```

This is the same if we close the project containing the layer:

```python
from pytvpaint import Project

project = Project.current_project()
layer = project.current_clip.current_layer

project.close()

# Will raise an error when we try to access properties
print(layer.name)
```

## Sequence parsing with Fileseq

When providing an output path to our functions, we use the handy Python library [Fileseq](https://github.com/justinfx/fileseq)
for parsing and handling the expected frame ranges, which means you can use frame range expressions when rendering a clip or a project.

For example, you can use:

```python
from pytvpaint.clip import Clip

clip = Clip.current_clip()
clip.render("./out.10-22#.png")
# This will render a sequence of (10-22) like so out.0010.png, out.0011.png, ..., out.0022.png

# This is the same as doing
clip.render("./out.#.png", start=10, end=22)
```

## Utilities

### Undoable

In George, you can manage the undo/redo stack with the [`tv_undoopenstack`](../api/george/misc.md#pytvpaint.george.grg_base.tv_undo_open_stack) and [`tv_undoclosestack`](../api/george/misc.md#pytvpaint.george.grg_base.tv_undo_close_stack) functions.

In order to facilitate this process, we provide :

- the [`undoable`](../api/george/misc.md#pytvpaint.george.grg_base.undoable) decorator
- the [`undoable_stack`](../api/george/misc.md#pytvpaint.george.grg_base.undoable_stack) context manager.

Undo a whole function:

```python
from pytvpaint import george


@george.undoable
def some_george_actions():
    george.tv_bookmark_clear(5)
    george.tv_background_set(george.BackgroundMode.NONE)
```

Or only register some operations:

```python
from pytvpaint import george
from pytvpaint.project import Project


def some_george_actions():
    with george.undoable_stack():
        p = Project.new("./project.tvpp")
        p.start_frame = 67

    p.add_sound("test.wav")
```

### Rendering Contexts

TVPaint's rendering functions do not provided an easy way to set render settings, you are expected to set
these yourself and restore them to their previous values when done.
PyTVPaint provides two helpful context functions to make this easier:

- the [`render_context`](../api/utils.md#pytvpaint.utils.render_context) context manager.
- the [`restore_current_frame`](../api/utils.md#pytvpaint.utils.restore_current_frame) context manager.

!!! Note

    Our `Clip.render` and `Project.render` functions already use these contexts so you don't have to.

#### `render_context`

Using `render_context` will :

- Set the alpha mode and save format (with custom options)
- Hide / Show the given layers (some render functions only render by visibility)
- Restore the previous values after rendering

```python
from pytvpaint.utils import render_context

with render_context(
    alpha_mode,
    save_format,
    format_opts,
    layer_selection=[my_layer],
):
    george.tv_save_image(export_path)
```

#### `restore_current_frame`

Context that temporarily changes the current frame to the one provided and restores it when done.

```python
from pytvpaint.utils import restore_current_frame

with restore_current_frame(my_clip, my_render_frame):
    george.tv_save_display(export_path)
```

## George functions

The George functions are implemented in the [`pytvpaint.george`](../api/george/project.md) module, sorted by the type of TVPaint element they operate on.

The idea is to map these closely the real George functions documented [here](https://www.tvpaint.com/doc/tvpaint-animation-11/george-commands) (parameters, return types, enum values...).

!!! note

    Not all George functions are implemented in the library for now. Some are quite complicated to "translate" but
    others are trivial. For now we only implemented the functions that suit our needs in our pipeline. Feel free to
    make a PR or write an issue on Github if you want to contribute !

Here is an example of how you can use the basic/wrapped George functions:

```python
# Handy because you have access to all the functions within a single module
from pytvpaint import george

current_layer_id = george.tv_layer_current_id()
george.tv_layer_anim(current_layer_id)

# All the _info functions return a dataclass containing the returned values (here TVPLayer)
name = george.tv_layer_info(current_layer_id).name

george.tv_layer_rename(current_layer_id, f"{name}_anim_layer")
```

!!! success

    And that's it! No more `PARSE result` in George and everything is type-hinted and documented!
    We still recommend using the high level API though, if you found that something is missing, please open an issue!
