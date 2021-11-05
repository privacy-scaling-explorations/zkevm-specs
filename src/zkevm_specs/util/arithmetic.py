from __future__ import annotations
from typing import Sequence, Union


class FpNum:
    """FpNum represents the value in the BN254 scalar field."""

    # BN254 scalar field size
    FP_MODULUS = 21888242871839275222246405745257275088548364400416034343698204186575808495617

    def __init__(self, value: Union[int, FpNum]):
        if isinstance(value, int):
            self.value = value % FpNum.FP_MODULUS
        elif isinstance(value, FpNum):
            self.value = value.value
        else:
            raise TypeError(f"Expect int or FpNum, but get type {type(value)}")

    def __add__(self, other: Union[int, FpNum]) -> FpNum:
        return FpNum(self.value + FpNum(other).value)

    def __radd__(self, other: Union[int, FpNum]) -> FpNum:
        return self + other

    def __sub__(self, other: Union[int, FpNum]) -> FpNum:
        return FpNum(self.value - FpNum(other).value)

    def __rsub__(self, other: Union[int, FpNum]) -> FpNum:
        return FpNum(other) - self

    def __neg__(self) -> FpNum:
        return FpNum(-self.value)

    def __mul__(self, other: Union[int, FpNum]) -> FpNum:
        return FpNum(self.value * FpNum(other).value)

    def __eq__(self, other: Union[int, FpNum]) -> bool:
        return self.value == FpNum(other).value

    def __lt__(self, other: Union[int, FpNum]) -> bool:
        return self.value < FpNum(other).value

    def __gt__(self, other: Union[int, FpNum]) -> bool:
        return self.value > FpNum(other).value

    def __hash__(self) -> int:
        return hash(self.value)

    def __str__(self) -> str:
        return f"Fp({self.value})"

    __repr__ = __str__

    def inv(self) -> FpNum:
        return FpNum(pow(value, -1, FpNum.FP_MODULUS))


def fp_linear_combine(le_bytes: Union[bytes, Sequence[int]], factor: int) -> FpNum:
    ret = FpNum(0)
    factor = FpNum(factor)
    for byte in reversed(le_bytes):
        assert 0 <= byte < 256, "Each byte in le_bytes for linear combination should fit in 8-bit"
        ret = ret * factor + byte
    return ret


class RLC:
    le_bytes: bytes
    value: FpNum

    def __init__(self, int_or_bytes: Union[int, bytes], randomness: int, n_bytes: int = 32) -> None:
        if isinstance(int_or_bytes, int):
            assert 0 <= int_or_bytes < 256**n_bytes, f"Value {int_or_bytes} too large to fit {n_bytes} bytes"
            self.le_bytes = int_or_bytes.to_bytes(n_bytes, "little")
        elif isinstance(int_or_bytes, FpNum):
            assert int_or_bytes.value < 256 ** n_bytes, f"Value {int_or_bytes} too large to fit {n_bytes} bytes"
            self.le_bytes = int_or_bytes.value.to_bytes(n_bytes, "little")
        elif isinstance(int_or_bytes, bytes):
            assert len(int_or_bytes) <= n_bytes, f"Expected bytes with length less or equal than {n_bytes}"
            self.le_bytes = int_or_bytes.ljust(n_bytes, b"\x00")
        else:
            raise TypeError(f"Expected an int or bytes, but got object of type {type(int_or_bytes)}")

        self.value = fp_linear_combine(self.le_bytes, randomness)

    def __eq__(self, rhs: Union[int, FpNum, RLC]):
        if isinstance(rhs, (int, FpNum)):
            return self.value == rhs
        if isinstance(rhs, RLC):
            return self.value == rhs.value
        else:
            raise TypeError(f"Expected a RLC, but got object of type {type(rhs)}")

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return "RLC(%s)" % int.from_bytes(self.le_bytes, "little")

    def be_bytes(self) -> bytes:
        return bytes(reversed(self.le_bytes))
