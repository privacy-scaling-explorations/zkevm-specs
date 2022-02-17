# type: ignore
from ..instruction import Instruction, Transition
from ..table import BlockContextFieldTag
from ..opcode import Opcode


def coinbase(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.COINBASE)
    address = instruction.stack_push()
    # in real circuit also check address raw data is 160 bit length (20 bytes)
    # check block table for coinbase address
    instruction.constrain_equal(
        address,
        instruction.int_to_rlc(
            instruction.block_context_lookup(BlockContextFieldTag.Coinbase),
            # NOTE: We can replace this with N_BYTES_WORD if we reuse the 32
            # byte RLC constraint in all places.  See:
            # https://github.com/appliedzkp/zkevm-specs/issues/101
            20,
        ),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(1),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
