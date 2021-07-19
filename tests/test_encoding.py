from encoding import u256_to_u8s, u8s_to_u256
import pytest


@pytest.mark.parametrize("u256,u8s", (
    (1, (1, ) + (0, )*31),
    ((1 << 256) - 1, (255,) * 32),
    (1 << 248, (0, )*31 + (1, )),
))
def test_u256_and_u8s_conversion(u256, u8s):
    assert u256_to_u8s(u256) == u8s
    assert u8s_to_u256(u8s) == u256
