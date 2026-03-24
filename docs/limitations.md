# Limitations

This page list all the current limitations of PyTVPaint in its current state.

## Windows only

As stated on the homepage, the [`tvpaint-rpc`](https://github.com/brunchstudio/tvpaint-rpc) C++ plugin is currently compiled for Windows only.

We are interested in making it available for Linux and MacOS, but being a Windows first Studio we have not needed nor had 
time to do so yet. If you want to contribute on this, please open an issue or a pull request on the [plugin repository](https://github.com/brunchstudio/tvpaint-rpc/issues).

## TVPaint 11.5+

TVPaint 11.5 is minimum supported version simply because we currently do not have an older version of TVPaint. The TVPaint 
SDK is what really limits the compatibility, but we suspect PyTVPaint is also compatible with TVPaint 11 (and perhaps even 10) since the SDK 
hasn't changed in a while. If you have a version of TVPaint prior to 11.5 and want to test the API, please let us 
know if it works and we will update the minimum requirements for the plugin and API. 

## Control characters in George results

!!! Info

    The latest version of PyTVPaint tries to fix this via our API, it works 90% of the time but there are still some edge cases that cannot be resolved.

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

| Method                                                                               | Description                                                                                                                                                                |
|:-------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`tv_Ratio`](api/george/project.md#pytvpaint.george.grg_project.tv_ratio)            | Always returns an empty string (`""`)                                                                                                                                      |
| [`tv_InstanceName`](api/george/layer.md#pytvpaint.george.grg_layer.tv_instance_name) | Crashes if we provided with an invalid `layer_id`                                                                                                                          |
| `tv_CameraEnumPoints`                                                                      | Only returns the first point, no matter how many points there are.                                                                                                         |
| `tv_CameraPath`                                                                      | Confusing arguments and seemingly incorrect results (see [this](https://forum.tvpaint.com/viewtopic.php?t=15677))                                                          |
| `tv_SoundClipReload`                                                                 | Doesn't accept a proper clip id, only `0` seems to work for the current clip                                                                                               |
| `tv_LayerSelectInfo`                                                                 | Does not select frames as stated in the documentation and will also return non selected frames if attribute `full` is set to True                                          |
| `tv_ProjectSaveAudioDependencies` and `tv_ProjectSaveVideoDependencies`                                                | Missing arguments in documentation rendering the function useless, thankfully someone provided the correct details [here](http://tvpaint.net/forum/viewtopic.php?p=136709) |


## TVPaint 12 Bugs and Breaking Changes

TVPaint 12 introduces a lot of welcome changes (especially for the artists) and some new needed function for 
developers. However, it also introduces a lot of breaking changes and some new bugs. 

To deal with these changes as well as the new functions exclusive to TVP 12, we added a couple decorators and helper functions : 

| Method                                                                               | Description                                                                                              |
|:-------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------|
| [`min_version_compatible`](api/george/misc.md#pytvpaint.george.grg_base.min_version_compatible)    | When used as decorator, checks if the tvp instance making the call is above the miniumum version needed. |
| [`deprecated_warning`](api/george/misc.md#pytvpaint.george.grg_base.deprecated_warning) | When used as decorator, will log a warning message anytime the decorated function is called.             |
| [`is_tvp_version_below_12`](api/george/misc.md#pytvpaint.george.grg_base.is_tvp_version_below_12) | Returns True if the tvp instances version is below 12, False otherwise.                                  |


Below is also a list of the current breaking changes and bugs we noticed during development

### C++ Plugin :
* [BUG] plugin PIRF_HIDDEN_REQ doesn't seem to be working anymore, the plugin window is now visible and closing it kills the plugin with no way to restart it without restarting tvpaint.

### Project :
* [DEPRECATED/BREAKING] [`tv_ProjectInfo`](api/george/project.md#pytvpaint.george.grg_project.tv_project_info) values of `field_order` have been removed so for now we provide it ourselves.

### Scene :
* [BUG] [`tv_SceneCreate`](api/george/scene.md#pytvpaint.george.grg_scene.tv_scene_create) doesn't seem to work.

### Layers :
* [ERROR] [`tv_CTGGetSources`](api/george/layer.md#pytvpaint.george.grg_layer.tv_ctg_get_source) is actually misspelled and is actually `tv_CTGGetSource` without the `s` at the end.
* [ERROR] [`tv_CTGGetSources`](api/george/layer.md#pytvpaint.george.grg_layer.tv_ctg_get_source) actually requires and returns layer Ids not names.
* [FEATURE] Some function now return a clear error message which is much appreciated (Ex: [`tv_CTGSource`](api/george/layer.md#pytvpaint.george.grg_layer.tv_ctg_source_add))
* child layers have no way of knowing if they are in a folder layer or which one.
* Folder layer has no way of knowing which layers are inside the folder.
* [BUG] Creating a CTG layer from a folder crashes TVPaint.
* [BUG] Moving a layer that is already in a folder in the same folder crashes TVPaint.
* [`tv_LayerMove`](api/george/layer.md#pytvpaint.george.grg_layer.tv_layer_move) can now move layers into folders but the position is relative to the root and not the folder, 
 this is not ideal, since we can't know if a layer is already in a folder or not, which adds a lot of uncertainty when moving layers.
* Not providing a `FolderID` to [`tv_LayerMove`](api/george/layer.md#pytvpaint.george.grg_layer.tv_layer_move) doesn't 
 move the layer to the root, you just need to move outside the folder range for it to work, which again is pretty tough to do since we can't get the child layers of a folder and therefore their positions.
* Moving a layer inside a folder can be done without providing a `FolderID`, just by moving the layer in the folder's range.
* [BUG] UI doesn't always update when values are set/updated via code, you either have to wait a few seconds for a refresh, or click somewhere else, this might lead to errors when users are using the UI at the same time.
* [BUG] CTG layer sometimes takes a while to update in the UI (a few seconds), which means they can be unintentionally edited or reset before the update.
* CameraLayer is not really a layer and most layer functions will ignore it, prefer use of PyTVPaint [`Camera`](api/objects/camera.md#pytvpaint.camera.Camera) object instead.
* [BUG] Selecting the Camera Layer in the UI now disables/grays out most layer related tools (this is a new behaviour), this causes a lot of errors when using pipeline tools or 
 TVPaint panels as TVPaint now raises an error prompt/message anytime you try to use a tool that is not camera related when the camera layer is selected.

### Camera :
* [DEPRECATED/BREAKING] Camera.anti_aliasing always returns 1
* [DEPRECATED/BREAKING] [`Camera.fps`](api/objects/camera.md#pytvpaint.camera.Camera.fps) no longer returns/sets fps, now only fps is Project fps.
* [BUG] Most Camera values can still be edited/queried using [`tv_CameraInfo`](api/george/camera.md#pytvpaint.george.grg_camera.tv_camera_info_get) but they are not immediately reflected in the
  UI, and so they can be unintentionally edited or reset.
* [DEPRECATED/BREAKING] [`tv_CameraInfo`](api/george/camera.md#pytvpaint.george.grg_camera.tv_camera_info_get) values of pixel aspect ratio and fps have been "swapped" (since camera fps is no longer provided).
* [BUG] [`tv_CameraInterpolation`](api/george/camera.md#pytvpaint.george.grg_camera.tv_camera_interpolation) doesn't work properly in TVP12 and always returns an "empty" point.

