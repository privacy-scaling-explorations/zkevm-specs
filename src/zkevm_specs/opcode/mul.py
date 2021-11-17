from typing import Sequence

from ..encoding import U8, is_circuit_code, U256, u8s_to_u64s


def mul_common(
        a8s: Sequence[U8],
        x8s: Sequence[U8],
        y8s: Sequence[U8],
        t0: U256,
        t1: U256,
        t2: U256,
        t3: U256,
        v0: U256,
        v1: U256
):
    assert len(a8s) == len(x8s) == len(y8s) == 32
    a64s = u8s_to_u64s(a8s)
    x64s = u8s_to_u64s(x8s)
    y64s = u8s_to_u64s(y8s)
    cir_t = [U256(0)] * 4
    for total_idx in range(4):
        for a_id in range(0, total_idx + 1):
            a_idx, x_idx = a_id, total_idx - a_id
            if len(a64s) >= a_idx + 1:
                tmp_a = a64s[a_idx]
            else:
                tmp_a = 0
            if len(x64s) >= x_idx + 1:
                tmp_x = x64s[x_idx]
            else:
                tmp_x = 0
            cir_t[total_idx] += tmp_a * tmp_x

    
    assert t0 == cir_t[0]
    assert t1 == cir_t[1]
    assert t2 == cir_t[2]
    assert t3 == cir_t[3]
    assert v0 * (2 ** 128) == cir_t[0] + cir_t[1] * (2 ** 64) - y64s[0] - y64s[1] * (2 ** 64)
    assert v1 * (2 ** 128) == v0 + cir_t[2] + cir_t[3] * (2 ** 64) - y64s[2] - y64s[3] * (2 ** 64)

@is_circuit_code
def check_mul(a8s, b8s, c8s, t0, t1, t2, t3, v0, v1):
    mul_common(a8s, b8s, c8s, t0, t1, t2, t3, v0, v1)
