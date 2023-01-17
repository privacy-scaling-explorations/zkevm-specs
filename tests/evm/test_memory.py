import pytest

from zkevm_specs.util import rand_fq

TESTING_DATA = ()

@pytest.mark.parametrize("offset, value", TESTING_DATA)
def test_memory(offset: int, value: int):
    randomness = rand_fq()