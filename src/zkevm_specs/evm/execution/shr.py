from ...encoding import (
    # Conflict with imports in `__init__.py`
    U256 as EncodingU256,
    U64 as EncodingU64,
    U8,
    u256_to_u64s,
    u64s_to_u256,
    u8s_to_u64s,
)
from ...util import FQ, RLC
from ..instruction import Instruction, Transition
from ..typing import Sequence


def shr(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    a = instruction.stack_pop()
    shift = instruction.stack_pop()

    (
        a64s,
        b64s,
        a_slice_hi_digits,
        a_slice_lo_digits,
        a_slice_hi,
        a_slice_lo,
        shift_div_by_64,
        shift_mod_by_64,
        shift_mod_by_64_decpow,
        shift_mod_by_64_div_by_8,
        shift_mod_by_64_pow,
        shift_mod_by_8,
        shift_overflow,
    ) = gen_witness(instruction, a, shift)
    check_witness(
        instruction,
        a64s,
        b64s,
        a_slice_hi_digits,
        a_slice_lo_digits,
        a_slice_hi,
        a_slice_lo,
        shift,
        shift_div_by_64,
        shift_mod_by_64,
        shift_mod_by_64_decpow,
        shift_mod_by_64_div_by_8,
        shift_mod_by_64_pow,
        shift_mod_by_8,
        shift_overflow,
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )


def check_witness(
    instruction: Instruction,
    a64s: Sequence[EncodingU64],
    b64s: Sequence[EncodingU64],
    a_slice_hi_digits: Sequence[EncodingU64],
    a_slice_lo_digits: Sequence[EncodingU64],
    a_slice_hi: Sequence[U8],
    a_slice_lo: Sequence[U8],
    shift: RLC,
    shift_div_by_64,
    shift_mod_by_64,
    shift_mod_by_64_decpow,
    shift_mod_by_64_div_by_8,
    shift_mod_by_64_pow,
    shift_mod_by_8,
    shift_overflow,
):
    # SHR main constraints
    instruction.constrain_equal(FQ(u64s_to_u256(b64s)), FQ(instruction.stack_push().int_value))

    # shift[0]_split_constraints
    # if shift_overflow == 0:
    #   x = shift_div_by_64
    #   y = shift_mod_by_64_div_by_8
    #   z = shift_mod_by_8
    #   shift[0] == x * 64 + y * 8 + z
    shift_0 = instruction.bytes_to_fq(shift.le_bytes[:1])
    instruction.constrain_equal(
        shift_0,
        instruction.select(
            shift_overflow,
            shift_0,
            shift_div_by_64 * 64 + shift_mod_by_64_div_by_8 * 8 + shift_mod_by_8,
        ),
    )

    # shr_constraints
    for transplacement in range(4):
        select_transplacement_polynomial = instruction.is_zero(shift_div_by_64 - FQ(transplacement))
        for idx in range(4 - transplacement):
            tmp_hi_idx = FQ(idx + transplacement)
            is_max_idx = instruction.is_equal(tmp_hi_idx, FQ(3))
            tmp_lo_idx = instruction.select(is_max_idx, FQ(0), tmp_hi_idx + 1)
            merge_a = a_slice_hi_digits[tmp_hi_idx.n] + instruction.select(
                is_max_idx, FQ(0), a_slice_lo_digits[tmp_lo_idx.n] * shift_mod_by_64_decpow
            )
            instruction.constrain_zero(FQ((merge_a - b64s[idx]) * select_transplacement_polynomial))
        for idx in range(4 - transplacement, 4):
            instruction.constrain_zero(FQ(select_transplacement_polynomial * b64s[idx]))

    # merge_constraints
    for idx in range(4):
        instruction.constrain_equal(
            FQ(a_slice_lo_digits[idx] + a_slice_hi_digits[idx] * shift_mod_by_64_pow),
            FQ(a64s[idx]),
        )

    # slice_higher_cell_equal_to_zero_constraints
    for digit_transplacement in range(8):
        select_transplacement_polynomial = instruction.is_zero(
            shift_mod_by_64_div_by_8 - digit_transplacement
        )
        for virtual_idx in range(4):
            for idx in range(digit_transplacement + 1, 8):
                now_idx = virtual_idx * 8 + idx
                instruction.constrain_zero(
                    FQ(select_transplacement_polynomial * a_slice_lo[now_idx])
                )
            for idx in range(8 - digit_transplacement, 8):
                now_idx = virtual_idx * 8 + idx
                instruction.constrain_zero(
                    FQ(select_transplacement_polynomial * a_slice_hi[now_idx])
                )

    # slice_bits_lookups
    for virtual_idx in range(4):
        slice_bits_polynomial = [0] * 2
        for digit_transplacement in range(8):
            select_transplacement_polynomial = instruction.is_zero(
                shift_mod_by_64_div_by_8 - digit_transplacement
            )
            now_idx = virtual_idx * 8 + digit_transplacement
            slice_bits_polynomial[0] += select_transplacement_polynomial.n * a_slice_lo[now_idx]
            now_idx = virtual_idx * 8 + 7 - digit_transplacement
            slice_bits_polynomial[1] += select_transplacement_polynomial.n * a_slice_hi[now_idx]

        instruction.bitslevel_lookup(shift_mod_by_8, FQ(slice_bits_polynomial[0]))
        instruction.bitslevel_lookup(8 - shift_mod_by_8, FQ(slice_bits_polynomial[1]))

    # pow_lookups
    instruction.pow64_lookup(shift_mod_by_64, shift_mod_by_64_pow, shift_mod_by_64_decpow)

    # given_value_lookups
    instruction.bitslevel_lookup(FQ(2), instruction.select(shift_overflow, FQ(0), shift_div_by_64))
    instruction.bitslevel_lookup(
        FQ(3), instruction.select(shift_overflow, FQ(0), shift_mod_by_64_div_by_8)
    )
    instruction.bitslevel_lookup(FQ(3), instruction.select(shift_overflow, FQ(0), shift_mod_by_8))


def gen_witness(instruction: Instruction, a: RLC, shift: RLC):
    shift_div_by_64 = FQ(shift.int_value // 64)
    shift_mod_by_64 = FQ(shift.int_value % 64)
    shift_mod_by_64_div_by_8 = FQ(shift.int_value % 64 // 8)
    shift_mod_by_64_pow = FQ(1 << shift_mod_by_64.n)
    shift_mod_by_64_decpow = FQ((1 << 64) // shift_mod_by_64_pow.n)
    shift_mod_by_8 = FQ(shift.int_value % 8)
    shift_overflow = FQ(1 - instruction.is_zero(instruction.sum(shift.le_bytes[1:])))

    a64s = u256_to_u64s(EncodingU256(a.int_value))
    slice_hi = 0
    slice_lo = 0
    a_slice_hi = [U8(0)] * 32
    a_slice_lo = [U8(0)] * 32
    is_shift_mod_by_64_zero = instruction.is_zero(FQ(shift_mod_by_64))
    for virtual_idx in range(0, 4):
        slice_hi = a64s[virtual_idx] // shift_mod_by_64_pow.n
        slice_lo = a64s[virtual_idx] % shift_mod_by_64_pow.n

        for idx in range(0, 8):
            now_idx = (virtual_idx << 3) + idx
            a_slice_hi[now_idx] = U8(slice_hi % (1 << 8))
            a_slice_lo[now_idx] = U8(slice_lo % (1 << 8))
            slice_hi = slice_hi >> 8
            slice_lo = slice_lo >> 8

    a_slice_hi_digits = u8s_to_u64s(a_slice_hi)
    a_slice_lo_digits = u8s_to_u64s(a_slice_lo)

    b64s = [EncodingU64(0)] * 4
    b64s[3 - shift_div_by_64.n] = a_slice_hi_digits[3]
    for i in range(0, 3 - shift_div_by_64.n):
        b64s[i] = EncodingU64(
            a_slice_hi_digits[i + shift_div_by_64.n]
            + a_slice_lo_digits[i + shift_div_by_64.n + 1] * shift_mod_by_64_decpow.n
        )

    return (
        a64s,
        b64s,
        a_slice_hi_digits,
        a_slice_lo_digits,
        a_slice_hi,
        a_slice_lo,
        shift_div_by_64,
        shift_mod_by_64,
        shift_mod_by_64_decpow,
        shift_mod_by_64_div_by_8,
        shift_mod_by_64_pow,
        shift_mod_by_8,
        shift_overflow,
    )
