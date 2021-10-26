from typing import Sequence

from ..encoding import is_circuit_code, U8, U256, u256_to_u8s

def lt_circuit(
    a8s: Sequence[U8],
    b8s: Sequence[U8],
    result8s: Sequence[U8],
    c8s: Sequence[U8],
    carry: U8,
):
    """
    Check if `c8s` equals to `b8s - a8s`.
    When result is 1, the sum of `a8s` and `c8s` should not overflow and `c8s` cannot be 0.
    `carry` is the carry bit for the sum of lower 128 bits of `a8s` and `c8s`.
    """
    assert len(a8s) == len(b8s) == len(c8s) == len(result8s) == 32

    # result[0] == 0 / 1, result[1:32] == 0
    assert result8s[0] in [0, 1]
    for i in range(1, 32):
        assert result8s[i] == 0

    # c != 0
    sumc = sum(c8s)
    if result8s[0] == 1:
        assert sumc != 0

    # c[i] in 0..255
    for limb in c8s:
        assert 0 <= limb <= 255

    # lower 16 bytes
    # a[15:0] + c[15:0] == carry * 256^16 + b[15:0]
    lhs = 0
    rhs = carry
    for i in reversed(range(16)):
        lhs = lhs * 256 + a8s[i] + c8s[i]
        rhs = rhs * 256 + b8s[i]
    assert lhs == rhs

    # high 16 bytes
    # a[31:16] + c[31:16] + carry = b[31:16] + (1-result[0]) * (sumc == 0) * 256^16
    lhs = 0
    rhs = (1-result8s[0]) * (sumc != 0)
    for i in range(16, 32):
        lhs = lhs * 256 + a8s[i] + c8s[i]
        rhs = rhs * 256 + b8s[i]
    lhs += carry
    assert lhs == rhs


@is_circuit_code
def check_lt(
    a8s: Sequence[U8],
    b8s: Sequence[U8],
    result8s: Sequence[U8],
    c8s: Sequence[U8],
    carry: U8,
    is_gt: bool,
):
    assert not is_gt
    lt_circuit(a8s, b8s, result8s, c8s, carry)


@is_circuit_code
def check_gt(
    a8s: Sequence[U8],
    b8s: Sequence[U8],
    result8s: Sequence[U8],
    c8s: Sequence[U8],
    carry: U8,
    is_gt: bool,
):
    assert is_gt
    # We swap a8s and b8s for GT, and re-use the lt circuit to check the constraints
    lt_circuit(b8s, a8s, result8s, c8s, carry)
