from ..instruction import Instruction, Transition
from ..table import BlockContextFieldTag
from ..opcode import Opcode


def coinbase(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.COINBASE)
    address = instruction.stack_push()
    # in real circuit also check address raw data is 160 bit length (20 bytes)
    # check block table for coinbase address 
    instruction.constrain_equal(address,
        instruction.block_lookup(BlockContextFieldTag.Coinbase))

    instruction.constrain_same_context_state_transition(
        opcode,
        rw_counter=Transition.delta(1),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
