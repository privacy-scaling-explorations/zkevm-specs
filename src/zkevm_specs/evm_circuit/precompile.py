from enum import IntEnum
from typing import Final, Dict, Tuple, List

from ..util.param import *
from .execution_state import ExecutionState


class Precompile(IntEnum):
    ECRECOVER = 0x01
    SHA256 = 0x02
    RIPEMD160 = 0x03
    DATACOPY = 0x04
    BIGMODEXP = 0x05
    BN254ADD = 0x06
    BN254SCALARMUL = 0x07
    BN254PAIRING = 0x08
    BLAKE2F = 0x09

    def execution_state(self) -> ExecutionState:
        return PRECOMPILE_INFO_MAP[self].execution_state

    def base_gas_cost(self) -> int:
        return PRECOMPILE_INFO_MAP[self].base_gas

    @classmethod
    def len(cls) -> int:
        return len(cls)


class PrecompileInfo:
    """
    Precompile information.
    """

    base_gas: int
    execution_state: ExecutionState

    def __init__(
        self,
        base_gas: int,
        execution_state: ExecutionState,
    ) -> None:
        self.base_gas = base_gas
        self.execution_state = execution_state


PRECOMPILE_INFO_MAP: Final[Dict[Precompile, PrecompileInfo]] = dict(
    {
        Precompile.ECRECOVER: PrecompileInfo(EcrecoverGas, ExecutionState.ECRECOVER),
        Precompile.SHA256: PrecompileInfo(Sha256BaseGas, ExecutionState.SHA256),
        Precompile.RIPEMD160: PrecompileInfo(Ripemd160BaseGas, ExecutionState.RIPEMD160),
        Precompile.DATACOPY: PrecompileInfo(IdentityBaseGas, ExecutionState.DATACOPY),
        Precompile.BIGMODEXP: PrecompileInfo(BigModExpBaseGas, ExecutionState.BIGMODEXP),
        Precompile.BN254ADD: PrecompileInfo(Bn254AddGas, ExecutionState.BN254_ADD),
        Precompile.BN254SCALARMUL: PrecompileInfo(
            Bn254ScalarMulGas, ExecutionState.BN254_SCALAR_MUL
        ),
        Precompile.BN254PAIRING: PrecompileInfo(Bn254PairingBaseGas, ExecutionState.BN254_PAIRING),
        Precompile.BLAKE2F: PrecompileInfo(Blake2fBaseGas, ExecutionState.BLAKE2F),
    }
)


def valid_precompiles() -> List[Precompile]:
    return list(Precompile)


def precompile_info_pairs() -> List[Tuple[ExecutionState, Precompile, int]]:
    pairs = []
    for precompile in valid_precompiles():
        pairs.append((precompile.execution_state(), precompile, precompile.base_gas_cost()))
    return pairs
