import pytest

from zkevm_specs.encoding import u256_to_u8s, u8s_to_u256
from zkevm_specs.opcode import check_add, SignTable, compare
from common import NASTY_AB_VALUES


@pytest.mark.parametrize("a,b", NASTY_AB_VALUES)
def test_add(a, b):
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
    check_add(a8s, b8s, sum8s, False, carry32)

    # Check if the witness works
    sum256 = u8s_to_u256(sum8s)
    assert a + b == sum256 + (carry32[-1] << 256)


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
