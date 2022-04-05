from zkevm_specs.util.param import N_BYTES_WORD
from ..instruction import Instruction, Transition
from ..table import BlockContextFieldTag
from ..opcode import Opcode


def chainid(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.CHAINID)

    # check block table for CHAINID value
    instruction.constrain_equal(
        instruction.stack_push(), instruction.block_context_lookup(BlockContextFieldTag.ChainId)
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(1),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
