from turms.processors.merge import MergeProcessorConfig, merge_code

from .utils import build_relative_glob


def test_merge_code():
    """Tests the merge_code function"""

    with open(build_relative_glob("/merge_pairs/old.py")) as f:
        old_code = f.read()

    with open(build_relative_glob("/merge_pairs/new.py")) as f:
        new_code = f.read()

    result = merge_code(old_code, new_code, MergeProcessorConfig())

    with open(build_relative_glob("/merge_pairs/updated.py")) as f:
        new_code = f.read()
    assert result == new_code, (
        "The merge_code function did not merge the code correctly"
    )
