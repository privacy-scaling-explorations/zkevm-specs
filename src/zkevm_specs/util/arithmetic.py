from __future__ import annotations
from typing import Sequence, Union
from py_ecc.fields import bn128_FQ as FQ


def _hash_fq(v: FQ) -> int:
    return hash(v.n)


FQ.__hash__ = _hash_fq  # type: ignore
IntOrFQ = Union[int, FQ]


def fp_linear_combine(le_bytes: Union[bytes, Sequence[int]], _factor: int) -> FQ:
    ret = FQ.zero()
    factor = FQ(_factor)
    for byte in reversed(le_bytes):
        assert 0 <= byte < 256, "Each byte in le_bytes for linear combination should fit in 8-bit"
        ret = ret * factor + byte
    return ret


class RLC:
    le_bytes: bytes
    value: FQ

    def __init__(
        self, int_or_bytes: Union[IntOrFQ, bytes], randomness: int, n_bytes: int = 32
    ) -> None:
        if isinstance(int_or_bytes, int):
            assert (
                0 <= int_or_bytes < 256**n_bytes
            ), f"Value {int_or_bytes} too large to fit {n_bytes} bytes"
            self.le_bytes = int_or_bytes.to_bytes(n_bytes, "little")
        elif isinstance(int_or_bytes, FQ):
            assert (
                int_or_bytes.n < 256**n_bytes
            ), f"Value {int_or_bytes} too large to fit {n_bytes} bytes"
            self.le_bytes = int_or_bytes.n.to_bytes(n_bytes, "little")
        elif isinstance(int_or_bytes, bytes):
            assert (
                len(int_or_bytes) <= n_bytes
            ), f"Expected bytes with length less or equal than {n_bytes}"
            self.le_bytes = int_or_bytes.ljust(n_bytes, b"\x00")
        else:
            raise TypeError(
                f"Expected an int or bytes, but got object of type {type(int_or_bytes)}"
            )

        self.value = fp_linear_combine(self.le_bytes, randomness)

    def __eq__(self, rhs: Union[int, object]):
        if isinstance(rhs, (int, FQ)):
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
