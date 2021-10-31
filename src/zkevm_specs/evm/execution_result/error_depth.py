from ..opcode import Opcode, call_opcodes
from ..step import Step
from ..table import CallContextTag


def error_depth(curr: Step, next: Step, r: int, opcode: Opcode):
    assert opcode in call_opcodes()

    depth = curr.call_context_lookup(CallContextTag.Depth)
    assert depth == 1024

    # TODO: Return to caller's state
