from ..instruction import Instruction, Transition
from ..opcode import Opcode


def push(instruction: Instruction):
    opcode = instruction.opcode_lookup()
    num_pushed = opcode - Opcode.PUSH1 + 1
    num_additional_pushed = num_pushed - 1

    value = instruction.stack_push()
    value_bytes = instruction.rlc_to_bytes(value, 32)
    selectors = instruction.continuous_selectors(num_additional_pushed, 31)

    for idx in range(32):
        index = instruction.curr.program_counter + num_pushed - idx
        if idx == 0 or selectors[idx - 1]:
            instruction.constrain_equal(value_bytes[idx], instruction.opcode_lookup_at(index))
        else:
            instruction.constrain_zero(value_bytes[idx])

    instruction.constrain_same_context_state_transition(
        opcode,
        rw_counter=Transition.delta(1),
        program_counter=Transition.delta(1 + num_pushed),
        stack_pointer=Transition.delta(-1),
    )
