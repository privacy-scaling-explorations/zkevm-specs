from typing import Any, NewType, Sequence, List, Set, Tuple
from .constants import FIELD_SIZE

U256 = NewType("U256", int)
U8 = NewType("U8", int)
# must be one of -1, 0, 1
Sign = NewType("Sign", int)


def is_circuit_code(func):
    """
    A no-op decorator just to mark the function
    """
    def wrapper(*args, **kargs):
        return func(*args, **kargs)
    return wrapper


def u256_to_u8s(x: U256) -> Tuple[U8, ...]:
    assert 0 <= x < 2**256, "expect x is unsigned 256 bits"
    return tuple((x >> 8*i) & 0xff for i in range(32))


def u8s_to_u256(xs: Sequence[U8]) -> U256:
    assert len(xs) == 32
    for u8 in xs:
        assert 0 <= u8 <= 255
    return sum(x * (2**(8*i)) for i, x in enumerate(xs))


class LookupTable:
    columns: Tuple[str]
    rows: Set[int]
    random: int

    def __init__(self, columns: Sequence[str], random: int = 123) -> None:
        self.columns = set(columns)
        self.rows = set()
        self.random = random

    def __compress(self, **kwargs):
        assert set(kwargs.keys()) == self.columns
        return sum(kwargs[col] * self.random ** i for i, col in enumerate(self.columns))

    def add_row(self, **kwargs):
        self.rows.add(self.__compress(**kwargs))

    def __len__(self):
        return len(self.rows)

    def lookup(self, **kwargs) -> bool:
        if self.__compress(**kwargs) in self.rows:
            return True
        raise ValueError("Row does not exist", kwargs)


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
        a16 = a8s[i] + 2 * a8s[i + 1]
        b16 = b8s[i] + 2 * b8s[i + 1]

        diff = (a16 - b16) % FIELD_SIZE
        previous, current = result[i//2+1], result[i // 2]

        assert sign_table.lookup(
            x=(diff + 2**16 * previous) % FIELD_SIZE,
            sign=current
        )

    return result[0]
