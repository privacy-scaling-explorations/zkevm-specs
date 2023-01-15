import pytest

from zkevm_specs.encoding import (
    u256_to_u8s,
    u8s_to_u256,
    check_commitment,
    RangeTable,
    SignTable,
    commit,
)


@pytest.mark.parametrize(
    "u256,u8s",
    (
        (1, (1,) + (0,) * 31),
        ((1 << 256) - 1, (255,) * 32),
        (1 << 248, (0,) * 31 + (1,)),
    ),
)
def test_u256_and_u8s_conversion(u256, u8s):
    assert u256_to_u8s(u256) == u8s
    assert u8s_to_u256(u8s) == u256


def test_table_sizes():
    assert len(SignTable()) == 2**18 - 1
    assert len(RangeTable()) == 2**16


@pytest.mark.parametrize(
    "u256",
    (
        1,
        2,
        511,
        5566,
        (1 << 256) - 1,
        1 << 248,
    ),
)
def test_check_commitment(u256):
    range_table = RangeTable()
    random = 5566
    x8s, commitment = commit(u256, random)
    check_commitment(x8s, commitment, random, range_table)
