from typing import Sequence

# BN254 scalar field size
FP = 21888242871839275222246405745257275088548364400416034343698204186575808495617


def fp_add(a: int, b: int) -> int: return (a + b) % FP
def fp_mul(a: int, b: int) -> int: return (a * b) % FP
def fp_inv(value: int) -> int: return pow(value, -1, FP)


def le_to_int(bytes: Sequence[int]) -> int:
    assert len(bytes) < 32
    return linear_combine(bytes, 256)


def linear_combine(bytes: Sequence[int], r: int) -> int:
    ret = 0
    for byte in reversed(bytes):
        assert 0 <= byte < 256, 'bytes for linear combination should be already checked in range'
        ret = fp_add(fp_mul(ret, r), byte)
    return ret
