# PyTVPaint 🐍 → 🦋

[![](https://img.shields.io/github/actions/workflow/status/brunchstudio/pytvpaint/docs-deploy.yml?label=docs)](https://brunchstudio.github.io/pytvpaint/)
[![](https://img.shields.io/github/license/brunchstudio/pytvpaint)](https://github.com/brunchstudio/pytvpaint/blob/main/LICENSE.md)
[![](https://img.shields.io/pypi/v/pytvpaint)](https://pypi.org/project/pytvpaint/)
[![Downloads](https://static.pepy.tech/badge/pytvpaint/month)](https://pepy.tech/project/pytvpaint)
[![](https://img.shields.io/pypi/pyversions/pytvpaint)](https://pypi.org/project/pytvpaint/)
[![](https://custom-icon-badges.demolab.com/badge/custom-11.5+-blue.svg?logo=butterfly_1f98b&label=TVPaint)](https://www.tvpaint.com/doc/tvp11/)

<p align="center">
    <img src="https://raw.githubusercontent.com/brunchstudio/pytvpaint/main/docs/assets/pytvpaint_code_banner.png" width=700 />
</p>

**PyTVPaint** is a type-safe Python library that wraps the George programming language commands in order to interact with the 2D animation software TVPaint.

It communicates through WebSocket to a [custom C++ plugin](https://github.com/brunchstudio/tvpaint-rpc) running in an open TVPaint instance.

You can check the [documentation](https://brunchstudio.github.io/pytvpaint/) for more details.

## Installation

### Requirements

- Windows (for now, see [this](https://brunchstudio.github.io/pytvpaint/limitations/#windows-only))
- Python v3.9+
- TVPaint v11.5+
- TVPaint RPC plugin (install instructions [here](https://brunchstudio.github.io/pytvpaint/installation/#tvpaint-plugin-installation))

Install the package with Pip:

```console
pip install pytvpaint
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

Please make sure to [update tests](https://brunchstudio.github.io/pytvpaint/contributing/developer_setup/#unit-tests) as appropriate.

## Disclaimer

PyTVPaint is a project created at BRUNCH Studio to facilitate our development experience with George. The API is targeted at experienced developers and is by no means a replacement for TVPaint or George but simply builds on it.

We are not affiliated with the TVPaint development team and therefore can't fix any bugs in the software or the George API.

Please direct your issues appropriately; any issues with PyTVPaint should be submitted as [an issue in this repository](https://github.com/brunchstudio/pytvpaint/issues) or the [C++ plugin's repository](https://github.com/brunchstudio/tvpaint-rpc), any issues with TVPaint the software should be addressed to the [tvp support team](https://tvpaint.odoo.com/en_US/contactus).

For any questions on the limitations of our API, please head to [this page](https://brunchstudio.github.io/pytvpaint/limitations/).

## License

[MIT](./LICENSE.md)

<hr>

Made with ❤️ at [BRUNCH Studio](https://brunchstudio.tv/)
