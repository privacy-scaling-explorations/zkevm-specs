from ..instruction import Instruction


# Gadget for invalid opcodes. It verifies by a fixed lookup for ResponsibleOpcode.
def error_invalid_opcode(instruction: Instruction):
    # Fixed lookup for invalid opcode.
    opcode = instruction.opcode_lookup(True)
    instruction.responsible_opcode_lookup(opcode)

    instruction.constrain_error_state(instruction.curr.reversible_write_counter.n)
