from typing import Union
from Crypto.Random import get_random_bytes
from Crypto.Random.random import randrange

from .arithmetic import *
from .hash import *
from .param import *
from .typing import *


def rand_range(stop: Union[int, float] = 2**256) -> int:
    return randrange(0, int(stop))


def rand_fp() -> int:
    return rand_range(FpNum.FP_MODULUS)


def rand_address() -> U160:
    return rand_range(2**160)


def rand_word() -> U256:
    return rand_range(2**256)


def rand_bytes(n_bytes: int = 32) -> bytes:
    return get_random_bytes(n_bytes)
