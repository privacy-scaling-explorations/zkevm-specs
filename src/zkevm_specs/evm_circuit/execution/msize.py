from ..instruction import Instruction, Transition
from ...util import N_BYTES_WORD, Word


def msize(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    instruction.constrain_equal_word(
        Word.from_lo(instruction.curr.memory_word_size * N_BYTES_WORD), instruction.stack_push()
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(1),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
