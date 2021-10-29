from ..opcode import Opcode, call_opcodes
from ..step import Step
from ..table import CallTableTag


def error_depth(curr: Step, next: Step, r: int, opcode: Opcode):
    assert opcode in call_opcodes()

    depth = curr.call_lookup(CallTableTag.Depth)
    assert depth == 1024

    # TODO: Return to caller's state
