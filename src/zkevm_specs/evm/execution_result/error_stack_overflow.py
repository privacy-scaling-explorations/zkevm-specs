from ..opcode import Opcode
from ..step import Step
from ..table import FixedTableTag


def error_stack_overflow(curr: Step, next: Step, r: int, opcode: Opcode):
    curr.fixed_lookup(FixedTableTag.StackOverflow, [opcode, curr.call.stack_pointer])

    # TODO: Return to caller's state or go to next tx
