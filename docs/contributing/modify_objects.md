# Modifying high-level classes

This guide explains how to create/modify the high-level Python API with classes like [`Project`](../api/objects/project.md), [`Clip`](../api/objects/clip.md) or [`Layer`](../api/objects/layer.md).

Classes are object oriented wrappers around the raw data from TVPaint (as dataclasses).

For example the `Project` class has a `_data` attribute which is the main state of the object:

```python
# pytvpaint/project.py

class Project(Refreshable):
    def __init__(self, project_id: str) -> None:
        super().__init__()
        # ...
        self._data: TVPProject = george.tv_project_info(self._id)
```

The type of the internal `_data` attribute is [`TVPProject`](../api/george/project.md#pytvpaint.george.grg_project.TVPProject) which is the dataclass containing the data returned by TVPaint and parsed by our API.

## Properties

We use properties to expose the attributes of the object while controlling which one can be get or set by the end user.

For example this is the `id` property of the Project class, it can be read but not written (project ids are persistent across sessions):

```python
@property
def id(self) -> str:
    """The project id.

    Note:
        the id is persistent on project load/close.
    """
    return self._id
```

### Refreshable properties

Some properties can be changed after the object instance is created in Python. This means that the state of the Python object is different from the state of the real object in TVPaint. Since the data is fetched only at init, we need a mechanism to refresh the data at each property call.

Here is an example with the [`refreshed_property`](../api/utils.md#pytvpaint.utils.RefreshedProperty) decorator:

```python
@refreshed_property
def path(self) -> Path:
    """The project path on disk."""
    return self._data.path
```

It calls the object's overriden [`self.refresh()`](../api/utils.md#pytvpaint.utils.Refreshable.refresh) method before returning the internal value. This ensure that the value you are getting is always the right one at call time.

## Make the object current

Some George functions only apply to the "current" object in the TVPaint instance.

To do that in an elegant way, we use the [`set_as_current`](../api/utils.md#pytvpaint.utils.set_as_current) decorator for all the methods and properties that require that object to be the current:

```python
@property
@set_as_current
def width(self) -> int:
    """The width of the canvas."""
    return george.tv_get_width() # (1)!
```

1. Here we use a more specific George function to get the data instead of using the `tv_project_info` function which is more expensive. We don't need `refreshed_property` neither.

It calls the object's `self.make_current()` method.

## Get access to children objects

For the `Project` class, we want to give access to the scenes inside it. To do that we make a property that is a generator over `Scene` objects.

```python
@property
@set_as_current
def scenes(self) -> Iterator[Scene]:
    """Yields the project scenes."""
    from pytvpaint.scene import Scene # (1)!

    for scene_id in self.current_scene_ids():
        yield Scene(scene_id, self) # (2)!
```

1. We use the `from <mod> import ...` statement in the method because the `Scene` and `Project` classes have a circular dependency.
2. We pass `self` as the second argument to have a reference of the project in the Scene object.

!!! Tip

    Most of the `Iterator` in PyTVPaint are generators which mean it will only get the data (and send requests to TVPaint) if you want the next element.

    So you can stop whenever you want:

    ```python
    for scene in project.scenes:
        if scene.id == 787:
            print(scene)
            break
    ```
