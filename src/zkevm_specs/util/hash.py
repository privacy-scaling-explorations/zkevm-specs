from typing import Union
from Crypto.Hash import keccak


def keccak256(data: Union[str, bytes]) -> bytes:
    if type(data) == str:
        data = bytes.fromhex(data)
    return keccak.new(digest_bits=256).update(data).digest()


EMPTY_HASH = keccak256("")
EMPTY_CODE_HASH = EMPTY_HASH
EMPTY_TRIE_HASH = keccak256("80")
