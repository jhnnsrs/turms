from tests.utils import build_relative_glob
from turms.processors.merge import merge_code, MergeProcessorConfig

with open(build_relative_glob("/merge_pairs/old.py"), "r") as f:
    old_code = f.read()

with open(build_relative_glob("/merge_pairs/new.py"), "r") as f:
    new_code = f.read()

result = merge_code(old_code, new_code, MergeProcessorConfig())
assert result

with open(build_relative_glob("/merge_pairs/updated.py"), "w") as f:
    f.write(result)
