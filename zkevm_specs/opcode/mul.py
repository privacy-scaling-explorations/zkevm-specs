from typing import Sequence

from ..encoding import U8, is_circuit_code, U256, u8s_to_u64s


def mul_common(
    a8s: Sequence[U8],
    x8s: Sequence[U8],
    y8s: Sequence[U8],
    v0: Sequence[U8],
    v1: Sequence[U8],
):
    assert len(a8s) == len(x8s) == len(y8s) == 32
    assert len(v0) == len(v1) == 9
    a64s = u8s_to_u64s(a8s)
    x64s = u8s_to_u64s(x8s)
    y64s = u8s_to_u64s(y8s)

    v0m = U256(0)
    v1m = U256(0)
    for i, u8 in enumerate(v0):
        assert 0 <= u8 <= 255
        v0m += u8 * (2 ** (8 * i))

    for i, u8 in enumerate(v1):
        assert 0 <= u8 <= 255
        v1m += u8 * (2 ** (8 * i))

    t0 = a64s[0] * x64s[0]
    t1 = a64s[0] * x64s[1] + a64s[1] * x64s[0]
    t2 = a64s[0] * x64s[2] + a64s[1] * x64s[1] + a64s[2] * x64s[0]
    t3 = a64s[0] * x64s[3] + a64s[1] * x64s[2] + a64s[2] * x64s[1] + a64s[3] * x64s[0]
    assert v0m * (2**128) == t0 + t1 * (2**64) - y64s[0] - y64s[1] * (2**64)
    assert v1m * (2**128) == v0m + t2 + t3 * (2**64) - y64s[2] - y64s[3] * (2**64)


@is_circuit_code
def check_mul(a8s, b8s, c8s, v0, v1):
    mul_common(a8s, b8s, c8s, v0, v1)
