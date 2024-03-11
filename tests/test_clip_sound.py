import pytest

from pytvpaint.george.exceptions import GeorgeError
from pytvpaint.sound import ClipSound


def test_clip_sound_init(test_clip_sound: ClipSound) -> None:
    assert ClipSound(test_clip_sound.track_index) == test_clip_sound


def test_clip_sound_remove(test_clip_sound: ClipSound) -> None:
    index = test_clip_sound.track_index
    test_clip_sound.remove()

    with pytest.raises(GeorgeError):
        ClipSound(track_index=index)


@pytest.mark.skip("tv_sound_clip_reload doesn't work properly")
def test_clip_sound_reload(test_clip_sound: ClipSound) -> None:
    test_clip_sound.reload()
