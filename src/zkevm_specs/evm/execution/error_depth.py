from ...util import FQ
from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import CallContextFieldTag


def error_depth(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    # current executing op code must be CALL-family
    instruction.constrain_in(
        opcode,
        [FQ(Opcode.CALL), FQ(Opcode.CALLCODE), FQ(Opcode.DELEGATECALL), FQ(Opcode.STATICCALL)]
    )

    is_call, is_callcode, is_delegatecall, is_staticcall = instruction.multiple_select(
        opcode, (Opcode.CALL, Opcode.CALLCODE, Opcode.DELEGATECALL, Opcode.STATICCALL)
    )

    stack_delta = 0
    if is_call or is_callcode:
        stack_delta -= 7
    elif is_delegatecall or is_delegatecall:
        stack_delta -= 6

    # next step must have zero on stack top
    is_zero = instruction.stack_push()
    stack_delta += 1
    instruction.constrain_equal(is_zero, FQ(0))

    # check the call depth
    depth = instruction.call_context_lookup(CallContextFieldTag.Depth)
    instruction.constrain_equal(depth, FQ(1025))

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(stack_delta)
    )
