name = "pytvpaint"
version = "__BRUNCH_BUILD_VERSION__"
timestamp = 00000000


requires = [
    "python-3",
    "py_tools",
    "tvpaint",
]


def commands(env):
    env.PYTHONPATH.append("{root}/python")
    env.PYTVPAINT_WS_HOST = "ws://localhost"
    env.PYTVPAINT_WS_PORT = "3000"
    env.PYTVPAINT_WS_TIMEOUT = "30"


build_command = "python -m brunch_rez_build"
build_requires = ["ci"]

tests = {
    "py37": {
        "command": "python -m pytest {root}/tests",
        "requires": ["testing_tools", "python-3.7"],
    },
    "py39": {
        "command": "python -m pytest {root}/tests",
        "requires": ["testing_tools", "python-3.9"],
    },
    "py310": {
        "command": "python -m pytest {root}/tests",
        "requires": ["testing_tools", "python-3.10"],
    },
    "py311": {
        "command": "python -m pytest {root}/tests",
        "requires": ["testing_tools", "python-3.11"],
    },
}
