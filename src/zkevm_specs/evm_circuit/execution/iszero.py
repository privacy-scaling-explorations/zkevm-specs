from ..instruction import Instruction, Transition
from ...util import Word


def iszero(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    value = instruction.stack_pop()

    instruction.constrain_equal_word(
        Word.from_lo(instruction.is_zero_word(value)),
        instruction.stack_push(),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.same(),
    )
