import pytest
from pytvpaint.george.exceptions import GeorgeError
from pytvpaint.sound import ProjectSound


def test_project_sound_init(test_project_sound: ProjectSound) -> None:
    assert ProjectSound(track_index=0) == test_project_sound


def test_project_sound_remove(test_project_sound: ProjectSound) -> None:
    index = test_project_sound.track_index
    test_project_sound.remove()

    # The project sound doesn't exist anymore
    with pytest.raises(GeorgeError):
        ProjectSound(track_index=index)


def test_project_sound_reload(test_project_sound: ProjectSound) -> None:
    test_project_sound.reload()
