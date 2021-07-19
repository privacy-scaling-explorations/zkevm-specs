from encoding import u256_to_u8s
import pytest


@pytest.mark.parametrize("test_input,expected", (
    (1, (1, ) + (0, )*31),
    ((1 << 256) - 1, (255,) * 32),

))
def test_u256_to_u8s(test_input, expected):
    assert u256_to_u8s(test_input) == expected
