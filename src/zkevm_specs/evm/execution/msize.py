from ..instruction import Instruction
from ...util import N_BYTES_WORD


def msize(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    value = instruction.stack_push()

    instruction.constrain_equal(value, instruction.curr.memory_word_size * N_BYTES_WORD)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
