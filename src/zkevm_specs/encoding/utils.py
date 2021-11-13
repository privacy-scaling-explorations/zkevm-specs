from typing import Sequence, Tuple, List
from .typing import U8, U256, U64


def is_circuit_code(func) -> object:
    """
    A no-op decorator just to mark the function
    """

    def wrapper(*args, **kargs):
        return func(*args, **kargs)

    return wrapper


def u256_to_u8s(x: U256) -> Tuple[U8, ...]:
    assert 0 <= x < 2 ** 256, "expect x is unsigned 256 bits"
    return tuple((x >> 8 * i) & 0xff for i in range(32))


def u256_to_u64s(x: U256) -> Tuple[U64, ...]:
    assert 0 <= x < 2 ** 256, "expect x is unsigned 256 bits"
    return tuple((x >> 64 * i) & 0xffffffffffffffff for i in range(4))


def u8s_to_u256(xs: Sequence[U8]) -> U256:
    assert len(xs) == 32
    for u8 in xs:
        assert 0 <= u8 <= 255
    return sum(x * (2 ** (8 * i)) for i, x in enumerate(xs))

# [u8;32]->[u64;4]
def u8s_to_u64s(xs: Sequence[U8]) -> Tuple[U64, ...]:
    assert len(xs) == 32
    u64_0 = U64(0)
    A = [u64_0] * 4 # A = A3A2A1A0
    for i in range(4):
        for j in range(8):
            A[i] += U64(xs[j + 8 * i] * (2 ** (8 * j)))
    return tuple(A)

