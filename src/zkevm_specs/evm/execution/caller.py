from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag
from ..opcode import Opcode


def caller(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.CALLER)
    address = instruction.stack_push()

    # check [rw_table, call_context] table for caller address
    instruction.constrain_equal(
        address,
        instruction.bytes_to_rlc(
            instruction.int_to_bytes(
                instruction.call_context_lookup(CallContextFieldTag.CallerAddress),
                20,
            )
        ),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
