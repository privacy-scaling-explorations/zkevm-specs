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
            instruction.constrain_equal(precompile_return_len, calldata_len)
        elif precompile == Precompile.ECRECOVER:
            # The input different from 128 is allowed and is then right padded with zeros
            # We only ensure hat the return length is either 32 or 0.
            is_128 = instruction.is_equal(precompile_return_len, FQ(32))
            is_zero = instruction.is_equal(precompile_return_len, FQ.zero())
            instruction.constrain_equal(is_128 + is_zero, FQ.one())
        elif precompile == Precompile.BN254ADD:
            # input length is 128 bytes
            instruction.constrain_equal(calldata_len, FQ(128))
        elif precompile == Precompile.BN254SCALARMUL:
            # input length is 96 bytes
            instruction.constrain_equal(calldata_len, FQ(96))
        elif precompile == Precompile.BN254PAIRING:
            # input length is 192 * n bytes
            instruction.constrain_equal(FQ(calldata_len.n % 192), FQ.zero())
