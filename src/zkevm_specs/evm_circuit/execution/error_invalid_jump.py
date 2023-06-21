from ...util import FQ
from ..instruction import Instruction
from ..opcode import Opcode
from ...util import N_BYTES_PROGRAM_COUNTER


def error_invalid_jump(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    # current executing op code must be JUMP or JUMPI
    instruction.constrain_in(opcode, [FQ(Opcode.JUMP), FQ(Opcode.JUMPI)])
    _, is_jumpi = instruction.pair_select(opcode, Opcode.JUMP, Opcode.JUMPI)
    code_length = instruction.bytecode_length(instruction.curr.code_hash)
    dest = instruction.stack_pop()
    # if `JUMPI`, pop `condition`
    if is_jumpi == FQ(1):
        condition = instruction.stack_pop()
        # if condition is zero, jump will not happen, so constrain condition not zero
        instruction.constrain_not_zero_word(condition)
    # lookup value from bytecode table.  N_BYTES_PROGRAM_COUNTER is 64 bits
    dest_value = instruction.word_to_u64(dest)

    within_range, _ = instruction.compare(dest_value, code_length, N_BYTES_PROGRAM_COUNTER)

    # if not out of range, check `dest` is invalid
    if within_range == FQ(1):
        value, is_code = instruction.bytecode_lookup_pair(instruction.curr.code_hash, dest_value)
        # value is not `JUMPDEST` or `is_code` is false
        is_jump_dest = value == Opcode.JUMPDEST
        instruction.constrain_zero(is_code * FQ(is_jump_dest))

        instruction.constrain_error_state(
            2 + is_jumpi.n + instruction.curr.reversible_write_counter.n
        )
