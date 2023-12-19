from zkevm_specs.evm_circuit.precompile import Precompile
from ...util import FQ
from ..instruction import Instruction


class PrecompileGadget:
    address: FQ

    def __init__(
        self,
        instruction: Instruction,
        callee_addr: FQ,
        precompile_return_len: FQ,
        calldata_len: FQ,
    ):
        # next execution state must be one of precompiles
        instruction.constrain_equal(instruction.precompile(callee_addr), FQ.one())

        ### precompiles' specific constraints
        precompile = Precompile(callee_addr)
        if precompile == Precompile.DATACOPY:
            # input length is the same as return data length
            instruction.constrain_equal(calldata_len, precompile_return_len)
