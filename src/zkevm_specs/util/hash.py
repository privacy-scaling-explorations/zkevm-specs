from typing import Union, List
from Crypto.Hash import keccak

from .typing import U256


def keccak256(data: Union[str, bytes, bytearray]) -> bytes:
    if isinstance(data, str):
        data = bytes.fromhex(data)
    return keccak.new(digest_bits=256).update(data).digest()


def address_encode(address: str) -> List[int]:
    if len(address) == 42 and address[:2] == "0x":
        address = address[2:]
    if len(address) == 40:
        prefix = [HEX_PREFIX + ADDRESS_LENGTH]
        for a, b in zip(address[0::2], address[1::2]):
            prefix.append(int(a + b, 16))
        return prefix
    else:
        raise ValueError("Invalid address format")


def generate_contract_address(address: List[int], nonce: int) -> bytes:
    print(len(address))
    if len(address) - 1 != ADDRESS_LENGTH:
        raise ValueError("Invalid address format")
    prefix = [LIST_PREFIX + 0x16]
    prefix += address
    prefix.append(HEX_PREFIX if nonce == 0 else nonce)
    raw_hash = keccak256(bytearray(prefix))[12:]
    return raw_hash[(len(raw_hash) - ADDRESS_LENGTH) :]


ADDRESS_LENGTH = 0x14
HEX_PREFIX = 0x80
LIST_PREFIX = 0xC0

EMPTY_HASH: U256 = U256(int.from_bytes(keccak256(""), "big"))
EMPTY_CODE_HASH: U256 = EMPTY_HASH
EMPTY_TRIE_HASH: U256 = U256(int.from_bytes(keccak256("80"), "big"))
