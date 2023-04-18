from typing import NewType

U8 = NewType("U8", int)
U64 = NewType("U64", int)
U128 = NewType("U128", int)
U160 = NewType("U160", int)
U256 = NewType("U256", int)


def is_circuit_code(func):
    """
    A no-op decorator just to mark the function
    """

    def wrapper(*args, **kargs):
        return func(*args, **kargs)

    return wrapper
