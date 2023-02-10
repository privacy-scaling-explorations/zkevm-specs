from ..instruction import Instruction


def stack_error(instruction: Instruction):
    # retrieve op code associated to stack error
    opcode = instruction.opcode_lookup(True)
    instruction.responsible_opcode_lookup(opcode, instruction.curr.stack_pointer)

    instruction.constrain_error_state(1 + instruction.curr.reversible_write_counter.n)
