# Installation

## TVPaint plugin installation

PyTVPaint works by sending George commands to a custom C++ plugin running a WebSocket server in TVPaint.

You need to manually install it in your TVPaint installation folder.

### Windows

- Download the latest [`tvpaint-rpc.dll`](https://github.com/brunchstudio/tvpaint-rpc/releases) file from the GitHub releases.
- Copy it in your TVPaint `plugins` folder:

  ```
  C:/Program Files/TVPaint Developpement/TVPaint Animation <version> Pro (64bits)/plugins
  ```

!!! note

    You may need Administrator rights to copy the DLL file.

## PyTVPaint package

Simply install it with Pip:

```console
❯ pip install pytvpaint
```

or use [Poetry](https://python-poetry.org/):

```console
❯ poetry add pytvpaint
```

!!! success

    You are now ready to start coding in Python for TVPaint!
