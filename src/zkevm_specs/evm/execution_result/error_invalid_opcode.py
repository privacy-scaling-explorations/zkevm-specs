from ..opcode import Opcode
from ..step import Step
from ..table import FixedTableTag


def error_invalid_opcode(curr: Step, next: Step, r: int, opcode: Opcode):
    curr.fixed_lookup(FixedTableTag.InvalidOpcode, [opcode])

    # TODO: Return to caller's state or go to next tx
