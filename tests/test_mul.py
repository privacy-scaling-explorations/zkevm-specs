from typing import Sequence, List

import pytest

from src.zkevm_specs.encoding import u256_to_u8s, U64, U256, U8, u8s_to_u64s, u256_to_u64s
from src.zkevm_specs.opcode.mul import check_mul
from tests.common import NASTY_AB_VALUES


@pytest.mark.parametrize("a,b", NASTY_AB_VALUES)
def test_mul(a, b):
    # a = 452312848583677764537270546931827317263716268236872901646775034247878017024
    # b = 452312848688580287004445910143864716245535269665800179039870280078379188225
    c = a * b % (2 ** 256)
    a8s = u256_to_u8s(U256(a))
    b8s = u256_to_u8s(U256(b))
    c8s = u256_to_u8s(U256(c))
    print()
    print("a8s:", a8s)
    print("b8s:", b8s)
    print("c8s:", c8s)
    a64s = u8s_to_u64s(a8s)
    b64s = u8s_to_u64s(b8s)
    c64s = u8s_to_u64s(c8s)
    print("a64s:", a64s)
    print("b64s:", b64s)
    print("c64s:", c64s)
    # t0 t1 t2 t3
    t = [U256(0)] * 4
    for total_idx in range(4):
        rhs_sum = U256(0)
        for a_id in range(0, total_idx + 1):
            a_idx, b_idx = a_id, total_idx - a_id
            if len(a64s) >= a_idx + 1:
                tmp_a = a64s[a_idx]
            else:
                tmp_a = 0
            if len(b64s) >= b_idx + 1:
                tmp_b = b64s[b_idx]
            else:
                tmp_b = 0
            t[total_idx] += tmp_a * tmp_b

    print("t0:", t[0])
    print("t1:", t[1])
    print("t2:", t[2])
    print("t3:", t[3])
    # v0, v1
    v = [U256(0)] * 2
    v[0] = U256((t[0] + t[1] * (2 ** 64) - c64s[0] - c64s[1] * (2 ** 64)) // (2 ** 128))
    v[1] = U256((v[0] + t[2] + t[3] * (2 ** 64) - c64s[2] - c64s[3] * (2 ** 64)) // (2 ** 128))
    print("v0:", v[0])
    print("v1:", v[1])

    assert 0 <= v[0] <= (2 ** 66)
    assert 0 <= v[1] <= (2 ** 66)

    check_mul(a8s, b8s, c8s, t[0], t[1], t[2], t[3], v[0], v[1])

