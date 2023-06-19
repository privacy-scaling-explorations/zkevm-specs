import pytest

# This will make pytest rewrite the asserts in `src/zkevm_specs/` so that they
# print the values used in the assertions automatically.
pytest.register_assert_rewrite("zkevm_specs")
