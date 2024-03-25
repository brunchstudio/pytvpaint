import pytest

from pytvpaint.project import Project
from pytvpaint.utils import restore_current_frame


@pytest.mark.parametrize("frame", [5, 2, 10])
def test_with_restore_current_frame(test_project_obj: Project, frame: int) -> None:
    frame = test_project_obj.current_frame
    with restore_current_frame(test_project_obj, frame):
        assert test_project_obj.current_frame == frame
