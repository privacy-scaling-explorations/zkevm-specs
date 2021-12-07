from zkevm_specs.encoding import u256_to_u8s
from zkevm_specs.opcode import check_byte


def test_byte():
    value = range(1, 33)
    for i in range(1024):
        i8s = u256_to_u8s(i)
        r8s = [i + 1 if i < 32 else 0] + [0] * 31
        check_byte(value, i8s, r8s)
