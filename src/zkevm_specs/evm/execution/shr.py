from ...encoding import (
    # Conflict with imports in `__init__.py`
    U256 as EncodingU256,
    U64 as EncodingU64,
    U8,
    u256_to_u64s,
    u64s_to_u256,
    u8s_to_u64s,
)
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
    p_lo,
    p_hi,
):
    # a64s and b64s constraints
    for idx in range(4):
        offset = idx << 3  # idx * 8
        instruction.constrain_equal(
            a64s[idx],
            FQ(int.from_bytes(a.le_bytes[offset : offset + 8], "little")),
        )
        instruction.constrain_equal(
            b64s[idx],
            FQ(int.from_bytes(b.le_bytes[offset : offset + 8], "little")),
        )


def gen_witness(instruction: Instruction, a: RLC, shift: RLC):
    shf_div64 = FQ(shift.int_value // 64)
    shf_mod64 = FQ(shift.int_value % 64)
    p_lo = FQ(1 << shf_mod64.n)
    p_hi = FQ(1 << (64 - shf_mod64.n))

    a64s = [FQ(0)] * 4
    a64s_lo = [FQ(0)] * 4
    a64s_hi = [FQ(0)] * 4
    for idx in range(4):
        idx_offset = idx << 3  # idx * 8
        for i in range(8):
            a64s[idx] = FQ(a64s[idx] + a.le_bytes[idx_offset + i] * (1 << 8 * i))  # * pow(256, i)

        a64s_lo[idx] = FQ(a64s[idx].n % p_lo.n)
        a64s_hi[idx] = FQ(a64s[idx].n // p_lo.n)

    b64s = [FQ(0)] * 4
    b64s[3 - shf_div64.n] = a64s_hi[3]
    for k in range(0, 3 - shf_div64.n):
        b64s[k] = FQ(a64s_hi[k + shf_div64.n] + a64s_lo[k + shf_div64.n + 1] * p_hi.n)

    print("shift = ", shift)
    print("shf_div64 = ", shf_div64)
    print("shf_mod64 = ", shf_mod64)
    print("p_lo = ", p_lo)
    print("p_hi = ", p_hi)
    print("shift = ", shift)
    print("a64s = ", a64s)
    print("b64s = ", b64s)

    return (
        a64s,
        b64s,
        a64s_lo,
        a64s_hi,
        shf_div64,
        shf_mod64,
        p_lo,
        p_hi,
    )
