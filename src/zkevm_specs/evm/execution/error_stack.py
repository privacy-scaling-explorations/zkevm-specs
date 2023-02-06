from ...util import FQ
from ..instruction import Instruction, FixedTableTag
from ..opcode import Opcode
from ...util import N_BYTES_STACK


def stack_error(instruction: Instruction):
    # retrieve op code associated to stack error
    opcode = instruction.opcode_lookup(True)
    # lookup min or max stack pointer
    max_stack_pointer = FQ(Opcode(opcode.expr().n).max_stack_pointer())
    min_sp = Opcode(opcode.expr().n).min_stack_pointer()
    min_stack_pointer = FQ(min_sp if min_sp > 0 else 0)
    instruction.fixed_lookup(
        FixedTableTag.OpcodeStack, opcode, min_stack_pointer, max_stack_pointer
    )

    # check stack pointer is underflow or overflow
    is_overflow, _ = instruction.compare(
        instruction.curr.stack_pointer, FQ(min_stack_pointer), N_BYTES_STACK
    )
    is_underflow, _ = instruction.compare(
        FQ(max_stack_pointer), instruction.curr.stack_pointer, N_BYTES_STACK
    )
    instruction.constrain_bool(is_underflow)
    instruction.constrain_bool(is_overflow)

    # constrain one of [is_underflow, is_overflow] must be true when stack error happens
    instruction.constrain_equal(is_underflow + is_overflow, FQ(1))

    instruction.constrain_error_state(1 + instruction.curr.reversible_write_counter.n)
