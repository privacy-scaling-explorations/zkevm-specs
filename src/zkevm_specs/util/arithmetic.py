from __future__ import annotations
from typing import Sequence, Union

# BN254 scalar field size
FP_MODULUS = 21888242871839275222246405745257275088548364400416034343698204186575808495617


def fp_add(a: int, b: int) -> int:
    return (a + b) % FP_MODULUS


def fp_mul(a: int, b: int) -> int:
    return (a * b) % FP_MODULUS


def fp_inv(value: int) -> int:
    return pow(value, -1, FP_MODULUS)


def fp_linear_combine(le_bytes: Union[bytes, Sequence[int]], factor: int) -> int:
    com = 0
    for byte in reversed(le_bytes):
        assert 0 <= byte < 256, "Each byte in le_bytes for linear combination should fit in 8-bit"
        com = fp_add(fp_mul(com, factor), byte)
    return com


class RLC:
    le_bytes: bytes
    value: int

    def __init__(self, int_or_bytes: Union[int, bytes], randomness: int, n_bytes: int = 32) -> None:
        if isinstance(int_or_bytes, int):
            assert 0 <= int_or_bytes < 256 ** n_bytes, f"Value {int_or_bytes} too large to fit {n_bytes} bytes"
            self.le_bytes = int_or_bytes.to_bytes(n_bytes, "little")
        elif isinstance(int_or_bytes, bytes):
            assert len(int_or_bytes) <= n_bytes, f"Expected bytes with length less or equal than {n_bytes}"
            self.le_bytes = int_or_bytes.ljust(n_bytes, b"\x00")
        else:
            raise TypeError(f"Expected an int or bytes, but got object of type {type(int_or_bytes)}")

        self.value = fp_linear_combine(self.le_bytes, randomness)

    def __eq__(self, rhs: Union[int, RLC]):
        if isinstance(rhs, int):
            return self.value == rhs
        if isinstance(rhs, RLC):
            return self.value == rhs.value
        else:
            raise TypeError(f"Expected a RLC, but got object of type {type(rhs)}")

    def __hash__(self) -> int:
        return self.value

    def __repr__(self) -> str:
        return int.from_bytes(self.le_bytes, "little").__repr__()

    def be_bytes(self) -> bytes:
        return bytes(reversed(self.le_bytes))
