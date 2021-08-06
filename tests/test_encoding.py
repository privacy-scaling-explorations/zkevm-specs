from encoding import u256_to_u8s, u8s_to_u256, compare, SignTable, check_add, check_commitment, RangeTable, commit
import pytest


@pytest.mark.parametrize("u256,u8s", (
    (1, (1, ) + (0, )*31),
    ((1 << 256) - 1, (255,) * 32),
    (1 << 248, (0, )*31 + (1, )),
))
def test_u256_and_u8s_conversion(u256, u8s):
    assert u256_to_u8s(u256) == u8s
    assert u8s_to_u256(u8s) == u256


def test_table_sizes():
    assert len(SignTable()) == 2**18 - 1
    assert len(RangeTable()) == 2**16


@pytest.mark.parametrize("u256", (
    1,
    2,
    511,
    5566,
    (1 << 256) - 1,
    1 << 248,
))
def test_check_commitment(u256):
    range_table = RangeTable()
    random = 5566
    x8s, commitment = commit(u256, random)
    check_commitment(x8s, commitment, random, range_table)


NASTY_AB_VALUES = (
    (0, 0),
    (1, 0),
    (0, 1),
    (1, 1),
    (255, 0),
    (0, 255),
    (255, 255),
    (256, 0),
    (0, 256),
    (256, 256),
    (260, 513),
    (65535, 0),
    (0, 65535),
    (65535, 65535),
    (65536, 0),
    (0, 65536),
    (65536, 65536),
    ((1 << 256) - 1, (1 << 256) - 2),
    ((1 << 256) - 2, (1 << 256) - 1)
)


@pytest.mark.parametrize("a,b", NASTY_AB_VALUES)
def test_comparator(a, b):
    a8s = u256_to_u8s(a)
    b8s = u256_to_u8s(b)
    sign_table = SignTable()
    result = [0]*17
    for i in reversed(range(0, 32, 2)):
        a16 = a8s[i] + 256 * a8s[i + 1]
        b16 = b8s[i] + 256 * b8s[i + 1]
        _sum = a16 - b16 + 2**16 * result[i//2+1]
        result[i//2] = (_sum > 0) - (_sum < 0)

    result = result[:16]

    sign = compare(a8s, b8s, result, sign_table)
    if a > b:
        assert sign == 1
    elif a == b:
        assert sign == 0
    else:
        assert sign == -1


@pytest.mark.parametrize("a,b", NASTY_AB_VALUES)
def test_addition(a, b):
    a8s = u256_to_u8s(a)
    b8s = u256_to_u8s(b)
    carry33 = [0] * 33
    sum8s = [0] * 32
    for i in range(32):
        sum9 = a8s[i] + b8s[i] + carry33[i]
        sum8s[i] = sum9 % 256
        carry33[i + 1] = sum9 // 256

    carry32 = carry33[1:]

    # Check if the circuit works
    check_add(a8s, b8s, sum8s, carry32)

    # Check if the witness works
    sum256 = u8s_to_u256(sum8s)
    assert a + b == sum256 + (carry32[-1] << 256)
