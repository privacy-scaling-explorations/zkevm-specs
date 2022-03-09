from ..encoding import U8, U64, U128, U256
from typing import Sequence, Tuple
from .param import MEMORY_EXPANSION_LINEAR_COEFF


def memory_word_size(
    address: U64,
) -> U64:
    return (address + 31) // 32


def div(
    value: U256,
    divisor: U64,
) -> Tuple[U256, U256]:
    quotient = value // divisor
    remainder = value % divisor
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
    (curr_quad_memory_cost, _) = div(curr_memory_size * curr_memory_size, 512)
    (next_quad_memory_cost, _) = div(next_memory_size * next_memory_size, 512)

    # Calculate the gas cost for the memory expansion
    # This gas cost is the difference between the next and current memory costs
    memory_gas_cost = (next_memory_size - curr_memory_size) * MEMORY_EXPANSION_LINEAR_COEFF + (
        next_quad_memory_cost - curr_quad_memory_cost
    )

    # Return the new memory size and the memory expansion gas cost
    return next_memory_size, memory_gas_cost
