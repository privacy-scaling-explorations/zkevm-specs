from typing import Sequence, List

import pytest

from zkevm_specs.encoding import u256_to_u8s, U256, u8s_to_u64s
from zkevm_specs.opcode.mul import check_mul
from common import NASTY_AB_VALUES


@pytest.mark.parametrize("a,b", NASTY_AB_VALUES)
def test_mul(a, b):
    c = a * b % (2**256)
    a8s = u256_to_u8s(U256(a))
    b8s = u256_to_u8s(U256(b))
    c8s = u256_to_u8s(U256(c))
    a64s = u8s_to_u64s(a8s)
    b64s = u8s_to_u64s(b8s)
    c64s = u8s_to_u64s(c8s)
    # t0 t1 t2 t3
    t = [U256(0)] * 4
    for total_idx in range(4):
        rhs_sum = U256(0)
        for a_id in range(0, total_idx + 1):
            a_idx, b_idx = a_id, total_idx - a_id
            tmp_a = a64s[a_idx] if len(a64s) >= a_idx + 1 else 0
            tmp_b = b64s[b_idx] if len(b64s) >= b_idx + 1 else 0
            t[total_idx] += tmp_a * tmp_b

    # v0, v1
    v = [U256(0)] * 2
    v[0] = U256((t[0] + t[1] * (2**64) - c64s[0] - c64s[1] * (2**64)) // (2**128))
    v[1] = U256((v[0] + t[2] + t[3] * (2**64) - c64s[2] - c64s[3] * (2**64)) // (2**128))
    assert 0 <= v[0] <= (2**66)
    assert 0 <= v[1] <= (2**66)

    v0 = u256_to_u8s(v[0])[:9]
    v1 = u256_to_u8s(v[1])[:9]

    check_mul(a8s, b8s, c8s, v0, v1)
