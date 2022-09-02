from ...util import FQ, RLC
from ..instruction import Instruction, Transition
from ..opcode import Opcode


def shl_shr(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    pop1 = instruction.stack_pop()
    pop2 = instruction.stack_pop()
    push = instruction.stack_push()

    (
        is_shl,
        shf0,
        shift,
        dividend,
        divisor,
        quotient,
        remainder,
    ) = gen_witness(opcode, pop1, pop2, push)
    check_witness(
        instruction,
        is_shl,
        shf0,
        shift,
        dividend,
        divisor,
        quotient,
        remainder,
        pop1,
        pop2,
        push,
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )


def check_witness(
    instruction: Instruction,
    is_shl: FQ,
    shf0: FQ,
    shift: RLC,
    dividend: RLC,
    divisor: RLC,
    quotient: RLC,
    remainder: RLC,
    pop1: RLC,
    pop2: RLC,
    push: RLC,
):
    is_shr = 1 - is_shl
    divisor_is_zero = instruction.word_is_zero(divisor)

    # Constrain stack pops and pushes as:
    # - for SHL, two pops are shift and quotient, and push is dividend.
    # - for SHR, two pops are shift and dividend, and push is quotient.
    instruction.constrain_equal(pop1.expr(), shift.expr())
    instruction.constrain_equal(
        pop2.expr(),
        is_shl * quotient.expr() + is_shr * dividend.expr(),
    )
    instruction.constrain_equal(
        push.expr(), (is_shl * dividend.expr() + is_shr * quotient.expr()) * (1 - divisor_is_zero)
    )

    # Constrain shift == shift.cells[0] when divisor != 0.
    instruction.constrain_zero(
        (1 - divisor_is_zero) * (shift.expr() - shift.le_bytes[0]),
    )

    # Constrain remainder < divisor when divisor != 0.
    remainder_lt_divisor, _ = instruction.compare_word(remainder, divisor)
    instruction.constrain_zero((1 - divisor_is_zero) * (1 - remainder_lt_divisor))

    # Constrain remainder == 0 for SHL.
    remainder_is_zero = instruction.word_is_zero(remainder)
    instruction.constrain_zero(is_shl * (1 - remainder_is_zero))

    # Constrain overflow == 0 for SHR.
    overflow = instruction.mul_add_words(quotient, divisor, remainder, dividend)
    instruction.constrain_zero(is_shr * overflow)

    # Constrain divisor_lo == 2^shf0 when shf0 < 128, and
    # divisor_hi == 2^(128 - shf0) otherwise.
    divisor_lo = instruction.bytes_to_fq(divisor.le_bytes[:16])
    divisor_hi = instruction.bytes_to_fq(divisor.le_bytes[16:])
    if (1 - divisor_is_zero) == 1:
        instruction.pow2_lookup(shf0, divisor_lo, divisor_hi)


def gen_witness(opcode: FQ, pop1: RLC, pop2: RLC, push: RLC):
    is_shl = Opcode.SHR - opcode
    shift = pop1
    shf0 = shift.le_bytes[0]
    divisor = RLC(1 << shf0) if shf0 == shift.int_value else RLC(0)
    if is_shl.n == 1:
        dividend = push
        quotient = pop2
        remainder = RLC(0)
    else:  # SHR
        dividend = pop2
        quotient = push
        remainder = RLC(dividend.int_value - quotient.int_value * divisor.int_value)

    return (
        is_shl,
        shf0,
        shift,
        dividend,
        divisor,
        quotient,
        remainder,
    )
