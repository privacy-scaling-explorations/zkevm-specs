from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ...util import FQ, RLC


def sdiv_smod(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    pop1 = instruction.stack_pop()
    pop2 = instruction.stack_pop()
    push = instruction.stack_push()

    (a, b, c, d) = gen_witness(instruction, opcode, pop1, pop2, push)
    check_witness(instruction, a, b, c, d)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )


def check_witness(instruction: Instruction, a: RLC, b: RLC, c: RLC, d: RLC):
    a_is_zero = instruction.word_is_zero(a)
    b_is_zero = instruction.word_is_zero(b)
    c_is_zero = instruction.word_is_zero(c)

    a_is_neg = instruction.word_is_neg(a)
    b_is_neg = instruction.word_is_neg(b)
    c_is_neg = instruction.word_is_neg(c)
    d_is_neg = instruction.word_is_neg(d)

    a_abs = instruction.abs_word(a)
    b_abs = instruction.abs_word(b)
    c_abs = instruction.abs_word(c)
    d_abs = instruction.abs_word(d)

    # Constrain abs(remainder) < abs(divisor) when divisor != 0.
    lt, _ = instruction.compare_word(c_abs, b_abs)
    instruction.constrain_zero((1 - lt) * (1 - b_is_zero))

    # Constrain overflow == 0.
    overflow = instruction.mul_add_words(a_abs, b_abs, c_abs, d_abs)
    instruction.constrain_zero(overflow)

    # Constrain sign(dividend) == sign(remainder) when quotient, divisor and
    # remainder are all non-zero.
    condition = (1 - a_is_zero) * (1 - b_is_zero) * (1 - c_is_zero)
    instruction.constrain_equal(d_is_neg * condition, c_is_neg * condition)

    # The dividend is signed overflow when `-(1 << 255) // -1 = (1 << 255)`.
    d_is_signed_overflow = instruction.word_is_neg(d_abs)

    # Constrain sign(dividend) == sign(divisor) * sign(quotient) when both
    # quotient and divisor are non-zero and dividend is not signed overflow.
    condition = (1 - a_is_zero) * (1 - b_is_zero) * (1 - d_is_signed_overflow)
    instruction.constrain_equal(
        (1 - d_is_neg) * condition,
        ((a_is_neg * b_is_neg) + (1 - a_is_neg) * (1 - b_is_neg)) * condition,
    )


def gen_witness(instruction: Instruction, opcode: FQ, pop1: RLC, pop2: RLC, push: RLC):
    # The opcode value for SDIV and SMOD are 5 and 7. When the opcode is SDIV,
    # `Opcode.SMOD - opcode` is 2. To make `is_sdiv` be either 0 or 1, we need
    # to divide the product by 2, which is equivalent to multiply it by
    # inversion of 2.
    is_sdiv = (Opcode.SMOD - opcode) * FQ(2).inv()

    pop1_abs = instruction.abs_word(pop1)
    pop2_abs = instruction.abs_word(pop2)
    push_abs = instruction.abs_word(push)
    pop1_is_neg = instruction.word_is_neg(pop1)
    pop2_is_neg = instruction.word_is_neg(pop2)
    pop2_is_zero = instruction.word_is_zero(pop2)

    # Avoid word overflow for SMOD.
    sdiv_remainder_int = abs(pop1_abs.int_value - push_abs.int_value * pop2_abs.int_value)
    sdiv_remainder = RLC(sdiv_remainder_int) if sdiv_remainder_int < 1 << 256 else RLC(0)
    sdiv_remainder = instruction.select(
        pop1_is_neg, instruction.neg_word(sdiv_remainder), sdiv_remainder
    )
    smod_remainder = instruction.select(pop2_is_zero, pop1, push)

    # Avoid dividing by zero.
    pop2_abs = instruction.select(pop2_is_zero, RLC(1), pop2_abs)
    smod_quotient = instruction.select(
        pop2_is_zero, RLC(0), RLC(pop1_abs.int_value // pop2_abs.int_value)
    )
    smod_quotient = instruction.select(
        instruction.is_equal(pop1_is_neg, pop2_is_neg),
        smod_quotient,
        instruction.neg_word(smod_quotient),
    )

    return (
        instruction.select(is_sdiv, push, smod_quotient),  # quotient
        pop2,  # divisor
        instruction.select(is_sdiv, sdiv_remainder, smod_remainder),  # remainder
        pop1,  # dividend
    )
