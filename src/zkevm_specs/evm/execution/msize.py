from ..instruction import Instruction, Transition
from ...util import N_BYTES_WORD, Word, FQ


def msize(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    instruction.constrain_equal_word(
        Word((instruction.curr.memory_word_size * N_BYTES_WORD, FQ(0))), instruction.stack_push()
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(1),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
