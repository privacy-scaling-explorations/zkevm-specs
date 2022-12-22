from enum import IntEnum
from typing import Final, Dict, Tuple, List

from ..util.param import *


class Precompile(IntEnum):
    ECRECOVER = 0x01
    SHA256 = 0x02
    RIPEMD160 = 0x03
    DATACOPY = 0x04
    BIGMODEXP = 0x05
    BN256ADD = 0x06
    BN256SCALARMUL = 0x07
    BN256PAIRING = 0x08
    BLAKE2F = 0x09

    def base_gas_cost(self) -> int:
        return PRECOMPILE_INFO_MAP[self].base_gas

    def is_push(self) -> bool:
        return False

    def is_dup(self) -> bool:
        return False

    def is_swap(self) -> bool:
        return False

    def max_stack_pointer(self) -> int:
        return 0


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


PRECOMPILE_INFO_MAP: Final[Dict[Precompile, PrecompileInfo]] = dict(
    {
        Precompile.ECRECOVER: PrecompileInfo(EcrecoverGas),
        Precompile.SHA256: PrecompileInfo(Sha256BaseGas),
        Precompile.RIPEMD160: PrecompileInfo(Ripemd160BaseGas),
        Precompile.DATACOPY: PrecompileInfo(IdentityBaseGas),
        Precompile.BIGMODEXP: PrecompileInfo(BigModExpBaseGas),
        Precompile.BN256ADD: PrecompileInfo(Bn256AddGas),
        Precompile.BN256SCALARMUL: PrecompileInfo(Bn256ScalarMulGas),
        Precompile.BN256PAIRING: PrecompileInfo(Bn256PairingBaseGas),
        Precompile.BLAKE2F: PrecompileInfo(Blake2fBaseGas),
    }
)


def valid_precompiles() -> List[Precompile]:
    return list(Precompile)


def base_gas_cost_pairs() -> List[Tuple[Precompile, int]]:
    pairs = []
    for precompile in valid_precompiles():
        if precompile.base_gas_cost() > 0:
            pairs.append((precompile, precompile.base_gas_cost()))
    return pairs
