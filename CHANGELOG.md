# Changelog

## [1.1.0] - 2024-05-13
### Features and Updates

* Improved parsing logic and added a new features to handle tvpaint not escaping characters
* Added option to set aliases in the dataclass fields to have more pythonic variable names
* Updated `Layer.render...` functions to use the parent clips render instead of `george.tv_save_image`
* Updated `render` functions to use `Fileseq.FrameSet` instead of a `(start, end)` this allows rendering of non consecutive ranges and makes range handling more streamlined.
* Improved `utils.get_tvp_element` functions and added searching `by_regex` as well
* Updated all tests for compatibility with tvpaint 12
* Improved documentation and fixed some typos
* Move project from `poetry` to `hatch`

### George

* Added dataclass `george.RGBAColor`
* Added function `george.tv_pick_color`
* Added warning to `george.tv_save_image` as it outputs low quality images
* added `to_extension` in SaveFormat

### Project

* Added Support for Guidelines in george functions and python classes
  * new module `george/grg_guidelines.py`
  * new module `guideline.py` with classes :
    * `guideline.GuidelineImage`
    * `guideline.GuidelineLine`
    * `guideline.GuidelineSegment`
    * `guideline.GuidelineCircle`
    * `guideline.GuidelineEllipse`
    * `guideline.GuidelineGrid`
    * `guideline.GuidelineMarks`
    * `guideline.GuidelineSafeArea`
    * `guideline.GuidelineFieldChart`
    * `guideline.GuidelineAnimatorField`
    * `guideline.GuidelineVanishPoint1`
    * `guideline.GuidelineVanishPoint2`
    * `guideline.GuidelineVanishPoint3`
* Added `Project.guidelines` and `Project.add_guideline_...` functions to `Project` class

### Scene

* Added new `Scene.split()` function to `Scene` based on the new function `tv_SceneSplit`.
* Added new george function `tv_SceneCreate`, however this functions doesn't seem to work for now, check bugs and breaking changes section.

### Clip

* Added `Clip.ctg_layers()` property to `Clip`.
* Added `Clip.folders()` property to `Clip`.
* Added `Clip.camera_layer()` property to `Clip`.
* Added `Clip.get_layers()` property to `Clip` which returns the clip's layers using filters (use this instead of `Clip.layers` when using TVP 12 or above) .Added `Clip.camera_layer()` property to `Clip`.
* [DEPRECATED] `Clip.layers()` is deprecated and only returns animation layers (this remains unchanged from before) and ignores all new Folder, Camera and CTG layers. Prefer `Clip.get_layers()` instead.
* Added support for new unescape logic to :
  * `Clip.action_text`
  * `Clip.dialog_text`
  * `Clip.note_text`
  * `Project.header_info`
  * `Project.author`
  * `Project.notes`

### Layers

* `tv_LayerMove` now takes a `folder_id` argument, more on this in the bugs sections.
* `tv_LayerCreate` now takes a `layer_type` argument to create a layer folder.
* Added new object `LayerFolder` which uses the new layer folder functions (e.g: `tv_LayerFolderDelete`).
* Added new `Layer.folder` property in `Layer`.
* Added new `Layer.set_folder_position` function in `Layer` though it is pretty finicky to use (check bugs and breaking changes section).
* Added new object `CameraLayer`.
* Added new object `CTGLayer`  which uses the new CTG layer functions :
  &#x20; \* `CTGLayer.squiggles_visible` / `tv_CTGSquigglesVisible`.
  &#x20; \* `CTGLayer.apply_changes` / `tv_CTGApplyChanges`.
  &#x20; \* `CTGLayer.sources` / `tv_CTGGetSource`.
  &#x20; \* `CTGLayer.add_sources` and `CTGLayer.remove_sources` / `tv_CTGSource`.
  &#x20; \* `CTGLayer.load_structure` / `tv_CTGLoadStructure`.
* Added new `Layer.is_ctg_layer` property in `Layer`.
* Added new `Layer.is_ctg_source` property in `Layer`.
* Added new `Layer.sourced_ctg_layers` property in `Layer`.
* Added `Layer.pan` function in `Layer`.
* Added `Layer.cut` , `Layer.copy`, and `Layer.paste` functions to the `Layer` class.
* Added `Layer.render_instances` function which only renders the instances in the layer not the whole sequence.

### Camera

* `Camera.get_point_data_at()` now returns a new read-only `InterpolationCameraPoint` object (inherited from `CameraPoint`).
* `Camera.get_point_data_at_frame()` now returns a new read-only `FrameCameraPoint` object (inherited from `CameraPoint`).
* `CameraPoint` object now has two new properties : `CameraPoint.width` and `CameraPoint.height`.

***

### Fixes

* fixed an issue with the values provided to `get_unique_name()`
* fixed `test_tv_clip_save_structure_json` file format
* fixed misc small bugs/typos

