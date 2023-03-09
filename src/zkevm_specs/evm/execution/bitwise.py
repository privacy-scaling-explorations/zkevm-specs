from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import FixedTableTag
from ...util import FQ


def bitwise(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    a = instruction.stack_pop()
    b = instruction.stack_pop()
    c = instruction.stack_push()

    a8s = a.to_le_bytes()
    b8s = b.to_le_bytes()
    c8s = c.to_le_bytes()

    tag = FixedTableTag.BitwiseAnd + (opcode.n - Opcode.AND)

    for idx in range(32):
        instruction.fixed_lookup(FixedTableTag(tag), FQ(a8s[idx]), FQ(b8s[idx]), FQ(c8s[idx]))

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )
