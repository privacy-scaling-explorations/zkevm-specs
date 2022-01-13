import pytest

from zkevm_specs.encoding import u256_to_u8s, U256
from zkevm_specs.opcode import check_slt, check_sgt
from common import NASTY_AB_VALUES

def gen_slt_sgt_witness(a: U256, b: U256, is_sgt: bool):
    a8s = u256_to_u8s(a)
    b8s = u256_to_u8s(b)
    result8s = [0] * 32

    (aa, aa8s) = (b, b8s) if is_sgt else (a, a8s)
    (bb, bb8s) = (a, a8s) if is_sgt else (b, b8s)

    # a < 0 and b >= 0
    if aa8s[0] >= 128 and bb8s[0] < 128:
        result8s[0] = 1
    # b < 0 and a >= 0
    elif bb8s[0] >= 128 and aa8s[0] < 128:
        result8s[0] = 0
    # (a >= 0 and b >= 0) or (a < 0 and b < 0)
    else:
        result8s[0] = int(aa < bb)

    return a8s, b8s, result8s

@pytest.mark.parametrize("a,b", NASTY_AB_VALUES)
def test_slt(a, b):
    a8s, b8s, result8s = gen_slt_sgt_witness(a, b, False)
    check_slt(a8s, b8s, result8s, False)

@pytest.mark.parametrize("a,b", NASTY_AB_VALUES)
def test_sgt(a, b):
    a8s, b8s, result8s = gen_slt_sgt_witness(a, b, True)
    check_sgt(a8s, b8s, result8s, True)
