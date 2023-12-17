from ...util import FQ
from ..instruction import Instruction


# PrecompileGadget helps execution state transition between callop and precompiles
# We only verify the data (input and output data of precompiles) consistence between transitions.
class PrecompileGadget:
    address: FQ

    def __init__(
        self,
        instruction: Instruction,
        callee_addr: FQ,
        input_rlc: FQ,
        output_rlc: FQ,
    ):
        # next execution state must be one of precompile execution states
        instruction.constrain_equal(instruction.precompile(callee_addr), FQ.one())

        # verify current data is the same as the ones in next execution state
        next_input_rlc: FQ = instruction.next.aux_data[0]
        next_output_rlc: FQ = instruction.next.aux_data[1]
        instruction.constrain_equal(input_rlc, next_input_rlc)
        instruction.constrain_equal(output_rlc, next_output_rlc)

        # FIXME, Q: do we need return_data_rlc? what is the diff between output??

        # FIXME how to connect rlced input, output with real in/out in `word`, or we don't have to?
