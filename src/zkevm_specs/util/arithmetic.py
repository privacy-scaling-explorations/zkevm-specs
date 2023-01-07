from __future__ import annotations
from typing import List, Protocol, Sequence, Tuple, Type, TypeVar, Union
from py_ecc import bn128
from py_ecc.utils import prime_field_inv
from .param import MAX_N_BYTES


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


class FQ(bn128.FQ):
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


class Expression(Protocol):
    def expr(self) -> FQ:
        ...


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


def word_to_lo_hi(word: RLC) -> Tuple[FQ, FQ]:
    assert len(word.le_bytes) == 32, "Expected word to contain 32 bytes"
    return bytes_to_fq(word.le_bytes[:16]), bytes_to_fq(word.le_bytes[16:])


def word_to_64s(word: RLC) -> Tuple[FQ, ...]:
    assert len(word.le_bytes) == 32, "Expected word to contain 32 bytes"
    return tuple(bytes_to_fq(word.le_bytes[8 * i : 8 * (i + 1)]) for i in range(4))


def lo_hi_to_64s(lo_hi: Tuple[FQ, FQ]) -> Tuple[FQ, ...]:
    lo_bytes = lo_hi[0].n.to_bytes(16, "little")
    hi_bytes = lo_hi[1].n.to_bytes(16, "little")
    return (
        bytes_to_fq(lo_bytes[0:8]),
        bytes_to_fq(lo_bytes[8:16]),
        bytes_to_fq(hi_bytes[0:8]),
        bytes_to_fq(hi_bytes[8:16]),
    )


def sum_values(values: Sequence[IntOrFQ]) -> FQ:
    return FQ(sum(values))


def add_words(addends: Sequence[RLC], randomness: FQ) -> Tuple[RLC, FQ]:
    addends_lo, addends_hi = list(zip(*map(word_to_lo_hi, addends)))
    carry_lo, sum_lo = divmod(sum_values(addends_lo).n, 1 << 128)
    carry_hi, sum_hi = divmod((sum_values(addends_hi) + carry_lo).n, 1 << 128)
    sum_bytes = sum_lo.to_bytes(16, "little") + sum_hi.to_bytes(16, "little")
    return RLC(sum_bytes, randomness, n_bytes=len(sum_bytes)), FQ(carry_hi)


def mul_add_words(a: RLC, b: RLC, c: RLC, d: RLC) -> Tuple[FQ, Tuple[FQ, FQ], List[Tuple[FQ, FQ]]]:
    """
    The function constrains a * b + c == d, where a, b, c, d are 256-bit words.
    It returns the overflow part of a * b + c.
    """
    a64s = word_to_64s(a)
    b64s = word_to_64s(b)
    c_lo, c_hi = word_to_lo_hi(c)
    d_lo, d_hi = word_to_lo_hi(d)

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
