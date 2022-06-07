from ...util import RLC
from ..instruction import Instruction, Transition


def shl(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    a = instruction.stack_pop()
    shift = instruction.stack_pop()
    b = instruction.stack_push()

    shf0 = instruction.bytes_to_fq(shift.le_bytes[:1])
    shf_lt256 = instruction.is_zero(instruction.sum(shift.le_bytes[1:]))
    mul = instruction.select(shf_lt256, RLC(1 << shf0.n), RLC(0))
    instruction.mul_add_words(a, mul, RLC(0), b)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )
