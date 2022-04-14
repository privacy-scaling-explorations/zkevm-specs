from ...encoding import (
    LookupTable,
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
from ..opcode import Opcode
from ..typing import Sequence


def shr(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    a = instruction.stack_pop()
    shift = instruction.stack_pop()

    # If shift is greater than 255, returns 0.
    shift_lo, shift_hi = shift.le_bytes[:1], shift.le_bytes[1:]
    shift_valid = instruction.is_zero(instruction.sum(shift_hi))

    result = instruction.select(
        shift_valid,
        instruction.select(
            instruction.is_zero(instruction.sum(shift_lo)),
            a,
            word_shift_right(instruction, shift_valid, a, instruction.bytes_to_fq(shift_lo)),
        ),
        RLC(0),
    )
    instruction.constrain_equal(result, instruction.stack_push())

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )


def word_shift_right(instruction: Instruction, shift_valid: FQ, a: RLC, shift: FQ) -> RLC:
    if shift_valid == 0 or shift == 0:
        return RLC(0)
    shift_div_by_64 = shift.n // 64
    shift_mod_by_64 = shift.n % 64
    shift_mod_by_64_div_by_8 = shift.n % 64 // 8
    shift_mod_by_64_pow = 1 << shift_mod_by_64
    shift_mod_by_64_decpow = (1 << 64) // shift_mod_by_64_pow
    shift_mod_by_8 = shift.n % 8

    a_digits = u256_to_u64s(EncodingU256(a.int_value))
    slice_hi = 0
    slice_lo = 0
    a_slice_hi = [U8(0)] * 32
    a_slice_lo = [U8(0)] * 32
    for virtual_idx in range(0, 4):
        if shift_mod_by_64 == 0:
            slice_hi = 0
            slice_lo = a_digits[virtual_idx]
        else:
            slice_hi = a_digits[virtual_idx] // (1 << shift_mod_by_64)
            slice_lo = a_digits[virtual_idx] % (1 << shift_mod_by_64)

        for idx in range(0, 8):
            now_idx = (virtual_idx << 3) + idx
            a_slice_lo[now_idx] = U8(slice_lo % (1 << 8))
            a_slice_hi[now_idx] = U8(slice_hi % (1 << 8))
            slice_lo = slice_lo >> 8
            slice_hi = slice_hi >> 8

    a_slice_hi_digits = u8s_to_u64s(a_slice_hi)
    a_slice_lo_digits = u8s_to_u64s(a_slice_lo)

    b_digits = [EncodingU64(0)] * 4
    b_digits[3 - shift_div_by_64] = a_slice_hi_digits[3]
    for i in range(0, 3 - shift_div_by_64):
        b_digits[i] = EncodingU64(
            a_slice_hi_digits[i + shift_div_by_64]
            + a_slice_lo_digits[i + shift_div_by_64 + 1] * shift_mod_by_64_decpow
        )

    check_internal_constraints(
        instruction,
        shift,
        a_digits,
        b_digits,
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
    )

    return RLC(u64s_to_u256(b_digits))


def check_internal_constraints(
    instruction: Instruction,
    shift: FQ,
    a_digits: Sequence[EncodingU64],
    b_digits: Sequence[EncodingU64],
    a_slice_hi_digits: Sequence[EncodingU64],
    a_slice_lo_digits: Sequence[EncodingU64],
    a_slice_hi: Sequence[U8],
    a_slice_lo: Sequence[U8],
    shift_div_by_64,
    shift_mod_by_64,
    shift_mod_by_64_decpow,
    shift_mod_by_64_div_by_8,
    shift_mod_by_64_pow,
    shift_mod_by_8,
):
    # shift_split_constraints
    instruction.constrain_equal(
        shift, FQ(shift_div_by_64 * 64 + shift_mod_by_64_div_by_8 * 8 + shift_mod_by_8)
    )

    # shr_constraints
    for transplacement in range(4):
        if shift_div_by_64 == transplacement:
            select_transplacement_polynomial = 1
        else:
            select_transplacement_polynomial = 0
        for idx in range(4 - transplacement):
            tmp_idx = idx + transplacement
            if tmp_idx == 3:
                merge_a = a_slice_hi_digits[tmp_idx]
            else:
                merge_a = (
                    a_slice_hi_digits[tmp_idx]
                    + a_slice_lo_digits[tmp_idx + 1] * shift_mod_by_64_decpow
                )
            instruction.constrain_zero(
                FQ((merge_a - b_digits[idx]) * select_transplacement_polynomial)
            )
        for idx in range(4 - transplacement, 4):
            instruction.constrain_zero(FQ(select_transplacement_polynomial * b_digits[idx]))

    # merge_constraints
    for idx in range(4):
        instruction.constrain_equal(
            FQ(a_slice_lo_digits[idx] + a_slice_hi_digits[idx] * shift_mod_by_64_pow),
            FQ(a_digits[idx]),
        )

    # slice_higher_cell_equal_to_zero_constraints
    for digit_transplacement in range(8):
        if shift_mod_by_64_div_by_8 == digit_transplacement:
            select_transplacement_polynomial = 1
        else:
            select_transplacement_polynomial = 0
        for virtual_idx in range(4):
            for idx in range(digit_transplacement + 1, 8):
                now_idx = virtual_idx * 8 + idx
                instruction.constrain_zero(
                    FQ(select_transplacement_polynomial * a_slice_hi[now_idx])
                )
            for idx in range(8 - digit_transplacement, 8):
                now_idx = virtual_idx * 8 + idx
                instruction.constrain_zero(
                    FQ(select_transplacement_polynomial * a_slice_lo[now_idx])
                )

    # slice_bits_lookups
    for virtual_idx in range(4):
        slice_bits_polynomial = [0] * 2
        for digit_transplacement in range(8):
            if shift_mod_by_64_div_by_8 == digit_transplacement:
                select_transplacement_polynomial = 1
            else:
                select_transplacement_polynomial = 0
            now_idx = virtual_idx * 8 + digit_transplacement
            slice_bits_polynomial[0] += select_transplacement_polynomial * a_slice_lo[now_idx]
            now_idx = virtual_idx * 8 + 7 - digit_transplacement
            slice_bits_polynomial[1] += select_transplacement_polynomial * a_slice_hi[now_idx]

        instruction.bitslevel_lookup(shift_mod_by_8, FQ(slice_bits_polynomial[0]))
        instruction.bitslevel_lookup(8 - shift_mod_by_8, FQ(slice_bits_polynomial[1]))

    # pow_lookups
    instruction.pow64_lookup(shift_mod_by_64, shift_mod_by_64_pow, shift_mod_by_64_decpow)

    # given_value_lookups
    instruction.bitslevel_lookup(FQ(2), shift_div_by_64)
    instruction.bitslevel_lookup(FQ(3), shift_mod_by_64_div_by_8)
    instruction.bitslevel_lookup(FQ(3), shift_mod_by_8)