***

### TVPaint 12 Bugs and Breaking Changes

TVPaint 12 introduces a lot of welcome changes (especially for the artists) and some new needed functions for developers. 
However, it also introduces a lot of breaking changes and some new bugs.

To deal with these changes, as well as the new functions exclusive to TVPaint 12, we added a few decorators and functions :

| Method                                                                               | Description                                                                                              |
|:-------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------|
| [`min_version_compatible`](api/george/misc.md#pytvpaint.george.grg_base.min_version_compatible)    | When used as decorator, checks if the tvp instance making the call is above the miniumum version needed. |
| [`deprecated_warning`](api/george/misc.md#pytvpaint.george.grg_base.deprecated_warning) | When used as decorator, will log a warning message anytime the decorated function is called.             |
| [`is_tvp_version_below_12`](api/george/misc.md#pytvpaint.george.grg_base.is_tvp_version_below_12) | Returns True if the tvp instances version is below 12, False otherwise.                                  |


Below is also a list of the current breaking changes and bugs we noticed during development :

### George Documentation 
* George documentation is still not up to date and still contains many errors (seems stuck at some older TVP11 version), for now prefer the PyTVPaint documentation whenever possible.

### General 
* UI doesn't always update when values are set/updated via code, you either have to wait a few seconds for a refresh, or click somewhere else. This might lead to errors when users are using the UI at the same time.

### C++ Plugin 
* [BUG] plugin PIRF_HIDDEN_REQ and FILTERREQ_NO_TBAR don't seem to be working anymore, the plugin window is now visible and closing it kills the plugin with no way to restart it without restarting tvpaint.

### Project 
* [DEPRECATED/BREAKING] [`tv_ProjectInfo`](api/george/project.md#pytvpaint.george.grg_project.tv_project_info) values of `field_order` have been removed so for now we provide it ourselves.
* [BUG] [`tv_project_save_sequence`](api/george/project.md#pytvpaint.george.grg_project.tv_project_save_sequence) does not render empty instances even if they exist in the timeline.

### Scene 
* [BUG] [`tv_SceneCreate`](api/george/scene.md#pytvpaint.george.grg_scene.tv_scene_create) doesn't seem to work.

### Clip
* [BUG] [`tv_ClipSaveStructure`](api/george/clip.md#pytvpaint.george.grg_clip.tv_clip_save_structure_json) json %fi does not work for folder structure (in v11 and v12)
* [BUG] [`tv_ClipSaveStructure`](api/george/clip.md#pytvpaint.george.grg_clip.tv_clip_save_structure_json) json seems to output low quality images, this may use the same function `george.tv_save_image`.

### Layers 
* [ERROR] [`tv_CTGGetSources`](api/george/layer.md#pytvpaint.george.grg_layer.tv_ctg_get_source) is actually misspelled and is actually `tv_CTGGetSource` without the `s` at the end.
* [ERROR] [`tv_CTGGetSources`](api/george/layer.md#pytvpaint.george.grg_layer.tv_ctg_get_source) actually requires and returns layer Ids not names.
* Child layers have no way of knowing if they are in a folder layer or which one.
* A Folder layer has no way of knowing which layers are its children.
* [BUG] Creating a CTG layer from a folder crashes TVPaint.
* [BUG] Moving a layer that is already in a folder in the same folder crashes TVPaint.
* `tv_LayerMove` can now move layers into folders but the position is relative to the root and not the folder, this is not ideal, since we can't know if a layer is already in a folder or not, which adds a lot of uncertainty when moving layers in and out of folders.
* Not providing a `FolderID` to `tv_LayerMove` doesn't move the layer to the root, you just need to move outside the folder range for it to work, which again is pretty tough to do since we can't get the child layers of a folder and therefore their positions.
* Moving a layer inside a folder can be done without providing a `FolderID`, just by moving the layer in the folder's range.
* [BUG] CTG layer sometimes takes a while to update in the UI (a few seconds), which means they can be unintentionally edited or reset before the update.
* CameraLayer is not really a layer and most layer functions will ignore it, prefer use of PyTVPaint `Camera` object instead.
* [BUG] Selecting the Camera Layer in the UI now disables/grays out most layer related tools (this is a new behavior), this causes a lot of errors when using pipeline tools or TVPaint panels as TVPaint now raises an error messages anytime you try to use a tool that is not camera related when the camera layer is selected.
* [BUG] `tv_LayerRename` does not work in TVP12 and will replace the name with an empty string, this is either a new bug or there is now a new argument that is needed but not documented.
* [BREAKING] default layers name is now `Anim_X` and when these layers are queried for their names they return an empty string.
* [BUG] `tv_layer_move` still sets position at (value-1) when value is superior to 0.
* [BUG] `tv_preserve_set` does not seem to work in TVP12
* [BUG] `tv_LayerColor setcolor` will fail when the `name` argument is provided.
* [BUG] `tv_LayerColor setcolor` no longer returns -1 when given a bad color index.
* [BUG] `tv_layer_move` no longer returns -1 when given a bad position.
* [BUG] `tv_LayerCreate`  should not be used when an empty string as it will consider the new variable `layer_type` as the name.
* [BUG] Many layer functions that used to return -1 when given a bad layer id or position no longer do so, this can lead to silent errors and breaking behavior, this also breaks any way to check/validate these functions return values. The functions are :
    * `tv_layer_set`
    * `tv_LayerSelection`
    * `tv_layer_kill`
    * `tv_LayerBlendingMode`
    * `tv_LayerStencil`
    * `tv_LayerPreBehavior`
    * `tv_LayerPostBehavior`
    * `tv_LayerLockPosition`
    * `tv_LayerMarkSet`

### Camera 
* [DEPRECATED/BREAKING] [`Camera.anti_aliasing`](api/objects/camera.md#pytvpaint.camera.Camera.anti_aliasing) no longer returns anti_aliasing, for now it always returns 1.
* [DEPRECATED/BREAKING] [`Camera.fps`](api/objects/camera.md#pytvpaint.camera.Camera.fps) no longer returns/sets fps, now only fps is Project fps.
* [BUG] Most Camera values can still be edited/queried using [`tv_CameraInfo`](api/george/camera.md#pytvpaint.george.grg_camera.tv_camera_info_get) but they are not immediately reflected in the
  UI, and so they can be unintentionally edited or reset.
* [DEPRECATED/BREAKING] [`tv_CameraInfo`](api/george/camera.md#pytvpaint.george.grg_camera.tv_camera_info_get) values of pixel aspect ratio and fps have been "swapped" (since camera fps is no longer provided).
* [BUG] [`tv_CameraInterpolation`](api/george/camera.md#pytvpaint.george.grg_camera.tv_camera_interpolation) doesn't work properly in TVP12 and always returns an "empty" point.

### Guidelines
* `tv_GuidelineModify "marks"` doesn't seem to work, values are never changed, added function with a warning.

---

## [1.0.2] - 2024-10-02
### Fixes
* FIX save_dependencies functions #14

---

## [1.0.1] - 2024-09-16
### Fixes
* HOTFIX tv_save_sequence range handling

---

## [1.0.0] - 2024-06-21
### Added
* Releasing first production version after successful use in projects at Brunch Studio

---

## [1.0.0b9] - 2024-05-28
### Fixes
* FIX tv_load_sequence/tv_load_image always stretching loaded media

### Features/Updates
* UPDATE default values for functions :
  * grg_clip.tv_load_sequence
  * grg_clip.tv_sound_clip_adjust
  * grg_layer.tv_load_image
  * grg_project.tv_load_project
  * grg_project.tv_project_save_sequence
  * grg_project.tv_frame_rate_project_set
  * grg_project.tv_sound_project_adjust

---

## [1.0.0b8] - 2024-05-22
### Features/Updates
* UPDATE george.grg_clip.tv_clip_save_structure_json default values and param names

### Fixes
* FIX Layer.new_background_layer not working when providing an image to set

---

## [1.0.0b7] - 2024-04-30
### Features/Updates
* UPDATE clip json export to handle all options (fill_bakcground, all_images, etc...)
* [BREAKING CHANGES] UPDATE tv_clip_save_structure_json default values

---

## [1.0.0b6] - 2024-04-22
### Features/Updates
* Updated documentation
* Added new functions in Layer class : render and render_instances
* Clamp values for position to minimum 0
* Updated `get_` functions in classes to return None instead of raising an error when element not found
* Update tests
* [BREAKING CHANGES] Updated function signatures and default values for:
  * Clip.load_media
  * Clip.render
  * Clip.export_json
  * Clip.export_psd
  * Clip.export_csv
  * Clip.export_sprites
  * Clip.export_flix
  * Clip.set_layer_color
  * Layer.render_frame
  * Project.render
  * Project.render_clips

### Fixes
* Fix layer position not setting position 0 correctly
* Fix mark_in/mark_out not set correctly

---

## [1.0.0b5] - 2024-04-02
### Fixes
* FIX client auto-connect not working properly
* FIX background colors set in Project class

---

## [1.0.0b4] - 2024-03-28
### Features/Updates
* Change `tv_background_set` George function signature to accepts a single color argument of type `tuple[RGBColor, RGBColor] | RGBColor | None` to be coherent with `tv_background_get`. #9

---

## [1.0.0b3] - 2024-03-27
### Added
* ADD background mode option in render functions
* UPDATE background mode and color functions in API

### Fixes
* FIX render context setting save mode instead of alpha mode