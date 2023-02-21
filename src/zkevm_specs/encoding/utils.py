from typing import Sequence, Tuple
from .typing import U8, U256


def is_circuit_code(func):
    """
    A no-op decorator just to mark the function
    """

    def wrapper(*args, **kargs):
        return func(*args, **kargs)

    return wrapper


def u256_to_u8s(x: U256) -> Tuple[U8, ...]:
    assert 0 <= x < 2**256, "expect x is unsigned 256 bits"
    return tuple(U8((x >> 8 * i) & 0xFF) for i in range(32))


def u8s_to_u256(xs: Sequence[U8]) -> U256:
    assert len(xs) == 32
    for u8 in xs:
        assert 0 <= u8 <= 255
    return U256(sum(x * (2 ** (8 * i)) for i, x in enumerate(xs)))
