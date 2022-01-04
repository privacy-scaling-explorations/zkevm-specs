from ..instruction import Instruction, Transition

# TODO:
# constraint op?
# combine to storage?

def sload(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.SLOAD)
    address = instruction.stack_pop()
    # TODO:
    # value = instruction.stack_pop()

def sstore(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.SSTORE)

    address = instruction.stack_pop()
    value = instruction.stack_pop()

    rw_counter_end_of_reversion = instruction.call_context_lookup(CallContextFieldTag.RWCounterEndOfReversion)
    is_persistent = instruction.call_context_lookup(CallContextFieldTag.IsPersistent)
