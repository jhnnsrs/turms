
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
