from typing import Sequence

from .utils import is_circuit_code
from .typing import U8
from .lookup import LookupTable


class AdditionTable(LookupTable):
    """
    x: unsigned 17 bits
    ------------
    low8: 8 bits
    high8: 8 bits
    carry: 1 bit
    (4 columns and 2**17 rows)
    """

    def __init__(self):
        super().__init__(["x", "low8", "high8", "carry"])
        for x in range(2**17):
            self.add_row(
                x=x,
                low8=x % 2**8,
                high8=(x % 2**16) // 2**8,
                carry=1 if x >= 2**16 else 0,
            )


@is_circuit_code
def check_add(
    a8s: Sequence[U8],
    b8s: Sequence[U8],
    sum8s: Sequence[U8],
    carry: Sequence[bool],
    addition_table: AdditionTable
):
    assert len(a8s) == len(b8s) == len(sum8s) == 32
    assert len(carry) == 16

    # Before we add anything yet, the carry bit should be 0
    # We allow the last carry bit to be 1 to support the overflow case
    carry = [0] + carry[:]

    for i in range(0, 32, 2):
        a16 = a8s[i] + 256 * a8s[i + 1]
        b16 = b8s[i] + 256 * b8s[i + 1]
        assert addition_table.lookup(
            x=a16 + b16 + carry[i//2],
            low8=sum8s[i],
            high8=sum8s[i + 1],
            carry=carry[i//2 + 1],
        )
