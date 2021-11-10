from src.zkevm_specs.encoding import U8, u8s_to_u64s, is_circuit_code
from typing import Sequence


@is_circuit_code
def check_shr(a: Sequence[U8],
              b: Sequence[U8],
              shift: U8,
              a_slice_front: Sequence[U8],
              a_slice_back: Sequence[U8],
              shift_div_by_64,
              shift_mod_by_64_div_by_8,
              shift_mod_by_64_decpow,
              shift_mod_by_64_pow,
              shift_mod_by_8
              ):
    assert len(a) == len(b) == 32
    assert len(a_slice_back) == len(a_slice_front) == 32
    assert 0 <= shift_div_by_64 < 2 ** 2
    assert 0 <= shift_mod_by_64_div_by_8 < 2 ** 3
    assert 0 <= shift_mod_by_8 < 2 ** 3

    a_digits = u8s_to_u64s(a)
    b_digits = u8s_to_u64s(b)
    a_slice_back_digits = u8s_to_u64s(a_slice_back)
    a_slice_front_digits = u8s_to_u64s(a_slice_front)

    # shift_split_constraints
    shift_mod_by_64 = shift_mod_by_64_div_by_8 * 8 + shift_mod_by_8
    assert shift == shift_div_by_64 * 64 + shift_mod_by_64

    # shr_constraints
    for transplacement in range(4):
        if shift_div_by_64 == transplacement:
            select_transplacement_polynomial = 1
        else:
            select_transplacement_polynomial = 0
        for idx in range(4 - transplacement):
            tmp_idx = idx + transplacement
            if tmp_idx == 3:
                merge_a = a_slice_front_digits[tmp_idx]
            else:
                merge_a = a_slice_front_digits[tmp_idx] + a_slice_back_digits[tmp_idx + 1] * shift_mod_by_64_decpow
            assert (merge_a - b_digits[idx]) * select_transplacement_polynomial == 0
        for idx in range(4 - transplacement, 4):
            assert select_transplacement_polynomial * b_digits[idx] == 0

    # merge_constraints
    # check a_slice_back_digits[i] + a_slice_front_digits * shift_mod_by_64_pow == a_digits[i]
    for idx in range(4):
        assert a_slice_back_digits[idx] + a_slice_front_digits[idx] * shift_mod_by_64_pow == a_digits[idx]

    # check 2^shift_mod_by_64 == shift_mod_by_64_pow
    # check shift_mod_by_64_pow * shift_mod_by_64_decpow == 2^64
    assert 2 ** shift_mod_by_64 == shift_mod_by_64_pow
    assert shift_mod_by_64_pow * shift_mod_by_64_decpow == 2 ** 64

    # check several higher cells for slice_back and slice_front
    for digit_transplacement in range(8):
        if shift_mod_by_64_div_by_8 == digit_transplacement:
            select_transplacement_polynomial = 1
        else:
            select_transplacement_polynomial = 0
        for virtual_idx in range(4):
            for idx in range(digit_transplacement + 1, 8):
                now_idx = virtual_idx * 8 + idx
                assert select_transplacement_polynomial * a_slice_back[now_idx] == 0
            for idx in range(8 - digit_transplacement, 8):
                now_idx = virtual_idx * 8 + idx
                assert select_transplacement_polynomial * a_slice_front[now_idx] == 0

    # check the specific 4 cells for shift_mod_by_8 bits and 4 cells for (8 - shift_mod_by_8) bits.
    for virtual_idx in range(4):
        slice_bits_polynomial = [0] * 2
        for digit_transplacement in range(8):
            if shift_mod_by_64_div_by_8 == digit_transplacement:
                select_transplacement_polynomial = 1
            else:
                select_transplacement_polynomial = 0
            now_idx = virtual_idx * 8 + digit_transplacement
            slice_bits_polynomial[0] += select_transplacement_polynomial * a_slice_back[now_idx]
            now_idx = virtual_idx * 8 + 7 - digit_transplacement
            slice_bits_polynomial[1] += select_transplacement_polynomial * a_slice_front[now_idx]
        assert slice_bits_polynomial[0] < 2 ** shift_mod_by_8
        assert slice_bits_polynomial[1] < 2 ** (8 - shift_mod_by_8)
