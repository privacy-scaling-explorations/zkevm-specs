from ..instruction import Instruction, Transition
from ..table import BlockContextFieldTag
from ..opcode import Opcode


def timestamp(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.TIMESTAMP)
    timestamp = instruction.stack_push()
    # check block table for timestamp
    instruction.constrain_equal(
        timestamp,
        instruction.block_context_lookup(BlockContextFieldTag.Timestamp),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(1),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
