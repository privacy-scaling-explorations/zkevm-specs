from ..instruction import Instruction, Transition
from ..table import BlockContextFieldTag
from ...util import FQ

def blockhash(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    block_number = instruction.rlc_to_fq(instruction.stack_pop(), 8)
    
    current_block_number = instruction.block_context_lookup(BlockContextFieldTag.Number)
    is_current_bigger = instruction.compare(block_number, current_block_number.expr(), 8)[0]

    diff = current_block_number.expr() - block_number if is_current_bigger == 1 else block_number - current_block_number.expr()
    is_invalid_range = 1 - (
        is_current_bigger
        * instruction.compare(diff, FQ(257), 8)[0]
    )
    op = BlockContextFieldTag.HistoryHash
    block_hash = FQ(0) if is_invalid_range == 1 else instruction.block_context_lookup(op, block_number)

    instruction.constrain_equal(
        instruction.select(is_invalid_range, FQ(0), block_hash),
        instruction.stack_push()
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.same(),
    )
