# Limitations

This page list all the current limitations of PyTVPaint in its current state.

## Windows only

As stated on the homepage, the [`tvpaint-rpc`](https://github.com/brunchstudio/tvpaint-rpc) C++ plugin is currently compiled for Windows only.

We are interested in making it available for Linux and MacOS, but being a Windows Studio we have not needed nor had 
time to do so yet. If you want to contribute on this, please open an issue or a pull request on the [plugin repository](https://github.com/brunchstudio/tvpaint-rpc/issues).

## TVPaint 11.5+

TVPaint 11.5 is minimum supported version simply because we does currently have an older version of TVPaint. The TVPaint 
SDK is what really limits the compatibility, but we suspect PyTVPaint is also compatible with TVPaint 11 since the SDK 
hasn't changed in a while. If you have a version of TVPaint prior to 11.5 and want to test to the API, please let us 
know it works and we will update the minimum requirements for teh plugin and API. 

## Control characters in George results

This issue has been reported to TVPaint and is related to how the C++ SDK function `TVSendCmd` returns and encodes [control character](https://en.wikipedia.org/wiki/Control_character) values.

If we use the George command [`tv_projectheadernotes`](https://www.tvpaint.com/doc/tvpaint-animation-11/george-commands#tv_projectheadernotes) for instance and the project notes text has some line breaks (`\n`), then the characters in the result buffer are not encoded properly.

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

Therefore, it is currently impossible to determine if it's actually a backslash `\` followed by `n` or simply the line 
break character. SO PyTVPaint leaves these characters as is.

!!! Info

    The TVPaint dev team have been made aware of the issue, and we are hopeful that it will be fixed in the future.

## George Official Documentation and Naming Convention Issues

Many functions in the official George documentation are poorly described or have the wrong description all together, 
many are overly complex and some don't work at all. Some functions also have misleading names, with some 
"layer" functions actually impacting the clip and not the layer for instance. 

We tried to fix as many of these issues as we could when wrapping functions, putting the functions in the appropriate 
module when possible. We advise using our documentation for all wrapped functions instead of the official one as 
PyTVPaint's documentation is usually more accurate.


## Misbehaving George functions

We will try to keep a list of the bugs/inconsistencies we encountered with any George commands, and describe the 
issues in the table below:

| Method                                                                               | Description                                                                                                                       |
|:-------------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------|
| [`tv_Ratio`](api/george/project.md#pytvpaint.george.grg_project.tv_ratio)            | Always returns an empty string (`""`)                                                                                             |
| [`tv_InstanceName`](api/george/layer.md#pytvpaint.george.grg_layer.tv_instance_name) | Crashes if we provided with an invalid `layer_id`                                                                                 |
| `tv_CameraPath`                                                                      | Confusing arguments and seemingly incorrect results (see [this](https://forum.tvpaint.com/viewtopic.php?t=15677))                 |
| `tv_SoundClipReload`                                                                 | Doesn't accept a proper clip id, only `0` seems to work for the current clip                                                      |
| `tv_LayerSelectInfo`                                                                 | Does not select frames as stated in the documentation and will also return non selected frames if attribute `full` is set to True |
