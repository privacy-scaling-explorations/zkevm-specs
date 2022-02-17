# type: ignore
from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag
from ..opcode import Opcode


def callvalue(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.CALLVALUE)

    # check [rw_table, call_context] table for call value and compare against
    # stack top after push.
    instruction.constrain_equal(
        instruction.call_context_lookup(CallContextFieldTag.Value),
        instruction.stack_push(),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
