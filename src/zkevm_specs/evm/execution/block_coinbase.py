from ...util.param import N_BYTES_ACCOUNT_ADDRESS
from ..instruction import Instruction, Transition
from ..table import BlockContextFieldTag
from ..opcode import Opcode


def coinbase(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.COINBASE)

    # in real circuit also check address raw data is 160 bit length (20 bytes)
    # check block table for coinbase address
    instruction.constrain_equal(
        instruction.block_context_lookup(BlockContextFieldTag.Coinbase),
        # NOTE: We can replace this with N_BYTES_WORD if we reuse the 32 byte RLC constraint in
        # all places. See: https://github.com/appliedzkp/zkevm-specs/issues/101
        instruction.rlc_to_fq(instruction.stack_push(), N_BYTES_ACCOUNT_ADDRESS),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(1),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
