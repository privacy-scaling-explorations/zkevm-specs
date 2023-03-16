from typing import Tuple, Union
from collections import namedtuple
from Crypto.Random import get_random_bytes
from Crypto.Random.random import randrange
from zkevm_specs.util import U64, U128, U160, U256, MEMORY_EXPANSION_LINEAR_COEFF, FQ

CallContext = namedtuple(
    "CallContext",
    [
        "is_root",
        "is_create",
        "program_counter",
        "stack_pointer",
        "gas_left",
        "memory_word_size",
        "reversible_write_counter",
        "rw_counter_end_of_reversion",
        "is_persistent",
    ],
    defaults=[True, False, 232, 1023, 0, 0, 0, 0, True],
)

NASTY_AB_VALUES = (
    (0, 0),
    (1, 0),
    (0, 1),
    (1, 1),
    (255, 0),
    (0, 255),
    (255, 255),
    (256, 0),
    (0, 256),
    (256, 256),
    (260, 513),
    (65535, 0),
    (0, 65535),
    (65535, 65535),
    (65536, 0),
    (0, 65536),
    (65536, 65536),
    ((1 << 256) - 1, (1 << 256) - 2),
    ((1 << 256) - 2, (1 << 256) - 1),
    ((1 << 256) - 1, 0),
    (0, (1 << 256) - 1),
)


def generate_nasty_tests(tests, opcodes):
    for opcode in opcodes:
        for a, b in NASTY_AB_VALUES:
            tests.append((opcode, a, b))


def memory_word_size(
    address: U64,
) -> U64:
    return U64((address + 31) // 32)


def div(
    value: U256,
    divisor: U64,
) -> Tuple[U256, U256]:
    quotient = U256(value // divisor)
    remainder = U256(value % divisor)
    return (quotient, remainder)


def memory_expansion(
    curr_memory_size: U64,
    address: U64,
) -> Tuple[U64, U128]:
    # The memory size required for the used address
    address_memory_size = memory_word_size(address)

    # Expand the memory if needed
    next_memory_size = max(address_memory_size, curr_memory_size)

    # Calculate the quad memory cost
    (curr_quad_memory_cost, _) = div(U256(curr_memory_size * curr_memory_size), U64(512))
    (next_quad_memory_cost, _) = div(U256(next_memory_size * next_memory_size), U64(512))

    # Calculate the gas cost for the memory expansion
    # This gas cost is the difference between the next and current memory costs
    memory_gas_cost = (next_memory_size - curr_memory_size) * MEMORY_EXPANSION_LINEAR_COEFF + (
        next_quad_memory_cost - curr_quad_memory_cost
    )

    # Return the new memory size and the memory expansion gas cost
    return (next_memory_size, U128(memory_gas_cost))


def rand_range(stop: Union[int, float] = 2**256) -> int:
    return randrange(0, int(stop))


def rand_fq() -> FQ:
    return FQ(rand_range(FQ.field_modulus))


def rand_address() -> U160:
    return U160(rand_range(2**160))


def rand_word() -> U256:
    return U256(rand_range(2**256))


def rand_bytes(n_bytes: int = 32) -> bytes:
    return get_random_bytes(n_bytes)
