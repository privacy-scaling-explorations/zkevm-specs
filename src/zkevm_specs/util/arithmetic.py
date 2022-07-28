from __future__ import annotations
from typing import Sequence, Protocol, Type, TypeVar, Union
from py_ecc import bn128
from py_ecc.utils import prime_field_inv


def linear_combine(le_bytes: Sequence[Union[int, FQ]], base: FQ, range_check: bool = True) -> FQ:
    """
    Aggregate bytes into a single field element.
    If we intend to use it as a commitment, the base must be a secured random number.
    >>> r = 10
    >>> assert linear_combine([1, 2, 3], r) == 1 * r**2 + 2 * r + 3
    If the input represents a sequence of data, apply the function directly.
    If the input represents a number, it must be in little-endian order.
    Do not use linear_combine(le_limbs, 256) to evaluate the integer value.
    """
    result = FQ.zero()
    be_bytes = reversed(le_bytes)
    for limb in be_bytes:
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
        self.rlc_value = linear_combine(value, randomness)
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
