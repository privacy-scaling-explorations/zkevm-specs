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
    assert len(a8s) == len(b8s) == len(sum8s) == 32
    assert len(carry32) == 32

    # Before we add anything yet, the carry bit should be 0
    # We allow the last carry bit to be 1 to support the overflow case
    carry33 = [0] + carry32[:]

    for i in range(32):
        assert carry32[i] * (carry32[i] - 1) == 0, "carry should be 0 or 1"
        assert a8s[i] + b8s[i] + carry33[i] == sum8s[i] + (carry33[i + 1] << 8)
