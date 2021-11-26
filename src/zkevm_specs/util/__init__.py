from Crypto.Random import get_random_bytes
from Crypto.Random.random import randrange

from .arithmetic import *
from .hash import *
from .typing import *


def hex_to_word(hex: str) -> bytes:
    return bytes.fromhex(hex.removeprefix('0x').zfill(64))


def rand_int(mod: int = 2**256) -> int:
    return randrange(0, mod)


def rand_bytes(n_bytes: int = 32) -> bytes:
    return get_random_bytes(n_bytes)
