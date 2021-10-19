import pytest

from zkevm_specs.encoding import u256_to_u8s, U256
from zkevm_specs.opcode import check_lt, check_gt
from zkevm_specs.opcode.stack import Stack
from common import NASTY_AB_VALUES

def gen_lt_gt_witness(a: U256, b: U256, is_gt: bool):
    a8s = u256_to_u8s(a)
    b8s = u256_to_u8s(b)
    result8s = [0] * 32

    swap = True if is_gt else False
    aa = b if swap else a
    bb = a if swap else b
    c = bb - aa
    if c < 0:
        c += 1 << 256
        result8s[0] = 0
    elif c == 0:
        result8s[0] = 0
    else:
        result8s[0] = 1
    c8s = u256_to_u8s(c)

    aa_low128 = aa % (1<<128)
    bb_low128 = bb % (1<<128)
    carry = True if bb_low128 - aa_low128 < 0 else False
    return a8s, b8s, result8s, c8s, swap, carry


@pytest.mark.parametrize("a,b", NASTY_AB_VALUES)
def test_lt(a, b):
    a8s, b8s, result8s, c8s, swap, carry = gen_lt_gt_witness(a, b, False)
    check_lt(a8s, b8s, result8s, c8s, swap, carry)
    assert int(a < b) == result8s[0]


@pytest.mark.parametrize("a,b", NASTY_AB_VALUES)
def test_gt(a, b):
    a8s, b8s, result8s, c8s, swap, carry = gen_lt_gt_witness(a, b, True)
    assert int(a > b) == result8s[0]
    check_gt(a8s, b8s, result8s, c8s, swap, carry)
