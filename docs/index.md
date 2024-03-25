# PyTVPaint 🐍 → 🦋

[![](https://img.shields.io/github/actions/workflow/status/brunchstudio/pytvpaint/docs-deploy.yml?label=docs)](https://brunchstudio.github.io/pytvpaint/)
[![](https://img.shields.io/github/license/brunchstudio/pytvpaint)](https://github.com/brunchstudio/pytvpaint/blob/main/LICENSE.md)
[![](https://img.shields.io/pypi/v/pytvpaint)](https://pypi.org/project/pytvpaint/)
[![Downloads](https://static.pepy.tech/badge/pytvpaint/month)](https://pepy.tech/project/pytvpaint)
[![](https://img.shields.io/pypi/pyversions/pytvpaint)](https://pypi.org/project/pytvpaint/)
[![](https://custom-icon-badges.demolab.com/badge/custom-11.5+-blue.svg?logo=butterfly_1f98b&label=TVPaint)](https://www.tvpaint.com/doc/tvp11/)

PyTVPaint lets you script for [TVPaint](https://www.tvpaint.com/) in Python instead of 
[George](https://www.tvpaint.com/doc/tvp11/index.php?id=lesson-advanced-functions-george-introduction). It offers a 
high level object-oriented API as well as low-level George commands in a fully type-hinted library.

PyTVPaint communicates through WebSocket to a [custom C++ plugin](https://github.com/brunchstudio/tvpaint-rpc) running in an open TVPaint instance.

![](./assets/pytvpaint_code_banner.png)

!!! warning

    PyTVPaint only works on Windows for now (because of the C++ plugin, the python code is agnostic to the platform but hasn't yet been tested on other OSes).
    Support for Linux and MacOS can be added later. If you're interested, please [submit an issue](https://github.com/brunchstudio/tvpaint-rpc/issues/new) or a pull request !

## Why use PyTVPaint?

- **Coding in George is not optimal** - it produces hard to maintain code, has bugs and poor support in IDEs (except syntax highlighting in IDEs, for example [VSCode](https://marketplace.visualstudio.com/items?itemName=johhnry.vscode-george)).

- **Fully documented** - all modules are fully documented and the george docstring is up-to-date, clearer and fixes many of the errors in the official George documentation.

- **Fully type-hinted and tested API** - the library uses [MyPy](https://mypy.readthedocs.io) to strictly check the Python code, [Ruff](https://docs.astral.sh/ruff/) to lint and detect errors and [Pytest](https://docs.pytest.org) and is almost fully unit tested.

- **Seamless coding experience** - no need to manually connect or disconnect to the WebSocket server, you can start coding directly and PyTVPaint will do everything for you! Just code in your favourite language (Python) and it will work!

- **Fully extensible** - a George function wasn't implemented? You can either submit an issue on the repository or [code it yourself](./contributing/wrap_george.md)! We provide tools to directly speak in George with TVPaint and parse the resulting values.

- **Used in production** - PyTVPaint was born from the frustration of coding in George which made our codebase really hard to maintain here at [BRUNCH Studio](https://brunchstudio.tv/). It's now used in production to support our pipeline.

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

Iterate through the layer instances:

```python
from pytvpaint import Layer

for instance in Layer.current_layer().instances:
    print(instance.start, instance.name)
```

## Disclaimer

PyTVPaint is a project created at BRUNCH Studio to facilitate our development experience with George. The API is targeted at experienced developers and is by no means a replacement for TVPaint or George but simply builds on it.

We are not affiliated with the TVPaint development team and therefore can't fix any bugs in the software or the George API.

Please direct your issues appropriately; any issues with PyTVPaint should be submitted as [an issue in this repository](https://github.com/brunchstudio/pytvpaint/issues) or the [C++ plugin's repository](https://github.com/brunchstudio/tvpaint-rpc), any issues with TVPaint the software should be addressed to the [tvp support team](https://tvpaint.odoo.com/en_US/contactus).

For any questions on the limitations of our API, please head to [this page](limitations.md).
