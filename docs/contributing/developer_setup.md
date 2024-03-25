# Developer setup

This guide will explain how to set up your environment in order to contribute to PyTVPaint.

## Requirements

- [Python](https://www.python.org/) 3.9 or greater are the supported versions for PyTVPaint.

- We use [Poetry](https://python-poetry.org/) which is the packaging and dependency management tool. It handles your dev virtualenv with your working dependencies.

## PyTVPaint

First clone the repository:

```shell
❯ git clone https://github.com/brunchstudio/pytvpaint.git

# or if you use SSH auth
❯ git clone git@github.com:brunchstudio/pytvpaint.git
```

Then install the dependencies in a virtualenv with Poetry:

```shell
❯ poetry install
```

Note that this will only install the library dependency. To install optional [dependency groups](https://python-poetry.org/docs/managing-dependencies/#dependency-groups) (to build the documentation, run tests, etc...) you can use the `--with` parameter:

```shell
❯ poetry install --with dev,docs,test
```

### Code formatting

We use [Black](https://black.readthedocs.io/en/stable/) to ensure that the code format is always the same. Black has strong defaults and is easy to use:

```shell
# Will format all the .py files in the current directory
(venv) ❯ black .

# To only check if the format is correct
(venv) ❯ black --check .
```

!!! Tip

    Use `poetry shell` to enter a new shell in the virtualenv. In this page commands marked `(venv) ❯` can also be run with `poetry run <command>`

### Linting

We also use [Ruff](https://docs.astral.sh/ruff/) as a linter. It combines a lot of rules from other projects like Flake8, pyupgrade, pydocstyle, isort, etc...

```shell
(venv) ❯ ruff .

# Will apply autofixes
(venv) ❯ ruff --fix .
```

### Type checking

Mypy is the go-to static type checker for Python. It ensures that variables and functions are used correctly and can catch refactor errors when editing the codebase.

```shell
(venv) ❯ mypy .
```

!!! info

    We currently exclude untyped calls for [Fileseq](https://github.com/justinfx/fileseq) and [websocket-client](https://github.com/websocket-client/websocket-client)  in [`pyproject.toml`](https://github.com/brunchstudio/pytvpaint/blob/main/pyproject.toml) with [`untyped_calls_exclude`](https://mypy.readthedocs.io/en/stable/config_file.html#untyped-definitions-and-calls)

### Documentation

The documentation is built using [MkDocs](https://www.mkdocs.org/) which is a static site generator that uses Markdown as the source format.

On top of that we use [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) which provides the Material look as well as some other nice features.

You can either run the development server or build the entire documentation:

```shell
# Will serve the doc on http://127.0.0.1:8000 with hot reload
(venv) ❯ mkdocs serve

# Build the doc as static files
(venv) ❯ mkdocs build
```

The [Python API documentation](https://brunchstudio.github.io/pytvpaint/api/objects/project/) is auto-generated from the docstrings in the code by using [mkdocstrings](https://mkdocstrings.github.io/). We use the [Google style](https://mkdocstrings.github.io/griffe/docstrings/#google-style) for docstrings.

For example:

```python
def tv_request(msg: str, confirm_text: str = "Yes", cancel_text: str = "No") -> bool:
    """Open a confirmation prompt with a message.

    Args:
        msg: the message to display
        confirm_text: the confirm button text. Defaults to "Yes".
        cancel_text: the cancel button text. Defaults to "No".

    Returns:
        bool: True if clicked on "Yes"
    """
    return bool(int(send_cmd("tv_Request", msg, confirm_text, cancel_text)))
```

### Unit tests

For the unit tests, we use [Pytest](https://docs.pytest.org/). Fixtures are located in the `conftest.py` file.

To run the tests you'll need an open TVPaint instance with the [tvpaint-rpc plugin](https://github.com/brunchstudio/tvpaint-rpc) installed.

To run them, use the following commands:

```shell
# Will run all the tests
(venv) ❯ pytest

# Run with verbosity enabled (use PYTVPAINT_LOG_LEVEL to DEBUG) to see George commands
(venv) ❯ pytest -v -s

# Only run specific tests with pattern matching
(venv) ❯ pytest -k test_tv_clip

# See the coverage statistics with pytest-cov
(venv) ❯ pytest --cov=pytvpaint
```
