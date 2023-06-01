from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag
from ..opcode import Opcode


def caller(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.CALLER)

    address_word = instruction.call_context_lookup_word(CallContextFieldTag.CallerAddress)
    # check [rw_table, call_context] table for caller address and compare with
    # stack top after push
    instruction.constrain_equal_word(
        address_word,
        instruction.stack_push(),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
