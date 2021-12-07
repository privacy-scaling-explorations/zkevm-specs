import random
import pytest

from zkevm_specs.encoding import u256_to_u8s, u8s_to_u256
from zkevm_specs.opcode import check_and, check_or, check_xor


def test_and():
    for _ in range(5):
        a = random.randint(0, 2 ** 256)
        b = random.randint(0, 2 ** 256)
        c = a & b
        a8s = u256_to_u8s(a)
        b8s = u256_to_u8s(b)
        c8s = u256_to_u8s(c)
        check_and(a8s, b8s, c8s)


def test_check_or():
    for _ in range(5):
        a = random.randint(0, 2 ** 256)
        b = random.randint(0, 2 ** 256)
        c = a | b
        a8s = u256_to_u8s(a)
        b8s = u256_to_u8s(b)
        c8s = u256_to_u8s(c)
        check_or(a8s, b8s, c8s)


def test_check_xor():
    for i in range(5):
        print(i)
        a = random.randint(0, 2 ** 256)
        b = random.randint(0, 2 ** 256)
        c = a ^ b
        a8s = u256_to_u8s(a)
        b8s = u256_to_u8s(b)
        c8s = u256_to_u8s(c)
        check_xor(a8s, b8s, c8s)
