from ..instruction import Instruction


def error_stack(instruction: Instruction):
    # retrieve op code associated to stack error
    opcode = instruction.opcode_lookup(True)
    instruction.responsible_opcode_lookup(opcode, instruction.curr.stack_pointer)

    instruction.constrain_error_state(
        instruction.rw_counter_offset + instruction.curr.reversible_write_counter
    )
