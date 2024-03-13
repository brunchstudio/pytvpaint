# Pytvpaint 🐍 → 🦋

[![](https://img.shields.io/github/actions/workflow/status/brunchstudio/pytvpaint/docs-deploy.yml?label=docs)](https://brunchstudio.github.io/pytvpaint/)
[![](https://img.shields.io/github/license/brunchstudio/pytvpaint)](https://github.com/brunchstudio/pytvpaint/blob/main/LICENSE.md)
[![](https://img.shields.io/pypi/v/pytvpaint)](https://pypi.org/project/pytvpaint/)
[![Downloads](https://static.pepy.tech/badge/pytvpaint/month)](https://pepy.tech/project/pytvpaint)
[![](https://img.shields.io/pypi/pyversions/pytvpaint)](https://pypi.org/project/pytvpaint/)

<p align="center">
    <img src="https://raw.githubusercontent.com/brunchstudio/pytvpaint/main/docs/assets/pytvpaint_code_banner.png" width=700 />
</p>

**Pytvpaint** is a type-safe Python library that wraps the George programming language commands in order to interact with the 2D animation software TVPaint.

It communicates through WebSocket to a [custom C++ plugin](https://github.com/brunchstudio/tvpaint-rpc) running in an opened TVPaint instance.

You can check the [documentation](https://brunchstudio.github.io/pytvpaint/) for more details.

## Installation

First install the [TVPaint RPC plugin](https://brunchstudio.github.io/pytvpaint/installation/#tvpaint-plugin-installation).

Then install the package with Pip:

```console
❯ pip install pytvpaint
```

## Simple example

```python
from pytvpaint import george
from pytvpaint.project import Project

# Get access to tvp elements
project = Project.load("scene.tvpp", silent=True)

clip = project.current_clip
# Or get the clip by name
clip = project.get_clip(by_name="my_clip")

layer = clip.add_layer("my_new_layer")

# Check out other layers
for layer in clip.layers:
    print(layer.name)

# Get access to George functions
george.tv_rect(50, 50, 100, 100)

# Render your file
clip.render("./out.#.png", start=20, end=45)

project.close()
```

## Contributing

Pull requests are welcome. For major changes, please [open an issue](https://github.com/brunchstudio/pytvpaint/issues/new/choose) first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](./LICENSE.md)

<hr>

Made with ❤️ at [BRUNCH Studio](https://brunchstudio.tv/) 🥐🍳
