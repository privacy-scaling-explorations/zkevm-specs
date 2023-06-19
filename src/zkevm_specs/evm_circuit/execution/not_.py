from ..instruction import Instruction, Transition, FixedTableTag
from ...util import FQ


def not_opcode(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    a = instruction.stack_pop()
    a_le_bytes = a.to_le_bytes()
    b = instruction.stack_push()
    b_le_bytes = b.to_le_bytes()

    for i in range(32):
        byte_a = FQ(a_le_bytes[i])
        byte_b = FQ(b_le_bytes[i])
        instruction.fixed_lookup(FixedTableTag.BitwiseXor, byte_a, byte_b, FQ(255))

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.same(),
    )
