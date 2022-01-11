from typing import Sequence

from ..encoding import is_circuit_code, U8, U256, u8s_to_u256

def slt_circuit(
    a8s: Sequence[U8],
    b8s: Sequence[U8],
    result8s: Sequence[U8],
):
    """
    Check if `a8s < b8s` and set `result8s = 1` if that is the case, else set `result8s = 0`.
    """
    assert len(a8s) == len(b8s) == len(result8s) == 32

    # result is binary
    assert result8s[0] in [0, 1]
    for i in range(1, 32):
        assert result8s[i] == 0

    # encode a8s and b8s to U256
    aa = u8s_to_u256(a8s)
    bb = u8s_to_u256(b8s)

    # if a and b (two's complement form) both are unsigned
    if a8s[0] < 128 and b8s[0] < 128:
        assert result8s[0] == (aa < bb)
    # only a is unsigned
    elif a8s[0] < 128:
        assert result8s[0] == 1
    # only b is unsigned
    elif b8s[0] < 128:
        assert result8s[0] == 0
    # both a and b are signed, reverse our check
    else:
        assert result8s[0] == (bb < aa)

@is_circuit_code
def check_slt(
    a8s: Sequence[U8],
    b8s: Sequence[U8],
    result8s: Sequence[U8],
    is_sgt: bool,
):
    assert not is_sgt
    slt_circuit(a8s, b8s, result8s)

@is_circuit_code
def check_sgt(
    a8s: Sequence[U8],
    b8s: Sequence[U8],
    result8s: Sequence[U8],
    is_sgt: bool,
):
    assert is_sgt
    slt_circuit(b8s, a8s, result8s)
