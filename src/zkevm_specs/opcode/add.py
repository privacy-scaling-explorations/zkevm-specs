from typing import Sequence

from ..encoding import U8, is_circuit_code


def add_sub_common(
    a8s: Sequence[U8],
    x8s: Sequence[U8],
    y8s: Sequence[U8],
    carry32: Sequence[bool],
):
    """
    Check the addition of two length 32 8-bit chunks a8s and x8s
    Items of a8s and x8s should already be verified to be 8 bits before.
    We allow the last carry bit to be 1 to match the overflow behavior of the EVM
    """
    assert len(a8s) == len(x8s) == len(y8s) == 32
    assert len(carry32) == 32

    # Case 0:
    assert a8s[0] + x8s[0] == y8s[0] + carry32[0] * 256

    # Case 1 to 31:
    for i in range(1, 32):
        assert carry32[i] * (carry32[i] - 1) == 0, "carry should be 0 or 1"
        assert a8s[i] + x8s[i] + carry32[i - 1] == y8s[i] + carry32[i] * 256


@is_circuit_code
def check_add(a8s, b8s, sum8s, is_sub, carry32):
    assert not is_sub
    add_sub_common(a8s, b8s, sum8s, carry32)


@is_circuit_code
def check_sub(a8s, b8s, diff8s, is_sub, carry32):
    assert is_sub
    add_sub_common(a8s, diff8s, b8s, carry32)


def test_check_add_basic():
    a8s = [1] + [0] * 31
    b8s = [2] + [0] * 31
    sum8s = [3] + [0] * 31
    carry32 = [0] * 32
    check_add(a8s, b8s, sum8s, False, carry32)
    check_sub(sum8s, b8s, a8s, True, carry32)


def test_check_add_simple_carry():
    a8s = [255] + [0] * 31
    b8s = [2] + [0] * 31
    sum8s = [1, 1] + [0] * 30
    carry32 = [1] + [0] * 32
    check_add(a8s, b8s, sum8s, False, carry32)
    check_sub(sum8s, b8s, a8s, True, carry32)


def test_check_add_overflow():
    a8s = [255] * 32
    b8s = [2] + [0] * 31
    sum8s = [1] + [0] * 31
    carry32 = [1] * 32
    check_add(a8s, b8s, sum8s, False, carry32)
    check_sub(sum8s, b8s, a8s, True, carry32)
