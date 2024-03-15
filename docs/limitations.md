# Limitations

This page list all the current limitations of PyTVPaint in its current state.

## Windows only

As stated on the homepage, the [`tvpaint-rpc`](https://github.com/brunchstudio/tvpaint-rpc) C++ plugin is currently compiled for Windows only.

We are interested in making it available for Linux and MacOS, but since we only have Windows workstations we didn't have time to do it yet. If you want to contribute on this, please open an issue or do a pull request on the [plugin repository](https://github.com/brunchstudio/tvpaint-rpc/issues).

## Control characters in George results

This issue has been reported to TVPaint and is related to how the C++ SDK function `TVSendCmd` return and encode [control character](https://en.wikipedia.org/wiki/Control_character) values.

If we use the George command [`tv_projectheadernotes`](https://www.tvpaint.com/doc/tvpaint-animation-11/george-commands#tv_projectheadernotes) and the project notes text has some line break (`\n`), then the resulting characters in the result buffer are not encoded properly.

For example:

In the project notes:

```
aa
bb
cc
```

The result from `TVSendCmd`:

```console
['a', 'a', '\', 'n', 'b', 'b', '\', 'n', 'c', 'c' ]
```

This C++ code was used to print it:

```cpp
char george_result[2048];
int executionStatus = TVSendCmd(iFilter, payload.command.c_str(), george_result);

std::stringstream ss;
ss << "[";

int i = 0;
while (george_result[i]) {
    ss << "'" << george_result[i] << "', ";
    i += 1;
}

ss << "]";

spdlog::info(ss.str());
```

So we suppose that [control characters](https://en.wikipedia.org/wiki/Control_character) are not properly encoded.

Therefore, it is currently impossible to determine if it's actually an antislash followed by `n` or simply the line break character. (the case if there is a Windows path returns from any George function starting with `n` like `C:\Users\jhenry\new.tvpp`).

!!! Info

    We contacted the TVPaint technical support and they'll see what they can do to fix it in the future.

## Misbehaving George functions

Here is a list of the bugs/inconsistencies in the George commands:

| Method                                                                                | Description                                                                                                       |
| :------------------------------------------------------------------------------------ | :---------------------------------------------------------------------------------------------------------------- |
| [`tv_ratio`](api/george/project.md#pytvpaint.george.grg_project.tv_ratio)             | Always return an empty string (`""`)                                                                              |
| [`tv_instance_name`](api/george/layer.md#pytvpaint.george.grg_layer.tv_instance_name) | Crashes if we give a wrong `layer_id`                                                                             |
| `tv_camera_path`                                                                      | Confusing arguments and seemingly incorrect results (see [this](https://forum.tvpaint.com/viewtopic.php?t=15677)) |
