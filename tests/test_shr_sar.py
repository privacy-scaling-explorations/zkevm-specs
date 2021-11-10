import secrets

from src.zkevm_specs.encoding import u256_to_u8s, U256, u8s_to_u64s, U8
from src.zkevm_specs.opcode.shr_sar import check_shr, check_sar, BitslevelTable, Pow64Table


def generate_high(shift_mod_by_64_div_by_8, shift_mod_by_8):
    count = 8 * shift_mod_by_64_div_by_8 + shift_mod_by_8
    return 2 ** 64 - 2 ** (64 - count)


def result_generate(a, shift):
    b = a >> shift
    a8s = u256_to_u8s(U256(a))
    b8s = u256_to_u8s(U256(b))
    if a8s[31] >= 128:
        is_sar = 1
    else:
        is_sar = 0

    shift_div_by_64 = shift // 64
    shift_mod_by_64_div_by_8 = shift % 64 // 8
    shift_mod_by_64 = shift % 64
    shift_mod_by_64_pow = 1 << shift_mod_by_64
    shift_mod_by_64_decpow = (1 << 64) // shift_mod_by_64_pow
    shift_mod_by_8 = shift % 8
    print("shift_div_by_64 : ", shift_div_by_64)
    print("shift_mod_by_64 : ", shift_mod_by_64)
    print("shift_mod_by_64_div_by_8 : ", shift_mod_by_64_div_by_8)
    print("shift_mod_by_64_pow: ", shift_mod_by_64_pow)
    print("shift_mod_by_64_decpow: ", shift_mod_by_64_decpow)
    print("shift_mod_by_8 : ", shift_mod_by_8)
    high_cell = shift_div_by_64 * 8 + shift_mod_by_64_div_by_8
    b1 = list(b8s)
    if is_sar == 1:
        idx = 0
        while idx != high_cell:
            b1[31 - idx] = 255
            idx += 1
        m8 = 255 - (1 << (8 - shift_mod_by_8)) + 1
        b1[31 - high_cell] += m8
    print("b1:", b1)
    a64s = u8s_to_u64s(a8s)
    a_slice_front = [U8(0)] * 32
    a_slice_back = [U8(0)] * 32
    for virtual_idx in range(0, 4):
        if shift_mod_by_64 == 0:
            slice_back = a64s[virtual_idx]
            slice_front = 0
        else:
            slice_back = a64s[virtual_idx] % (1 << shift_mod_by_64)
            slice_front = a64s[virtual_idx] // (1 << shift_mod_by_64)
        assert slice_front * (1 << shift_mod_by_64) + slice_back == a64s[virtual_idx]

        for idx in range(0, 8):
            now_idx = virtual_idx * 8 + idx
            a_slice_back[now_idx] = U8(slice_back % (1 << 8))
            a_slice_front[now_idx] = U8(slice_front % (1 << 8))
            slice_back = slice_back >> 8
            slice_front = slice_front >> 8
    print("a_slice_back:", a_slice_back)
    print("a_slice_front:", a_slice_front)
    m256 = [U8(255)] * 32

    high_pow = generate_high(shift_mod_by_64_div_by_8, shift_mod_by_8)
    return (b1,
            a_slice_front,
            a_slice_back,
            shift_div_by_64,
            shift_mod_by_64_div_by_8,
            shift_mod_by_64_decpow,
            shift_mod_by_64_pow,
            shift_mod_by_8,
            is_sar,
            high_pow,
            m256)


def test_shr_sar():
    a = secrets.randbelow(2 ** 256)
    bitsleveltable = BitslevelTable()
    pow64table = Pow64Table()
    print()
    print("a8s:", u256_to_u8s(U256(a)))
    a_bits = len(bin(a)) - 2
    print("a_bits:", a_bits)
    shift = secrets.randbelow(a_bits)
    print("shift:", shift)
    (b,
     a_slice_front,
     a_slice_back,
     shift_div_by_64,
     shift_mod_by_64_div_by_8,
     shift_mod_by_64_decpow,
     shift_mod_by_64_pow,
     shift_mod_by_8,
     is_sar,
     high_pow,
     m256) = result_generate(a, shift)

    if is_sar == 0:
        check_shr(u256_to_u8s(U256(a)),
                  b,
                  U8(shift),
                  a_slice_front,
                  a_slice_back,
                  shift_div_by_64,
                  shift_mod_by_64_div_by_8,
                  shift_mod_by_64_decpow,
                  shift_mod_by_64_pow,
                  shift_mod_by_8,
                  is_sar,
                  high_pow,
                  m256,
                  bitsleveltable,
                  pow64table)
    else:
        check_sar(u256_to_u8s(U256(a)),
                  b,
                  U8(shift),
                  a_slice_front,
                  a_slice_back,
                  shift_div_by_64,
                  shift_mod_by_64_div_by_8,
                  shift_mod_by_64_decpow,
                  shift_mod_by_64_pow,
                  shift_mod_by_8,
                  is_sar,
                  high_pow,
                  m256,
                  bitsleveltable,
                  pow64table)
