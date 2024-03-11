# Pytvpaint 🐍 → 🦋

![](https://img.shields.io/github/actions/workflow/status/brunchstudio/pytvpaint/docs-deploy.yml?label=docs) ![](https://img.shields.io/github/license/brunchstudio/pytvpaint)

Pytvpaint is a library that allows you to script for [TVPaint](https://www.tvpaint.com/) in Python instead of [George](https://www.tvpaint.com/doc/tvp11/index.php?id=lesson-advanced-functions-george-introduction).

Python is the go-to language when it comes to scripting, Pytvpaint offers a high level object-oriented API as well as low-level George commands in a fully type-hinted library.

It communicates through WebSocket to a [custom C++ plugin]() running in an opened TVPaint instance.

![](./assets/pytvpaint_code_banner.png)

!!! warning

    Pytvpaint only works on Windows for now (because of the C++ plugin).
    Support for Linux and MacOS can be added later. If you're interested, please submit an issue!

## Why use Pytvpaint?

- **Coding in George is not optimal** - it produces hard to maintain code, has bugs and poor support in IDEs (only syntax highlighting [in VSCode](https://marketplace.visualstudio.com/items?itemName=johhnry.vscode-george)).

- **Fully type-hinted, tested and documented API** - our library uses [MyPy](https://mypy.readthedocs.io) to strictly check the Python code, [Ruff](https://docs.astral.sh/ruff/) to lint and detect errors and [Pytest](https://docs.pytest.org) with 3000+ unit tests and has a test coverage of more than 90%.

- **Seamless coding experience** - no need to manually connect or disconnect to the WebSocket server, you can start coding directly and Pytvpaint will do everything for you! Just code in your favourite language (Python) and it will work!

- **Fully extensible** - a George function wasn't implemented? You can either submit an issue on the repository or code it yourself! We provide tools to directly speak in George with TVPaint and parse the resulting values.

## Pytvpaint examples

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

## Credits

- The [George commands documentation](https://www.tvpaint.com/doc/tvpaint-animation-11/george-commands) from TVPaint.

- The C++ plugin was made possible with the already existing codebase of Ynput's [OpenPype TVPaint plugin](https://github.com/ynput/OpenPype/tree/develop/openpype/hosts/tvpaint/tvpaint_plugin/plugin_code).

- Also thanks to [Jakub Trllo](https://www.linkedin.com/in/jakub-trllo-751387a6/) from Ynput who helped with the C++ implementation on their Discord server 🙏.

!!! Quote "Quote from Milan Kolar (ynput)"

    Great things happen when open-source builds on open-source that builds on open-source!
