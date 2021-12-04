from typing import Dict, Sequence, Tuple, Union
from Crypto.Random import get_random_bytes
from Crypto.Random.random import randrange


# BN254 scalar field size
FP_MODULUS = 21888242871839275222246405745257275088548364400416034343698204186575808495617

# Maximun number of bytes with composition value that doesn't wrap around the field
MAX_N_BYTES = 31


def fp_add(a: int, b: int) -> int:
    return (a + b) % FP_MODULUS


def fp_mul(a: int, b: int) -> int:
    return (a * b) % FP_MODULUS


def fp_inv(value: int) -> int:
    return pow(value, -1, FP_MODULUS)


def le_to_int(bytes: Sequence[int]) -> int:
    assert len(bytes) <= MAX_N_BYTES, "too many bytes to composite an integer in field"
    return linear_combine(bytes, 256)


def linear_combine(bytes: Sequence[int], r: int) -> int:
    ret = 0
    for byte in reversed(bytes):
        assert 0 <= byte < 256, "bytes for linear combination should be already checked in range"
        ret = fp_add(fp_mul(ret, r), byte)
    return ret


class RLCStore:
    randomness: int
    rlc_to_bytes: Dict[int, bytes] = dict()

    def __init__(self, randomness: int = randrange(0, FP_MODULUS)) -> None:
        self.randomness = randomness
        for byte in range(256):
            self.to_rlc([byte])

    def to_rlc(self, seq_or_int: Union[Sequence[int], int], n_bytes: int = 0) -> int:
        seq = seq_or_int
        if type(seq_or_int) == int:
            seq = seq_or_int.to_bytes(n_bytes, "little")
        rlc = linear_combine(seq, self.randomness)

        if rlc in self.rlc_to_bytes:
            existed = self.rlc_to_bytes[rlc]
            maxlen = max(len(existed), len(seq))
            assert existed.ljust(maxlen, b"\x00") == bytes(seq).ljust(
                maxlen, b"\x00"
            ), f"Random lienar combination collision on {existed} and {bytes(seq)} with randomness {self.randomness}"
        else:
            self.rlc_to_bytes[rlc] = bytes(seq)

        return rlc

    def to_bytes(self, rlc: int) -> bytes:
        return self.rlc_to_bytes[rlc]

    def rand(self, n_bytes: int = 32) -> Tuple[int, bytes]:
        bytes = get_random_bytes(n_bytes)
        return self.to_rlc(bytes), bytes

    def add(self, lhs: int, rhs: int, modulus: int = 2 ** 256) -> Tuple[int, bytes, bool]:
        lhs_bytes = self.to_bytes(lhs)
        rhs_bytes = self.to_bytes(rhs)
        carry, result = divmod(
            int.from_bytes(lhs_bytes, "little") + int.from_bytes(rhs_bytes, "little"),
            modulus,
        )
        result_bytes = result.to_bytes(32, "little")
        return self.to_rlc(result_bytes), result_bytes, carry > 0

    def sub(self, lhs: int, rhs: int, modulus: int = 2 ** 256) -> Tuple[int, bytes, bool]:
        lhs_bytes = self.to_bytes(lhs)
        rhs_bytes = self.to_bytes(rhs)
        borrow, result = divmod(
            int.from_bytes(lhs_bytes, "little") - int.from_bytes(rhs_bytes, "little"),
            modulus,
        )
        result_bytes = result.to_bytes(32, "little")
        return self.to_rlc(result_bytes), result_bytes, borrow < 0
