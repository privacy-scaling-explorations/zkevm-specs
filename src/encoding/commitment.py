from typing import Sequence, Tuple

from typing import Sequence
from .typing import U256, U8
from .utils import is_circuit_code, u256_to_u8s
from .lookup import LookupTable


class RangeTable(LookupTable):
    """
    This table checks if a and b are both 8 bits.
    a: 8 bits
    b: 8 bits
    (3 columns and 2**16 rows)
    """

    def __init__(self) -> None:
        super().__init__(["a", "b"])
        for a in range(256):
            for b in range(256):
                self.add_row(a=a, b=b)


def commit(x: U256, random: int) -> Tuple[Tuple[U8, ...], int]:
    x8s = u256_to_u8s(x)
    commitment = sum(x8 * random ** i for i, x8 in enumerate(x8s))
    return x8s, commitment


@is_circuit_code
def check_commitment(x8s: Sequence[U8], commitment: int, random: int, range_table: RangeTable):
    """
    We establish that x8s
    - represents the value we committed before
    - and all its elements are 8 bits
    """
    assert len(x8s) == 32

    assert sum(x8 * random ** i for i, x8 in enumerate(x8s)) == commitment

    for i in range(0, 32, 2):
        low8, high8 = x8s[i], x8s[i+1]
        assert range_table.lookup(a=low8, b=high8)
