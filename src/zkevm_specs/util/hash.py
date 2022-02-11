from typing import Union
from Crypto.Hash import keccak

from .typing import U256


def keccak256(_data: Union[str, bytes, bytearray]) -> bytes:
    data = bytes.fromhex(_data) if isinstance(_data, str) else _data
    return keccak.new(digest_bits=256).update(data).digest()


EMPTY_HASH = U256(int.from_bytes(keccak256(""), "big"))
EMPTY_CODE_HASH: U256 = EMPTY_HASH
EMPTY_TRIE_HASH = U256(int.from_bytes(keccak256("80"), "big"))
