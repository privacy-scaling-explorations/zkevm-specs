from ...encoding import u256_to_u64s, u64s_to_u256, u8s_to_u64s, U256, U64, U8
from ...util import FQ, RLC
from ..instruction import Instruction, Transition
from ..opcode import Opcode


def shr(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    a = instruction.stack_pop()
    shift = instruction.stack_pop()

    # If shift is greater than 255, returns 0.
    shift_lo, shift_hi = shift.le_bytes[:1], shift.le_bytes[1:]
    shift_valid = instruction.is_zero(instruction.sum(shift_hi))

    result = instruction.select(
        shift_valid,
        word_shift_right(instruction, a, instruction.bytes_to_fq(shift_lo)),
        RLC(0),
    )
    instruction.constrain_equal(result, instruction.stack_push())

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )


def word_shift_right(instruction: Instruction, a: RLC, shift: FQ) -> RLC:
    shift_div_by_64 = shift.n // 64
    shift_mod_by_64 = shift.n % 64
    shift_mod_by_64_pow = 1 << shift_mod_by_64
    shift_mod_by_64_decpow = (1 << 64) // shift_mod_by_64_pow

    a64s = u256_to_u64s(U256(a.int_value))
    slice_hi = 0
    slice_lo = 0
    a_slice_hi = [U8(0)] * 32
    a_slice_lo = [U8(0)] * 32
    for virtual_idx in range(0, 4):
        if shift_mod_by_64 == 0:
            slice_hi = 0
            slice_lo = a64s[virtual_idx]
        else:
            slice_hi = a64s[virtual_idx] // (1 << shift_mod_by_64)
            slice_lo = a64s[virtual_idx] % (1 << shift_mod_by_64)

        for idx in range(0, 8):
            now_idx = (virtual_idx << 3) + idx
            a_slice_lo[now_idx] = U8(slice_lo % (1 << 8))
            a_slice_hi[now_idx] = U8(slice_hi % (1 << 8))
            slice_lo = slice_lo >> 8
            slice_hi = slice_hi >> 8

    a_slice_hi_digits = u8s_to_u64s(a_slice_hi)
    a_slice_lo_digits = u8s_to_u64s(a_slice_lo)

    b_digits = [U64(0)] * 4
    b_digits[3 - shift_div_by_64] = a_slice_hi_digits[3]
    for i in range(0, 3 - shift_div_by_64):
        b_digits[i] = U64(
            a_slice_hi_digits[i + shift_div_by_64]
            + a_slice_lo_digits[i + shift_div_by_64 + 1] * shift_mod_by_64_decpow
        )

    return RLC(u64s_to_u256(b_digits))
