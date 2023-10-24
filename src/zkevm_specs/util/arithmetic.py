from __future__ import annotations
from typing import runtime_checkable, List, Protocol, Sequence, Tuple, Type, TypeVar, Union
from py_ecc import bn128
from py_ecc.utils import prime_field_inv
from .param import MAX_N_BYTES
from .typing import U256


def linear_combine_bytes(seq: Sequence[Union[int, FQ]], base: FQ, range_check: bool = True) -> FQ:
    """
    Aggregate a sequence of data into a single field element.
    To use it as a commitment, the base must be a secured random number.
    If the input represents a sequence of data, apply the function directly.
    If the input represents a number, it must be in little-endian order.
    >>> r = 10
    >>> assert linear_combine_bytes([1, 2, 3], r) == 1 + 2 * r + 3 * r**2
    """
    result = FQ.zero()
    for limb in reversed(seq):
        if range_check:
            limb_int = limb.n if isinstance(limb, FQ) else limb
            assert 0 <= limb_int < 256, "Each byte should fit in 8-bit"
        result = result * base + limb
    return result


class FQ(bn128.curve_order):
    def __init__(self, value: IntOrFQ) -> None:
        if isinstance(value, FQ):
            self.n = value.n
        else:
            super().__init__(value)

    def __hash__(self) -> int:
        return hash(self.n)

    def expr(self) -> FQ:
        return FQ(self)

    def inv(self) -> FQ:
        return FQ(prime_field_inv(self.n, self.field_modulus))

    def __repr__(self) -> str:
        return f"{hex(self.n)}"


IntOrFQ = Union[int, FQ]


class RLC:
    # value in int
    int_value: int
    # encoded value using random linear combination
    rlc_value: FQ
    # bytes in little-endian order
    le_bytes: bytes

    def __init__(self, value: Union[int, bytes], randomness: FQ = FQ(0), n_bytes: int = 32) -> None:
        if isinstance(value, int):
            value = value.to_bytes(n_bytes, "little")

        if len(value) > n_bytes:
            raise ValueError(f"RLC expects to have {n_bytes} bytes, but got {len(value)} bytes")
        value = value.ljust(n_bytes, b"\x00")

        self.int_value = int.from_bytes(value, "little")
        self.rlc_value = linear_combine_bytes(value, randomness)
        self.le_bytes = value

    def expr(self) -> FQ:
        return FQ(self.rlc_value)

    def __hash__(self) -> int:
        return hash(self.rlc_value)

    def __repr__(self) -> str:
        return "RLC(%s)" % int.from_bytes(self.le_bytes, "little")


class Word:
    """Word stored as lo/hi: lowest 128 bits and highest 128 bits"""

    # lowest 128 bits
    lo: Expression
    # highest 128 bits
    hi: Expression

    def __init__(
        self, value: Union[Tuple[Expression, Expression], int, U256, bytes], check=True
    ) -> None:
        if isinstance(value, tuple):
            self.lo, self.hi = value
            # sanity check
            assert not check or (self.lo.expr().n < 256**16 and self.hi.expr().n < 256**16)
            return
        if isinstance(value, int):
            # sanity check
            assert not check or (value < 256**32)
            value = value.to_bytes(32, "little")
        # sanity checks
        assert isinstance(value, bytes)
        assert len(value) == 32, f"Word expects to receive 32 bytes, but got {len(value)} bytes"
        self.lo = bytes_to_fq(value[0:16])
        self.hi = bytes_to_fq(value[16:32])

    @classmethod
    def from_lo(cls, lo: Expression):
        return cls((lo, FQ(0)))

    def int_value(self) -> int:
        """Return the word as an integer"""
        return self.lo.expr().n + (self.hi.expr().n << 128)

    def __hash__(self) -> int:
        return hash((self.lo, self.hi))

    def __repr__(self) -> str:
        return f"Word({hex(self.int_value())})"

    def __eq__(self, other) -> bool:
        assert isinstance(other, Word)
        return self.lo.expr() == other.lo.expr() and self.hi.expr() == other.hi.expr()

    def __add__(self, other: Word) -> Word:
        """Combine two words by adding their corresponding lo and hi parts.  Useful with select.
        This is not a 256 bit addition"""
        return Word((self.lo.expr() + other.lo.expr(), self.hi.expr() + other.hi.expr()))

    def select(self, selector: FQ) -> Word:
        """Return a new Word with lo and hi multiplied by selector"""
        return Word((selector * self.lo, selector * self.hi))

    def to_lo_hi(self) -> Tuple[FQ, FQ]:
        return (self.lo.expr(), self.hi.expr())

    def to_64s(self) -> Tuple[FQ, ...]:
        lo_bytes = self.lo.expr().n.to_bytes(16, "little")
        hi_bytes = self.hi.expr().n.to_bytes(16, "little")
        return (
            bytes_to_fq(lo_bytes[0:8]),
            bytes_to_fq(lo_bytes[8:16]),
            bytes_to_fq(hi_bytes[0:8]),
            bytes_to_fq(hi_bytes[8:16]),
        )

    def to_le_bytes(self) -> Tuple[FQ, ...]:
        lo = self.lo.expr().n.to_bytes(16, "little")
        hi = self.hi.expr().n.to_bytes(16, "little")
        return tuple([FQ(v) for v in lo + hi])


