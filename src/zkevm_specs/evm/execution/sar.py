from ...util import (
    FQ,
    MAX_U64,
    N_BYTES_U64,
    Word,
    int_is_neg,
    word_to_lo_hi,
)
from ..instruction import Instruction, Transition
from ..typing import Sequence


def sar(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    shift = instruction.stack_pop()
    a = instruction.stack_pop()
    b = instruction.stack_push()

    (
        a64s,
        b64s,
        a64s_lo,
        a64s_hi,
        shf_div64,
        shf_mod64,
        p_lo,
        p_hi,
        p_top,
    ) = gen_witness(instruction, shift, a)
    check_witness(
        instruction,
        shift,
        a,
        b,
        a64s,
        b64s,
        a64s_lo,
        a64s_hi,
        shf_div64,
        shf_mod64,
        p_lo,
        p_hi,
        p_top,
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )


def check_witness(
    instruction: Instruction,
    shift: Word,
    a: Word,
    b: Word,
    a64s: Sequence[FQ],
    b64s: Sequence[FQ],
    a64s_lo: Sequence[FQ],
    a64s_hi: Sequence[FQ],
    shf_div64: FQ,
    shf_mod64: FQ,
    p_lo: FQ,
    p_hi: FQ,
    p_top: FQ,
):
    a_le_bytes = a.to_le_bytes()
    b_le_bytes = b.to_le_bytes()
    is_neg, _ = instruction.compare(FQ(127), FQ(a_le_bytes[31]), 1)
    shf_lo, shf_hi = shift.to_lo_hi()
    shf_hi_is_zero = instruction.is_zero(shf_hi)

    for idx in range(4):
        offset = idx * N_BYTES_U64

        # a64s constraint
        instruction.constrain_equal(
            a64s[idx],
            instruction.bytes_to_fq(a_le_bytes[offset : offset + N_BYTES_U64]),
        )

        # b64s constraint
        instruction.constrain_equal(
            b64s[idx],
            instruction.bytes_to_fq(b_le_bytes[offset : offset + N_BYTES_U64]),
        )

        # Constrain `a64s[idx] == a64s_lo[idx] + a64s_hi[idx] * p_lo`.
        instruction.constrain_equal(a64s[idx], a64s_lo[idx] + a64s_hi[idx] * p_lo)

        # Constrain `a64s_lo[idx] < p_lo`.
        a64s_lo_lt_p_lo, _ = instruction.compare(a64s_lo[idx], p_lo, 16)
        instruction.constrain_equal(a64s_lo_lt_p_lo, FQ(1))

        # Constrain `a64s_hi[idx] < p_hi`.
        a64s_hi_lt_p_hi, _ = instruction.compare(a64s_hi[idx], p_hi, 16)
        instruction.constrain_equal(a64s_hi_lt_p_hi, FQ(1))

    # Merge contraints
    shf_div64_eq0 = shf_hi_is_zero * instruction.is_zero(shf_div64)
    shf_div64_eq1 = shf_hi_is_zero * instruction.is_zero(shf_div64 - 1)
    shf_div64_eq2 = shf_hi_is_zero * instruction.is_zero(shf_div64 - 2)
    shf_div64_eq3 = shf_hi_is_zero * instruction.is_zero(shf_div64 - 3)
    instruction.constrain_equal(
        b64s[0],
        (a64s_hi[0] + a64s_lo[1] * p_hi) * shf_div64_eq0
        + (a64s_hi[1] + a64s_lo[2] * p_hi) * shf_div64_eq1
        + (a64s_hi[2] + a64s_lo[3] * p_hi) * shf_div64_eq2
        + (a64s_hi[3] + p_top) * shf_div64_eq3
        + is_neg * MAX_U64 * (1 - shf_div64_eq0 - shf_div64_eq1 - shf_div64_eq2 - shf_div64_eq3),
    )
    instruction.constrain_equal(
        b64s[1],
        (a64s_hi[1] + a64s_lo[2] * p_hi) * shf_div64_eq0
        + (a64s_hi[2] + a64s_lo[3] * p_hi) * shf_div64_eq1
        + (a64s_hi[3] + p_top) * shf_div64_eq2
        + is_neg * MAX_U64 * (1 - shf_div64_eq0 - shf_div64_eq1 - shf_div64_eq2),
    )
    instruction.constrain_equal(
        b64s[2],
        (a64s_hi[2] + a64s_lo[3] * p_hi) * shf_div64_eq0
        + (a64s_hi[3] + p_top) * shf_div64_eq1
        + is_neg * MAX_U64 * (1 - shf_div64_eq0 - shf_div64_eq1),
    )
    instruction.constrain_equal(
        b64s[3],
        (a64s_hi[3] + p_top) * shf_div64_eq0 + is_neg * MAX_U64 * (1 - shf_div64_eq0),
    )

    # Shift constraint
    shf_mod64_lt_64, _ = instruction.compare(shf_mod64, FQ(64), 1)
    instruction.constrain_equal(shf_mod64_lt_64, FQ(1))
    instruction.constrain_equal(shf_lo, shf_mod64 + shf_div64 * 64)

    # `is_neg` constraints
    instruction.constrain_bool(is_neg)
    instruction.sign_byte_lookup(
        instruction.bytes_to_fq(a_le_bytes[31:]),
        instruction.select(is_neg, FQ(255), FQ(0)),
    )

    # `p_top` constraint
    instruction.constrain_equal(p_top, is_neg * (MAX_U64 + 1 - p_hi))

    # `p_lo == pow(2, shf_mod64)` and `p_hi == pow(2, 64 - shf_mod64)`.
    instruction.pow2_lookup(shf_mod64, p_lo, FQ(0))
    instruction.pow2_lookup(64 - shf_mod64, p_hi, FQ(0))


def gen_witness(instruction: Instruction, shift: Word, a: Word):
    is_neg = int_is_neg(a.int_value())
    shf_lo, shf_hi = shift.to_lo_hi()
    shf_div64 = shf_lo.n // 64
    shf_mod64 = shf_lo.n % 64
    p_lo = 1 << shf_mod64
    p_hi = 1 << (64 - shf_mod64)

    # The new bits should be set to 1 if negative.
    p_top = is_neg * (MAX_U64 + 1 - p_hi)

    # Each of the four `a64s` limbs is split into two parts `a64s_lo` and
    # `a64s_hi` at position `shf_mod64`. `a64s_lo` is the lower `shf_mod64`
    # bits, and `a64s_hi` is the higher `64 - shf_mod64` bits,
    a64s = a.to_64s()
    a64s_lo = [FQ(0)] * 4
    a64s_hi = [FQ(0)] * 4
    for idx in range(4):
        a64s_lo[idx] = FQ(a64s[idx].n % p_lo)
        a64s_hi[idx] = FQ(a64s[idx].n // p_lo)

    b64s = [FQ(MAX_U64 if is_neg else 0)] * 4
    if shf_hi == 0 and shf_div64 < 4:
        b64s[3 - shf_div64] = a64s_hi[3] + p_top
        for k in range(3 - shf_div64):
            b64s[k] = a64s_hi[k + shf_div64] + a64s_lo[k + shf_div64 + 1] * p_hi

    return (
        a64s,
        b64s,
        a64s_lo,
        a64s_hi,
        FQ(shf_div64),
        FQ(shf_mod64),
        FQ(p_lo),
        FQ(p_hi),
        FQ(p_top),
    )
