from typing import Sequence

from ..encoding import FIELD_SIZE, LookupTable, is_circuit_code, U8, Sign

class SignTable(LookupTable):
    """
    x: 18 bits signed ( -(2**17 - 1) to 2**17 - 1)
    sign: 2 bits (0, -1, 1)
    (1 column and 2**18 - 1 rows)
    """

    def __init__(self):
        super().__init__(["x", "sign"])
        self.add_row(x=0, sign=0)
        for x in range(1, 2**17):
            self.add_row(x=x, sign=1)
            self.add_row(x=-x + FIELD_SIZE, sign=-1)


@is_circuit_code
def compare(
    a8s: Sequence[U8],
    b8s: Sequence[U8],
    result: Sequence[Sign],
    sign_table: SignTable,
) -> Sign:
    """
    returns -1 if a < b
             0 if a == b
             1 if a > b
    """
    assert len(a8s) == len(b8s) == 32
    assert len(result) == 16

    # Before we do any comparison, the previous result is "equal"
    result = result[:] + [0]

    for i in reversed(range(0, 32, 2)):
        a16 = a8s[i] + 256 * a8s[i + 1]
        b16 = b8s[i] + 256 * b8s[i + 1]

        diff = (a16 - b16) % FIELD_SIZE
        previous, current = result[i//2+1], result[i // 2]

        assert sign_table.lookup(
            x=(diff + 2**16 * previous) % FIELD_SIZE,
            sign=current
        )

    return result[0]
