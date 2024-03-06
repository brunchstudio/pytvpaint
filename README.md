# Pytvpaint 🐍 → 🦋

<center>
<img src="./docs/assets/pytvpaint_code_banner.png" width=500 />
</center>

**Pytvpaint** is a type-safe Python library that wraps the George programming language commands in order to interact with the 2D animation software TVPaint.

It communicates through WebSocket to a [custom C++ plugin](./cpp) running in an opened TVPaint instance.

## Installation

```console
❯ pip install pytvpaint
```

## Simple example

```python
from pytvpaint.clip import Clip

clip = Clip.current_clip()

for layer in clip.layers:
    print(layer.name)
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](./LICENSE.md)

<hr>

Made with ❤️ at [BRUNCH Studio](https://brunchstudio.tv/) 🥐🍳
