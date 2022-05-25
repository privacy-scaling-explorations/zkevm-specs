from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ...util import FQ, RLC


def sdiv_smod(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    # The opcode value for SDIV and SMOD are 5 and 7. When the opcode is SDIV,
    # `Opcode.MOD - opcode` is 2. To make `is_sdiv` be either 0 or 1, we need to
    # divide the product by 2, which is equivalent to multiply it by inversion
    # of 2.
    is_div = (Opcode.MOD - opcode) * FQ(2).inv()

    pop1 = instruction.bytes_to_fq(instruction.stack_pop().le_bytes)
    pop2 = instruction.bytes_to_fq(instruction.stack_pop().le_bytes)
    push = instruction.bytes_to_fq(instruction.stack_push().le_bytes)
    pop1_abs = get_abs(instruction, pop1)
    pop2_abs = get_abs(instruction, pop2)
    push_abs = get_abs(instruction, push)
    pop1_is_non_neg = is_non_neg(pop1)
    pop2_is_non_neg = is_non_neg(pop2)

    if is_div == 1:
        # quotient
        a = push
        # divisor
        b = pop2
        # residue
        c = pop1_abs - push_abs * pop2_abs
        c = instruction.select(pop1_is_non_neg, c, get_neg(instruction, c))
        # dividend
        d = pop1
    else:  # SMOD
        # quotient
        # gupeng
        a = FQ(pop1_abs.n // pop2_abs.n)
        a = instruction.select(
            instruction.is_zero(pop2),
            pop2,
            instruction.select(
                instruction.is_equal(pop1_is_non_neg, pop2_is_non_neg), a, get_neg(instruction, a)
            ),
        )
        # divisor
        b = pop2
        # residue
        c = instruction.select(instruction.is_zero(pop2), pop1, push)
        # dividend
        d = pop1

    a_abs = instruction.rlc_encode(get_abs(instruction, a), 32)
    b_abs = instruction.rlc_encode(get_abs(instruction, b), 32)
    c_abs = instruction.rlc_encode(get_abs(instruction, c), 32)
    d_abs = instruction.rlc_encode(get_abs(instruction, d), 32)

    divisor_is_zero = instruction.word_is_zero(b_abs)
    quotient_is_zero = instruction.word_is_zero(a_abs)
    residue_is_zero = instruction.word_is_zero(c_abs)
    overflow = instruction.mul_add_words(a_abs, b_abs, c_abs, d_abs)
    lt, _ = instruction.compare_word(c_abs, b_abs)

    # Constrain abs(residue) < abs(divisor) when divisor != 0.
    instruction.constrain_zero((1 - lt) * (1 - divisor_is_zero))

    # Constrain overflow == 0.
    instruction.constrain_zero(overflow)

    a_is_non_neg = is_non_neg(a)
    b_is_non_neg = is_non_neg(b)
    c_is_non_neg = is_non_neg(c)
    d_is_non_neg = is_non_neg(d)
    # Constrain sign(residue) == sign(divisor) when quotient, divisor and resisue are all non-zero.
    condition = (1 - quotient_is_zero) * (1 - divisor_is_zero) * (1 - residue_is_zero)
    instruction.constrain_equal(b_is_non_neg * condition, c_is_non_neg * condition)
    # Constrain sign(dividend) == sign(divisor) * sign(quotient) when both quotient and divisor are non-zero.
    condition = (1 - quotient_is_zero) * (1 - divisor_is_zero)
    instruction.constrain_equal(
        d_is_non_neg * condition,
        ((a_is_non_neg * b_is_non_neg) + (1 - a_is_non_neg) * (1 - b_is_non_neg)) * condition,
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )


def get_abs(instruction: Instruction, val: FQ) -> FQ:
    return instruction.select(is_non_neg(val), val, get_neg(instruction, val))


def get_neg(instruction: Instruction, val: FQ) -> FQ:
    return instruction.select(instruction.is_zero(val), val, FQ((1 << 256) - 1) - val + 1)


def is_non_neg(val: FQ) -> FQ:
    return FQ(val.n < 1 << 31)
