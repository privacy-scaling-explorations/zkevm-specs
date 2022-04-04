from ..instruction import Instruction, Transition
from ..opcode import Opcode


def shr(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    a = instruction.stack_pop()
    shift = instruction.stack_pop()

    instruction.constrain_equal(
        instruction.word_shift_right(a, shift),
        instruction.stack_push(),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )
