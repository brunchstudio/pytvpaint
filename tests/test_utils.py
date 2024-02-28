import pytest
from pytvpaint.utils import get_unique_name


@pytest.mark.parametrize(
    "test_case",
    [
        (["cl001"], "cl", "cl002"),
        (["cl"], "cl", "cl2"),
        (["a01", "a001"], "a", "a002"),
        (["a001"], "a001b", "a001b"),
        (["a001"], "a001", "a002"),
        (["cl001", "cl005"], "cl", "cl006"),
        (["001", "003"], "003", "004"),
        (["l"], "tset0", "tset0"),
        ([], "tset0", "tset0"),
        (["cl0001", "cl005"], "cl", "cl0006"),
    ],
)
def test_get_unique_name(test_case: tuple[list[str], str, str]) -> None:
    current_names, name, expected = test_case
    assert get_unique_name(current_names, name) == expected
