# PyTVPaint 🐍 → 🦋

[![](https://img.shields.io/github/actions/workflow/status/brunchstudio/pytvpaint/docs-deploy.yml?label=docs)](https://brunchstudio.github.io/pytvpaint/)
[![](https://img.shields.io/github/license/brunchstudio/pytvpaint)](https://github.com/brunchstudio/pytvpaint/blob/main/LICENSE.md)
[![](https://img.shields.io/pypi/v/pytvpaint)](https://pypi.org/project/pytvpaint/)
[![Downloads](https://static.pepy.tech/badge/pytvpaint/month)](https://pepy.tech/project/pytvpaint)
[![](https://img.shields.io/pypi/pyversions/pytvpaint)](https://pypi.org/project/pytvpaint/)

PyTVPaint is a library that allows you to script for [TVPaint](https://www.tvpaint.com/) in Python instead of [George](https://www.tvpaint.com/doc/tvp11/index.php?id=lesson-advanced-functions-george-introduction).

Python is the go-to language when it comes to scripting, PyTVPaint offers a high level object-oriented API as well as low-level George commands in a fully type-hinted library.

PyTVPaint communicates through WebSocket to a [custom C++ plugin](https://github.com/brunchstudio/tvpaint-rpc) running in an opened TVPaint instance.

![](./assets/pytvpaint_code_banner.png)

!!! warning

    PyTVPaint only works on Windows for now (because of the C++ plugin, the python code is agnostic to the platform but hasn't yet been tested on other OSes).
    Support for Linux and MacOS can be added later. If you're interested, please [submit an issue](https://github.com/brunchstudio/tvpaint-rpc/issues/new) or a pull request !

## Why use PyTVPaint?

- **Coding in George is not optimal** - it produces hard to maintain code, has bugs and poor support in IDEs (except syntax highlighting in IDEs, for example [VSCode](https://marketplace.visualstudio.com/items?itemName=johhnry.vscode-george)).

- **Fully documented** - all modules are fully documented and the george docstring is up-to-date, clearer and fixes some of the mistakes in TVPaints George documentation.

- **Fully type-hinted and tested API** - the library uses [MyPy](https://mypy.readthedocs.io) to strictly check the Python code, [Ruff](https://docs.astral.sh/ruff/) to lint and detect errors and [Pytest](https://docs.pytest.org) with ~2500 unit tests and has a test coverage of more than 90%.

- **Seamless coding experience** - no need to manually connect or disconnect to the WebSocket server, you can start coding directly and PyTVPaint will do everything for you! Just code in your favourite language (Python) and it will work!

- **Fully extensible** - a George function wasn't implemented? You can either submit an issue on the repository or [code it yourself](./contributing/wrap_george.md)! We provide tools to directly speak in George with TVPaint and parse the resulting values.

- **Used in production** - PyTVPaint comes from a frustration of coding in the George programming language which made our codebase really hard to maintain here at [BRUNCH Studio](https://brunchstudio.tv/). It's now used in production to support our pipeline.

## PyTVPaint examples

Get the name of all the layers in the current clip:

```python
from pytvpaint.clip import Clip

clip = Clip.current_clip()

for layer in clip.layers:
    print(layer.name)
```

Creating a new project:

```python
from pytvpaint import Project

new_project = Project.new(
    "./project.tvpp",
    width=500,
    height=800,
    frame_rate=25,
    start_frame=10,
)

new_project.save()
```

Render all the clips in the project:

```python
from pathlib import Path

from pytvpaint import Project

project = Project.current_project()

for clip in project.clips:
    out_clip = Path.cwd() / clip.name / f"{clip.name}.#.jpg"
    clip.render(out_clip)
```

Iterates through the layer instances:

```python
from pytvpaint import Layer

for instance in Layer.current_layer().instances:
    print(instance.start, instance.name)
```
