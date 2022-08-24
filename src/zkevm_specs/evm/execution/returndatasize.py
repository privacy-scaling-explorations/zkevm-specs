from ..opcode import Opcode
from ...util import N_BYTES_MEMORY_ADDRESS
from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag
from ..opcode import Opcode


def returndatasize(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.RETURNDATASIZE)

    # check [rw_table, call_context] table for last call return data length and compare
    # against stack top after push.
    instruction.constrain_equal(
        instruction.call_context_lookup(CallContextFieldTag.LastCalleeReturnDataLength),
        # NOTE: We can replace this with N_BYTES_WORD if we reuse the 32 byte RLC constraint in
        # all places. See: https://github.com/privacy-scaling-explorations/zkevm-specs/issues/101
        instruction.rlc_to_fq(instruction.stack_push(), N_BYTES_MEMORY_ADDRESS),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
