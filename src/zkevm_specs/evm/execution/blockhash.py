from ..instruction import Instruction, Transition
from ..table import BlockContextFieldTag
from ...util import FQ, N_BYTES_U64

def blockhash(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    block_number = instruction.rlc_to_fq(instruction.stack_pop(), N_BYTES_U64)
    
    current_block_number = instruction.block_context_lookup(BlockContextFieldTag.Number)
    # get value that was pushed to stack (RLC-encoded)
    block_hash = instruction.stack_push()

    # comparing block_number and current_block_number
    block_lt, _ = instruction.compare(block_number, current_block_number, N_BYTES_U64)
    diff_lt, _ = instruction.compare(current_block_number, FQ(256) + block_number, 2)

    # get the expected block hash depending on the above conditions (RLC-encoded)
    if instruction.is_equal(block_lt * diff_lt, FQ.one()) == FQ.one():
        expected_block_hash = instruction.block_context_lookup(
            BlockContextFieldTag.HistoryHash,
            block_number,
        )
    else:
        expected_block_hash = FQ.zero()

    # block hash is as expected
    instruction.constrain_equal(block_hash, expected_block_hash)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.same(),
    )
