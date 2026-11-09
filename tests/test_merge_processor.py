
from .utils import build_relative_glob
from turms.processors.merge import merge_code, MergeProcessorConfig


def test_merge_code():
    """Tests the merge_code function"""

    with open(build_relative_glob("/merge_pairs/old.py"), "r") as f:
        old_code = f.read()

    with open(build_relative_glob("/merge_pairs/new.py"), "r") as f:
        new_code = f.read()

    result = merge_code(old_code, new_code, MergeProcessorConfig())

    with open(build_relative_glob("/merge_pairs/updated.py"), "r") as f:
        new_code = f.read()
    assert (
        result == new_code
    ), "The merge_code function did not merge the code correctly"


def test_merge_code_preserves_hand_added_decorator_keywords():
    """Decorator keyword arguments with no schema representation (e.g. Strawberry's
    `permission_classes`/`extensions`) have no way to be regenerated, so a merge must
    preserve them from the existing file - only keywords present in the freshly
    generated decorator (e.g. `description`) should be allowed to update."""

    with open(build_relative_glob("/merge_pairs/decorator_old.py"), "r") as f:
        old_code = f.read()

    with open(build_relative_glob("/merge_pairs/decorator_new.py"), "r") as f:
        new_code = f.read()

    result = merge_code(old_code, new_code, MergeProcessorConfig())

    with open(build_relative_glob("/merge_pairs/decorator_updated.py"), "r") as f:
        expected_code = f.read()
    assert (
        result == expected_code
    ), "The merge_code function did not preserve hand-added decorator keywords"
