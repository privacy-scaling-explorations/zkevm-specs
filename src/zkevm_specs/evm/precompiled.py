from enum import IntEnum


class PrecompiledAddress(IntEnum):
    ECRECOVER = 0x01
    SHA256 = 0x02
    RIPEMD160 = 0x03
    DATA_COPY = 0x04
    BIG_MOD_EXP = 0x05
    BN254_ADD = 0x06
    BN254_SCALAR_MUL = 0x07
    BN254_PAIRING = 0x08
    BLAKE2F = 0x09
