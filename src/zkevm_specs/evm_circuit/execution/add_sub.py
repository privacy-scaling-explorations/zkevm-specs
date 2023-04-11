from ..instruction import Instruction, Transition
from ..opcode import Opcode


def add_sub(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    is_sub, _ = instruction.pair_select(opcode, Opcode.SUB, Opcode.ADD)

    a = instruction.stack_pop()
    b = instruction.stack_pop()
    c = instruction.stack_push()

    instruction.constrain_equal_word(
        instruction.add_words([instruction.select_word(is_sub, c, a), b])[0],
        instruction.select_word(is_sub, a, c),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )
