from ...util import RLC
from ..instruction import Instruction, Transition
from ..opcode import Opcode


def shl_shr(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    a = instruction.stack_pop()
    shift = instruction.stack_pop()
    b = instruction.stack_push()

    is_shl = Opcode.SHR - opcode
    shf0 = instruction.bytes_to_fq(shift.le_bytes[:1])
    shf_lt256 = instruction.is_zero(instruction.sum(shift.le_bytes[1:]))

    if is_shl == 1:
        dividend = b
        divisor = instruction.select(shf_lt256, RLC(1 << shf0.n), RLC(0))
        quotient = a
        remainder = RLC(0)
    else:
        dividend = a
        divisor = instruction.select(shf_lt256, RLC(1 << shf0.n), RLC(0))
        quotient = b
        remainder = instruction.rlc_encode(
            dividend.int_value - divisor.int_value * quotient.int_value, 32
        )

    instruction.mul_add_words(quotient, divisor, remainder, dividend)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )
