from ..instruction import Instruction, Transition


def pop(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    y = instruction.stack_pop()

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(1),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )
