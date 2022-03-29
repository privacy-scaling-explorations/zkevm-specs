from __future__ import annotations
from typing import Protocol, Sequence, Type, TypeVar, Union
from functools import reduce
from py_ecc import bn128


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

    @staticmethod
    def linear_combine(le_bytes: Sequence[int], base: FQ) -> FQ:
        def accumulate(acc: FQ, byte: int) -> FQ:
            assert (
                0 <= byte < 256
            ), "Each byte in le_bytes for linear combination should fit in 8-bit"
            return acc * base + FQ(byte)

        return reduce(accumulate, reversed(le_bytes), FQ(0))


IntOrFQ = Union[int, FQ]


class RLC:
    value: FQ
    le_bytes: bytes

    def __init__(self, value: Union[int, bytes], randomness: FQ = FQ(0), n_bytes: int = 32) -> None:
        if isinstance(value, int):
            value = value.to_bytes(n_bytes, "little")

        if len(value) > n_bytes:
            raise ValueError(f"RLC expects to have {n_bytes} bytes, but got {len(value)} bytes")
        value = value.ljust(n_bytes, b"\x00")

        self.value = FQ.linear_combine(value, randomness)
        self.le_bytes = value

    def expr(self) -> FQ:
        return FQ(self.value)

    def __hash__(self) -> int:
        return hash(self.value)

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
