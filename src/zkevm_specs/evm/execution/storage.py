from ..instruction import Instruction, Transition

def sload(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.SLOAD)
    address = instruction.stack_pop()
    # value = instruction.stack_pop()

def sstore(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.SSTORE)
    address = instruction.stack_pop()
    # value = instruction.stack_pop()
