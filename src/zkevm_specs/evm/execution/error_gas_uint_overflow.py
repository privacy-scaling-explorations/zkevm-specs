from ..instruction import Instruction, Transition


def gas_uint_overflow(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
