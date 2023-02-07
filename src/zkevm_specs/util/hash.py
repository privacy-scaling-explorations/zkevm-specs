from typing import Union
from Crypto.Hash import keccak

from .typing import U256


def keccak256(data: Union[str, bytes, bytearray]) -> bytes:
    if isinstance(data, str):
        data = bytes.fromhex(data)
    return keccak.new(digest_bits=256).update(data).digest()


def create_address(b: bytes, nonce: int) -> bytes:
    data = [b, nonce]
    return keccak.new(digest_bits=256).update(data).digest()


EMPTY_HASH: U256 = U256(int.from_bytes(keccak256(""), "big"))
EMPTY_CODE_HASH: U256 = EMPTY_HASH
EMPTY_TRIE_HASH: U256 = U256(int.from_bytes(keccak256("80"), "big"))
