from ...util.param import N_BYTES_ACCOUNT_ADDRESS, N_BYTES_U64
from ...util import Word, FQ
from ..instruction import Instruction, Transition
from ..table import BlockContextFieldTag
from ..opcode import Opcode


def blockctx(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    # get block context op element
    if opcode == Opcode.COINBASE:
        op = BlockContextFieldTag.Coinbase
        ctx_word = instruction.address_to_word(instruction.block_context_lookup(op).value())
    elif opcode == Opcode.TIMESTAMP:
        op = BlockContextFieldTag.Timestamp
        ctx_word = Word((instruction.block_context_lookup(op).value(), FQ(0)))
    elif opcode == Opcode.NUMBER:
        op = BlockContextFieldTag.Number
        ctx_word = Word((instruction.block_context_lookup(op).value(), FQ(0)))
    elif opcode == Opcode.GASLIMIT:
        op = BlockContextFieldTag.GasLimit
        ctx_word = Word((instruction.block_context_lookup(op).value(), FQ(0)))
    elif opcode == Opcode.DIFFICULTY:
        op = BlockContextFieldTag.Difficulty
        ctx_word = instruction.block_context_lookup(op)
    elif opcode == Opcode.BASEFEE:
        op = BlockContextFieldTag.BaseFee
        ctx_word = instruction.block_context_lookup(op)
    elif opcode == Opcode.CHAINID:
        op = BlockContextFieldTag.ChainId
        ctx_word = Word((instruction.block_context_lookup(op).value(), FQ(0)))

    # check block table for corresponding op data
    instruction.constrain_equal_word(ctx_word, instruction.stack_push())

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(1),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
