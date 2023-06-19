from ..instruction import Instruction, Transition
from ..table import BlockContextFieldTag
from ..opcode import Opcode


def blockctx(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    # get block context op element
    if opcode == Opcode.COINBASE:
        op = BlockContextFieldTag.Coinbase
    elif opcode == Opcode.TIMESTAMP:
        op = BlockContextFieldTag.Timestamp
    elif opcode == Opcode.NUMBER:
        op = BlockContextFieldTag.Number
    elif opcode == Opcode.GASLIMIT:
        op = BlockContextFieldTag.GasLimit
    elif opcode == Opcode.DIFFICULTY:
        op = BlockContextFieldTag.Difficulty
    elif opcode == Opcode.BASEFEE:
        op = BlockContextFieldTag.BaseFee
    elif opcode == Opcode.CHAINID:
        op = BlockContextFieldTag.ChainId
    ctx_word = instruction.block_context_lookup_word(op)

    # check block table for corresponding op data
    instruction.constrain_equal_word(ctx_word, instruction.stack_push())

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(1),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
