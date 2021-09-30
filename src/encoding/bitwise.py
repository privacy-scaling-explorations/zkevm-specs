from typing import Sequence
from .constants import FIELD_SIZE
from .lookup import LookupTable
from .utils import is_circuit_code
from .typing import U8, Sign


@is_circuit_code
def check_xor(
        a8s: Sequence[U8],
        b8s: Sequence[U8],
        c8s: Sequence[U8]
):
    assert len(a8s) == len(b8s) == len(c8s) == 32

    for i in range(0, 32):
        assert a8s[i] ^ b8s[i] == c8s[i]


def test_check_xor():
    a8s = [1]
    b8s = [4]
    c8s = [5]
    check_xor(a8s, b8s, c8s)



@is_circuit_code
def check_or(
        a8s: Sequence[U8],
        b8s: Sequence[U8],
        c8s: Sequence[U8]
):
    assert len(a8s) == len(b8s) == len(c8s) == 32

    for i in range(0, 32):
        assert a8s[i] | b8s[i] == c8s[i]


def test_check_or():
    a8s = [1]
    b8s = [4]
    c8s = [5]
    check_xor(a8s, b8s, c8s)



@is_circuit_code
def check_and(
        a8s: Sequence[U8],
        b8s: Sequence[U8],
        c8s: Sequence[U8]
):
    assert len(a8s) == len(b8s) == len(c8s) == 32

    for i in range(0, 32):
        assert a8s[i] & b8s[i] == c8s[i]


def test_check_and():
    a8s = [1]
    b8s = [4]
    c8s = [0]
    check_xor(a8s, b8s, c8s)
