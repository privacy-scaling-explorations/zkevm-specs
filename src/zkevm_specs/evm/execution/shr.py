from ...util import FQ, N_BYTES_U64, RLC
from ..instruction import Instruction, Transition
from ..typing import Sequence


def shr(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    a = instruction.stack_pop()
    shift = instruction.stack_pop()
    b = instruction.stack_push()

    (
        a64s,
        b64s,
        a64s_lo,
        a64s_hi,
        shf_div64,
        shf_mod64,
        shf_lt256,
        p_lo,
        p_hi,
    ) = gen_witness(instruction, a, shift)
    check_witness(
        instruction,
        a,
        shift,
        b,
        a64s,
        b64s,
        a64s_lo,
        a64s_hi,
        shf_div64,
        shf_mod64,
        shf_lt256,
        p_lo,
        p_hi,
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )


def check_witness(
    instruction: Instruction,
    a: RLC,
    shift: RLC,
    b: RLC,
    a64s: Sequence[FQ],
    b64s: Sequence[FQ],
    a64s_lo: Sequence[FQ],
    a64s_hi: Sequence[FQ],
    shf_div64,
    shf_mod64,
    shf_lt256,
    p_lo,
    p_hi,
):
    for idx in range(4):
        offset = idx * N_BYTES_U64

        # a64s constraint
        instruction.constrain_equal(
            a64s[idx],
            instruction.bytes_to_fq(a.le_bytes[offset : offset + N_BYTES_U64]),
        )

        # b64s constraint
        instruction.constrain_equal(
            b64s[idx],
            instruction.bytes_to_fq(b.le_bytes[offset : offset + N_BYTES_U64]),
        )

        # `a64s[idx] == a64s_lo[idx] + a64s_hi[idx] * p_lo`
        instruction.constrain_equal(a64s[idx], a64s_lo[idx] + a64s_hi[idx] * p_lo)

        # `a64s_lo[idx] < p_lo`
        a64s_lo_lt_p_lo, _ = instruction.compare(a64s_lo[idx], p_lo, N_BYTES_U64)
        instruction.constrain_equal(a64s_lo_lt_p_lo, FQ(1))

    # merge contraints
    shf_div64_eq0 = instruction.is_zero(shf_div64)
    shf_div64_eq1 = instruction.is_zero(shf_div64 - 1)
    shf_div64_eq2 = instruction.is_zero(shf_div64 - 2)
    instruction.constrain_equal(
        b64s[0],
        (a64s_hi[0] + a64s_lo[1] * p_hi) * shf_div64_eq0
        + (a64s_hi[1] + a64s_lo[2] * p_hi) * shf_div64_eq1
        + (a64s_hi[2] + a64s_lo[3] * p_hi) * shf_div64_eq2
        + a64s_hi[3] * (1 - shf_div64_eq0 - shf_div64_eq1 - shf_div64_eq2),
    )
    instruction.constrain_equal(
        b64s[1],
        (a64s_hi[1] + a64s_lo[2] * p_hi) * shf_div64_eq0
        + (a64s_hi[2] + a64s_lo[3] * p_hi) * shf_div64_eq1
        + a64s_hi[3] * shf_div64_eq2,
    )
    instruction.constrain_equal(
        b64s[2], (a64s_hi[2] + a64s_lo[3] * p_hi) * shf_div64_eq0 + a64s_hi[3] * shf_div64_eq1
    )
    instruction.constrain_equal(b64s[3], a64s_hi[3] * shf_div64_eq0)

    # shift[0] constraint
    shf0 = instruction.bytes_to_fq(shift.le_bytes[:1])
    instruction.constrain_equal(
        shf0,
        shf_mod64 + shf_div64 * 64,
    )

    # shf_div64 in [0, 4), shf_mod64 in [0, 64) and shf_div64 in [0, 1).
    assert instruction.select(shf_lt256, shf_div64, FQ(0)).n in range(4)
    assert shf_mod64 in range(64)
    instruction.constrain_bool(shf_lt256)

    # `p_lo == pow(2, shf_mod64)` and `p_hi == pow(2, 64 - shf_mod64)`.
    instruction.pow65_lookup(shf_mod64, p_lo)
    instruction.pow65_lookup(64 - shf_mod64, p_hi)


def gen_witness(instruction: Instruction, a: RLC, shift: RLC):
    shf_div64 = FQ(shift.int_value // 64)
    shf_mod64 = FQ(shift.int_value % 64)
    shf_lt256 = instruction.is_zero(instruction.bytes_to_fq(shift.le_bytes[1:]))
    p_lo = FQ(1 << shf_mod64.n)
    p_hi = FQ(1 << (64 - shf_mod64.n))

    a64s = instruction.word_to_64s(a)
    a64s_lo = [FQ(0)] * 4
    a64s_hi = [FQ(0)] * 4
    for idx in range(4):
        a64s_lo[idx] = FQ(a64s[idx].n % p_lo.n)
        a64s_hi[idx] = FQ(a64s[idx].n // p_lo.n)

    b64s = [FQ(0)] * 4
    b64s[3 - shf_div64.n] = a64s_hi[3]
    for k in range(0, 3 - shf_div64.n):
        b64s[k] = FQ(a64s_hi[k + shf_div64.n] + a64s_lo[k + shf_div64.n + 1] * p_hi.n)

    return (
        a64s,
        b64s,
        a64s_lo,
        a64s_hi,
        shf_div64,
        shf_mod64,
        shf_lt256,
        p_lo,
        p_hi,
    )