class WordOrValue(Word):
    """Type that holds a 256 bit word (as lo/hi) or a value that fits in the field"""

    is_word: bool

    def __init__(self, value: Union[Word, Expression]) -> None:
        if isinstance(value, Word):
            self.is_word = True
            self.lo = value.lo
            self.hi = value.hi
        else:
            self.is_word = False
            self.lo = value
            self.hi = FQ(0)

    def value(self) -> Expression:
        """When this type holds a value that fits in the field, return it"""
        assert not self.is_word
        return self.lo

    def __repr__(self) -> str:
        if self.is_word:
            return super().__repr__()
        else:
            return f"Value({hex(self.lo.expr().n)})"


@runtime_checkable
class Expression(Protocol):
    def expr(self) -> FQ:
        ...

    def __eq__(self, other) -> bool:
        assert isinstance(other, Expression)
        return self.expr() == other.expr()


ExpressionImpl = TypeVar("ExpressionImpl", bound=Expression)


def cast_expr(expression: Expression, ty: Type[ExpressionImpl]) -> ExpressionImpl:
    if not isinstance(expression, ty):
        raise TypeError(f"Casting Expression to {ty}, but got {type(expression)}")
    return expression


def byte_size(value: Union[int, RLC]) -> int:
    if isinstance(value, RLC):
        return len(bytearray(value.le_bytes).rstrip(b"\x00"))
    else:
        return (value.bit_length() + 7) // 8


def bytes_to_fq(value: bytes):
    assert len(value) <= MAX_N_BYTES
    return FQ(int.from_bytes(value, "little"))


def sum_values(values: Sequence[IntOrFQ]) -> FQ:
    return FQ(sum(values))


def add_words(addends: Sequence[Word]) -> Tuple[Word, FQ]:
    addends_lo, addends_hi = list(zip(*[w.to_lo_hi() for w in addends]))

    carry_lo, sum_lo = divmod(sum_values(addends_lo).n, 1 << 128)
    carry_hi, sum_hi = divmod((sum_values(addends_hi) + carry_lo).n, 1 << 128)

    return Word((FQ(sum_lo), FQ(sum_hi))), FQ(carry_hi)


def mul_add_words(
    a: Word, b: Word, c: Word, d: Word
) -> Tuple[FQ, Tuple[FQ, FQ], List[Tuple[FQ, FQ]]]:
    """
    The function constrains a * b + c == d, where a, b, c, d are 256-bit words.
    It returns the overflow part of a * b + c.
    """
    a64s = a.to_64s()
    b64s = b.to_64s()
    c_lo, c_hi = c.lo.expr(), c.hi.expr()
    d_lo, d_hi = d.lo.expr(), d.hi.expr()

    t0 = a64s[0] * b64s[0]
    t1 = a64s[0] * b64s[1] + a64s[1] * b64s[0]
    t2 = a64s[0] * b64s[2] + a64s[1] * b64s[1] + a64s[2] * b64s[0]
    t3 = a64s[0] * b64s[3] + a64s[1] * b64s[2] + a64s[2] * b64s[1] + a64s[3] * b64s[0]
    carry_lo = (t0 + (t1 * 2**64) + c_lo - d_lo) / (2**128)
    carry_hi = (t2 + (t3 * 2**64) + c_hi + carry_lo - d_hi) / (2**128)
    overflow = (
        carry_hi
        + a64s[1] * b64s[3]
        + a64s[2] * b64s[2]
        + a64s[3] * b64s[1]
        + a64s[2] * b64s[3]
        + a64s[3] * b64s[2]
        + a64s[3] * b64s[3]
    )

    constraint1 = (t0 + t1 * (2**64) + c_lo, d_lo + carry_lo * (2**128))
    constraint2 = (t2 + t3 * (2**64) + c_hi + carry_lo, d_hi + carry_hi * (2**128))

    return overflow, (carry_lo, carry_hi), [constraint1, constraint2]


def get_int_abs(x: int) -> int:
    return get_int_neg(x) if int_is_neg(x) else x


def get_int_neg(x: int) -> int:
    return 0 if x == 0 else (1 << 256) - x


def int_is_neg(x: int) -> int:
    return x >> 255
