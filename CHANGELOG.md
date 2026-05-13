# Changelog

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