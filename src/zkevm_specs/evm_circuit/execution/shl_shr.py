from ...util import FQ, Word
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
    shift: Word,
    dividend: Word,
    divisor: Word,
    quotient: Word,
    remainder: Word,
    pop1: Word,
    pop2: Word,
    push: Word,
):
    is_shr = 1 - is_shl
    divisor_is_zero = instruction.is_zero_word(divisor)
    shift_le_bytes = shift.to_le_bytes()

    # Constrain stack pops and pushes as:
    # - for SHL, two pops are shift and quotient, and push is dividend.
    # - for SHR, two pops are shift and dividend, and push is quotient.
    instruction.constrain_equal_word(pop1, shift)
    instruction.constrain_equal_word(
        pop2,
        quotient.select(is_shl) | dividend.select(is_shr),
    )
    instruction.constrain_equal_word(
        push, dividend.select(is_shl) | quotient.select(is_shr * (1 - divisor_is_zero))
    )
    instruction.constrain_zero(shf0 - FQ(shift_le_bytes[0]))

    # Constrain shift == shift.cells[0] when divisor != 0.
    instruction.constrain_equal_word(
        shift.select(1 - divisor_is_zero),
        Word((shift_le_bytes[0], FQ(0))).select(1 - divisor_is_zero),
    )

    # Constrain remainder < divisor when divisor != 0.
    remainder_lt_divisor, _ = instruction.compare_word(remainder, divisor)
    instruction.constrain_zero((1 - divisor_is_zero) * (1 - remainder_lt_divisor))

    # Constrain remainder == 0 for SHL.
    remainder_is_zero = instruction.is_zero_word(remainder)
    instruction.constrain_zero(is_shl * (1 - remainder_is_zero))

    # Constrain overflow == 0 for SHR.
    overflow = instruction.mul_add_words(quotient, divisor, remainder, dividend)
    instruction.constrain_zero(is_shr * overflow)

    # Constrain divisor_lo == 2^shf0 when shf0 < 128, and
    # divisor_hi == 2^(128 - shf0) otherwise.
    divisor_lo, divisor_hi = divisor.to_lo_hi()
    if (1 - divisor_is_zero) == 1:
        instruction.pow2_lookup(shf0, divisor_lo, divisor_hi)


def gen_witness(opcode: FQ, pop1: Word, pop2: Word, push: Word):
    is_shl = Opcode.SHR - opcode
    shift = pop1
    shf0 = shift.to_le_bytes()[0]
    divisor = Word(1 << shf0.n) if shf0 == shift.int_value() else Word(0)
    if is_shl.n == 1:
        dividend = push
        quotient = pop2
        remainder = Word(0)
    else:  # SHR
        dividend = pop2
        quotient = push
        remainder = Word(dividend.int_value() - quotient.int_value() * divisor.int_value())

    return (
        is_shl,
        shf0,
        shift,
        dividend,
        divisor,
        quotient,
        remainder,
    )
