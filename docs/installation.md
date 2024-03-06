# Installation

## TVPaint plugin installation

In order for Pytvpaint to work, a custom C++ plugin needs to be setup in your TVPaint installation.

### Windows

- Download the latest [`tvpaint-ws-server.dll`]() file.
- Copy it in your TVPaint `plugins` folder:

  ```
  C:/PROGRA~1/TVPaint Developpement/TVPaint Animation <version> Pro (64bits)/plugins
  ```

!!! note

    You may need Administrator rights to copy the DLL file.

## Pytvpaint package

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
