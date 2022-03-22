from ...util.param import N_BYTES_ACCOUNT_ADDRESS, N_BYTES_U64
from ..instruction import Instruction, Transition
from ..table import BlockContextFieldTag
from ..opcode import Opcode


def blockctx(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, instruction.curr.execution_state.responsible_opcode()[0])

    # get block context op element
    if opcode == Opcode.COINBASE:
        op = BlockContextFieldTag.Coinbase
        ctx_expr = instruction.rlc_to_fq_exact(instruction.stack_push(), N_BYTES_ACCOUNT_ADDRESS)
    elif opcode == Opcode.TIMESTAMP:
        op = BlockContextFieldTag.Timestamp
        ctx_expr = instruction.rlc_to_fq_exact(instruction.stack_push(), N_BYTES_U64)
    elif opcode == Opcode.NUMBER:
        op = BlockContextFieldTag.Number
        ctx_expr = instruction.rlc_to_fq_exact(instruction.stack_push(), N_BYTES_U64)
    elif opcode == Opcode.DIFFICULTY:
        op = BlockContextFieldTag.Difficulty
        ctx_expr = instruction.stack_push().expr()
    elif opcode == Opcode.GASLIMIT:
        op = BlockContextFieldTag.GasLimit
        ctx_expr = instruction.rlc_to_fq_exact(instruction.stack_push(), N_BYTES_U64)
    elif opcode == Opcode.BASEFEE:
        op = BlockContextFieldTag.BaseFee
        ctx_expr = instruction.stack_push().expr()

    # check block table for coinbase address
    instruction.constrain_equal(instruction.block_context_lookup(op), ctx_expr)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(1),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
