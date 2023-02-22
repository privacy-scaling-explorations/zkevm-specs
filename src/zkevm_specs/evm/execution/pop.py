from ..instruction import Instruction


def pop(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
