from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ...util import FQ, RLC


def sdiv_smod(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    pop1 = instruction.stack_pop()
    pop2 = instruction.stack_pop()
    push = instruction.stack_push()

    (
        quotient,
        divisor,
        remainder,
        dividend,
        quotient_abs,
        divisor_abs,
        remainder_abs,
        dividend_abs,
    ) = gen_witness(instruction, opcode, pop1, pop2, push)
    check_witness(
        instruction,
        quotient,
        divisor,
        remainder,
        dividend,
        quotient_abs,
        divisor_abs,
        remainder_abs,
        dividend_abs,
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )


def check_witness(
    instruction: Instruction,
    quotient: RLC,
    divisor: RLC,
    remainder: RLC,
    dividend: RLC,
    quotient_abs: RLC,
    divisor_abs: RLC,
    remainder_abs: RLC,
    dividend_abs: RLC,
):
    quotient_is_neg = instruction.word_is_neg(quotient)
    divisor_is_neg = instruction.word_is_neg(divisor)
    remainder_is_neg = instruction.word_is_neg(remainder)
    dividend_is_neg = instruction.word_is_neg(dividend)

    quotient_is_non_zero = 1 - instruction.word_is_zero(quotient)
    divisor_is_non_zero = 1 - instruction.word_is_zero(divisor)
    remainder_is_non_zero = 1 - instruction.word_is_zero(remainder)

    # Constrain the ABS values of quotient, divisor, remainder and dividend.
    instruction.constrain_equal(
        FQ(1), instruction.word_is_equal(quotient_abs, instruction.abs_word(quotient))
    )
    instruction.constrain_equal(
        FQ(1), instruction.word_is_equal(divisor_abs, instruction.abs_word(divisor))
    )
    instruction.constrain_equal(
        FQ(1), instruction.word_is_equal(remainder_abs, instruction.abs_word(remainder))
    )
    instruction.constrain_equal(
        FQ(1), instruction.word_is_equal(dividend_abs, instruction.abs_word(dividend))
    )

    # Function `mul_add_words` constrains `|quotient| * |divisor| + |remainder| = |dividend|`.
    overflow = instruction.mul_add_words(quotient_abs, divisor_abs, remainder_abs, dividend_abs)
    # Constrain overflow == 0.
    instruction.constrain_zero(overflow)

    # Constrain abs(remainder) < abs(divisor) when divisor != 0.
    remainder_lt_divisor, _ = instruction.compare_word(remainder_abs, divisor_abs)
    instruction.constrain_zero((1 - remainder_lt_divisor) * divisor_is_non_zero)

    # Constrain sign(dividend) == sign(remainder) when quotient, divisor and
    # remainder are all non-zero.
    condition = quotient_is_non_zero * divisor_is_non_zero * remainder_is_non_zero
    instruction.constrain_equal(dividend_is_neg * condition, remainder_is_neg * condition)

    # For a special `SDIV` case, when input `dividend = -(1 << 255)` and `divisor = -1`,
    # the quotient result should be `1 << 255`. But a `signed` word could only express
    # `signed` value from `-(1 << 255)` to `(1 << 255) - 1`. So below constraint
    # `sign(dividend) == sign(divisor) ^ sign(quotient)` cannot be applied for this case.
    dividend_is_signed_overflow = instruction.word_is_neg(dividend_abs)

    # Constrain sign(dividend) == sign(divisor) ^ sign(quotient) when both
    # quotient and divisor are non-zero and dividend is not signed overflow.
    condition = quotient_is_non_zero * divisor_is_non_zero * (1 - dividend_is_signed_overflow)
    instruction.constrain_equal(
        (1 - dividend_is_neg) * condition,
        ((quotient_is_neg * divisor_is_neg) + (1 - quotient_is_neg) * (1 - divisor_is_neg))
        * condition,
    )


def gen_witness(instruction: Instruction, opcode: FQ, pop1: RLC, pop2: RLC, push: RLC):
    # The opcode value for SDIV and SMOD are 5 and 7. When the opcode is SDIV,
    # `Opcode.SMOD - opcode` is 2. To make `is_sdiv` be either 0 or 1, we need
    # to divide the product by 2, which is equivalent to multiply it by
    # inversion of 2.
    is_sdiv = (Opcode.SMOD - opcode) * FQ(2).inv()

    pop1_abs = get_abs(pop1.int_value)
    pop2_abs = get_abs(pop2.int_value)
    push_abs = get_abs(push.int_value)
    pop1_is_neg = instruction.word_is_neg(pop1)
    pop2_is_neg = instruction.word_is_neg(pop2)
    pop2_is_zero = instruction.word_is_zero(pop2)

    # Avoid word overflow for SMOD.
    sdiv_remainder_int = abs(pop1_abs - push_abs * pop2_abs)
    sdiv_remainder_int = sdiv_remainder_int if sdiv_remainder_int < 1 << 256 else 0
    sdiv_remainder = instruction.select(
        pop1_is_neg, RLC(get_neg(sdiv_remainder_int)), RLC(sdiv_remainder_int)
    )
    smod_remainder = instruction.select(pop2_is_zero, pop1, push)

    # Avoid dividing by zero.
    pop2_abs = instruction.select(pop2_is_zero, RLC(1), RLC(pop2_abs)).int_value
    smod_quotient = instruction.select(pop2_is_zero, RLC(0), RLC(pop1_abs // pop2_abs))
    smod_quotient = instruction.select(
        instruction.is_equal(pop1_is_neg, pop2_is_neg),
        smod_quotient,
        RLC(get_neg(smod_quotient.int_value)),
    )

    quotient = instruction.select(is_sdiv, push, smod_quotient)
    divisor = pop2
    remainder = instruction.select(is_sdiv, sdiv_remainder, smod_remainder)
    dividend = pop1

    quotient_abs = RLC(get_abs(quotient.int_value))
    divisor_abs = RLC(get_abs(divisor.int_value))
    remainder_abs = RLC(get_abs(remainder.int_value))
    dividend_abs = RLC(get_abs(dividend.int_value))

    return (
        quotient,
        divisor,
        remainder,
        dividend,
        quotient_abs,
        divisor_abs,
        remainder_abs,
        dividend_abs,
    )


def get_abs(x: int) -> int:
    return get_neg(x) if is_neg(x) else x


def get_neg(x: int) -> int:
    return 0 if x == 0 else (1 << 256) - x


def is_neg(x: int) -> int:
    return x >> 255
