from ...util.param import N_BYTES_U64
from ..instruction import Instruction, Transition
from ..table import BlockContextFieldTag
from ..opcode import Opcode


def number(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.NUMBER)

    # check block table for number
    instruction.constrain_equal(
        instruction.block_context_lookup(BlockContextFieldTag.Number),
        instruction.rlc_to_fq_exact(instruction.stack_push(), N_BYTES_U64),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(1),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
