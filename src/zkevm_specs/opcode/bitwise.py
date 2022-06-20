from typing import Sequence
from ..encoding import U8, is_circuit_code


@is_circuit_code
def check_and(
    a8s: Sequence[U8],
    b8s: Sequence[U8],
    c8s: Sequence[U8],
):
    assert len(a8s) == len(b8s) == len(c8s) == 32
    for i in range(32):
        assert a8s[i] & b8s[i] == c8s[i]


@is_circuit_code
def check_or(
    a8s: Sequence[U8],
    b8s: Sequence[U8],
    c8s: Sequence[U8],
):
    assert len(a8s) == len(b8s) == len(c8s) == 32
    for i in range(32):
        assert a8s[i] | b8s[i] == c8s[i]


@is_circuit_code
def check_xor(
    a8s: Sequence[U8],
    b8s: Sequence[U8],
    c8s: Sequence[U8],
):
    assert len(a8s) == len(b8s) == len(c8s) == 32
    for i in range(32):
        assert a8s[i] ^ b8s[i] == c8s[i]


@is_circuit_code
def check_not(
    a8s: Sequence[U8],
    b8s: Sequence[U8],
):
    assert len(a8s) == len(b8s) == 32
    for i in range(32):
        assert a8s[i] ^ b8s[i] == 255
