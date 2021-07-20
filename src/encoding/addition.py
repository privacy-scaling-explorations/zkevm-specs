from typing import Sequence

from .utils import is_circuit_code
from .typing import U8


@is_circuit_code
def check_add(
    a8s: Sequence[U8],
    b8s: Sequence[U8],
    sum8s: Sequence[U8],
    carry: Sequence[bool],
):
    assert len(a8s) == len(b8s) == len(sum8s) == 32
    assert len(carry) == 32

    # Before we add anything yet, the carry bit should be 0
    # We allow the last carry bit to be 1 to support the overflow case
    carry = [0] + carry[:]

    for i in range(32):
        assert a8s[i] + b8s[i] + carry[i] == sum8s[i] + (carry[i + 1] << 8)
