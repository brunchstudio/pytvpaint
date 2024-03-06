# Usage

Pytvpaint offers **two ways** to interact with TVPaint.

The recommended one is to use the [**object-oriented API**](#object-oriented-api) which handles all the nitty-gritty details of George and provide an extra layer of features. The classes can be imported from `pytvpaint.*`

The other way is to use the wrapped George functions in Python which behaves almost extactly the same as real George commands. Those can be imported from `pytvpaint.george.*`.

## Automatic client connection

When you first import `pytvpaint`, a WebSocket client is automatically created and connects to the server runned by the [C++ plugin you installed](./installation.md).

For example in an interactive Python shell:

```console
>>> from pytvpaint.layer import Layer
[2024-02-26 12:39:00,634] pytvpaint / INFO -- Connected to TVPaint on port 3000
```

!!! tip

    Set the `PYTVPAINT_LOG_LEVEL` environment variable to `INFO` to see the log above.

## Object-oriented API

Pytvpaint provides a high level object-oriented API that handles the George calls behind the scene. Every element in TVPaint has its own object (`Project`, `Scene`, `Clip`, `Layer`...).

### Getting the current data in TVPaint

Most of the classes provide a way to get the **current** element in TVPaint because the current state of the opened TVPaint instance matters.

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
from pytvpaint.project import Project

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

Since the library queries for data, it's not synchronized with the current state of TVPaint. We solve that by "refreshing" the object data when we call properties or methods.

For example getting the project path:

```python
from pytvpaint.layer import Layer

layer = Layer.current_layer()

# Gets the layer name
layer_name = layer.name

# The user changes the layer name in the interface...

# The name property gives the right value
refreshed_name = layer.name
```

### Invalid and removable objects

Another issue we are facing is that if you have a Python object instance representing a layer and you remove that layer in TVPaint, then the Python object is no longer _valid_.

There's two ways an object can be invalid:

1. The programmer explicitly removed the object by calling the `.remove()` method.
2. The object itself was removed from the TVPaint interface.

In this example we are removing a layer:

```python
from pytvpaint.layer import Layer

layer = Layer.current_layer()
layer.remove()

# Will raise a ValueError: Layer has been removed!
print(layer.name)
```

This is the same if we close the project containing the layer:

```python
from pytvpaint.project import Project

project = Project.current_project()
layer = project.current_clip.current_layer

project.close()

# Will raise an error when we try to access properties
print(layer.name)
```

## George functions

George functions are implemented in the [`pytvpaint.george`](./api/george/project.md) module, separated by object on which they operate.

The idea is to map closely the real George functions documented [here](https://www.tvpaint.com/doc/tvpaint-animation-11/george-commands) (parameters, return types, enum values...).

!!! note

    Not all George functions are implemented in the library for now. Some are quite complicated to "translate" but others are trivial. For now we only implemented the majority of George functions that suit our needs in our pipeline. Feel free to make a PR or write an issue on Github!

Here is an example of how you can use basic George functions:

```python
# Handy because you have access to all the functions within a single module
from pytvpaint import george

current_layer_id = george.tv_layer_current_id()
george.tv_layer_anim(current_layer_id)

# All the _info functions return a dataclass instance (here TVPLayer)
name = george.tv_layer_info(current_layer_id).name

george.tv_layer_rename(current_layer_id, f"{name}_anim_layer")
```

!!! success

    And that's it! No more `PARSE result` in George and everything is type-hinted and documented! We still recommend using the high level API thought, if you found that something is missing, please open an issue!
