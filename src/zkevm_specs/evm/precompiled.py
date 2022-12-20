from enum import IntEnum
from typing import Final, Dict, Tuple, List

from ..util.param import *


class PrecompiledAddress(IntEnum):
    ECRECOVER = 0x01
    SHA256 = 0x02
    RIPEMD160 = 0x03
    DATA_COPY = 0x04
    BIG_MOD_EXP = 0x05
    BN256_ADD = 0x06
    BN256_SCALAR_MUL = 0x07
    BN256_PAIRING = 0x08
    BLAKE2F = 0x09

    def base_gas_cost(self) -> int:
        return PRECOMPILE_INFO_MAP[self].base_gas


class PrecompileInfo:
    """
    Precompile information.
    """

    base_gas: int

    def __init__(
        self,
        base_gas: int,
    ) -> None:
        self.base_gas = base_gas


PRECOMPILE_INFO_MAP: Final[Dict[PrecompiledAddress, PrecompileInfo]] = dict(
    {
        PrecompiledAddress.ECRECOVER: PrecompileInfo(EcrecoverGas),
        PrecompiledAddress.SHA256: PrecompileInfo(Sha256BaseGas),
        PrecompiledAddress.RIPEMD160: PrecompileInfo(Ripemd160BaseGas),
        PrecompiledAddress.DATA_COPY: PrecompileInfo(IdentityBaseGas),
        PrecompiledAddress.BIG_MOD_EXP: PrecompileInfo(BigModExpBaseGas),
        PrecompiledAddress.BN256_ADD: PrecompileInfo(Bn256AddGas),
        PrecompiledAddress.BN256_SCALAR_MUL: PrecompileInfo(Bn256ScalarMulGas),
        PrecompiledAddress.BN256_PAIRING: PrecompileInfo(Bn256PairingBaseGas),
        PrecompiledAddress.BLAKE2F: PrecompileInfo(Blake2fBaseGas),
    }
)


def valid_precompiles() -> List[PrecompiledAddress]:
    return list(PrecompiledAddress)


def base_gas_cost_pairs() -> List[Tuple[PrecompiledAddress, int]]:
    pairs = []
    for precompile in valid_precompiles():
        if precompile.base_gas_cost() > 0:
            pairs.append((precompile, precompile.base_gas_cost()))
    return pairs
