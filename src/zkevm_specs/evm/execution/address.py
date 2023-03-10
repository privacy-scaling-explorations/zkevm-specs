from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag
from ..opcode import Opcode


def address(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.ADDRESS)

    address = instruction.call_context_lookup(CallContextFieldTag.CalleeAddress).value()
    # Get callee address from call context and compare with stack top after push.
    instruction.constrain_equal_word(
        instruction.address_to_word(address),
        instruction.stack_push(),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
