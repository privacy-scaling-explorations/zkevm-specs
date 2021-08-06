from typing import Sequence

from .utils import is_circuit_code
from .typing import U8


@is_circuit_code
def check_add(
    a8s: Sequence[U8],
    b8s: Sequence[U8],
    sum8s: Sequence[U8],
    carry32: Sequence[bool],
):
    """
    Check the addition of two length 32 8-bit chunks a8s and b8s
    Items of a8s and b8s should already be verified to be 8 bits before.
    We allow the last carry bit to be 1 to match the overflow behavior of the EVM
    """
    assert len(a8s) == len(b8s) == len(sum8s) == 32
    assert len(carry32) == 32

    # Case 0:
    assert a8s[0] + b8s[0] == sum8s[0] + carry32[0] * 256

    # Case 1 to 31:
    for i in range(1, 32):
        assert carry32[i] * (carry32[i] - 1) == 0, "carry should be 0 or 1"
        assert a8s[i] + b8s[i] + carry32[i - 1] == sum8s[i] + carry32[i] * 256


def test_check_add_basic():
    a8s = [1] + [0] * 31
    b8s = [2] + [0] * 31
    sum8s = [3] + [0] * 31
    carry32 = [0] * 32
    check_add(a8s, b8s, sum8s, carry32)


def test_check_add_simple_carry():
    a8s = [255] + [0] * 31
    b8s = [2] + [0] * 31
    sum8s = [1, 1] + [0] * 30
    carry32 = [1] + [0] * 32
    check_add(a8s, b8s, sum8s, carry32)


def test_check_add_overflow():
    a8s = [255] * 32
    b8s = [2] + [0] * 31
    sum8s = [1] + [0] * 31
    carry32 = [1] * 32
    check_add(a8s, b8s, sum8s, carry32)
