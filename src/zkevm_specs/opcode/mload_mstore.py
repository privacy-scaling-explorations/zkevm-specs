from typing import Sequence, Tuple
from zkevm_specs.opcode.memory import Memory
from ..encoding import U8, U64, U128, U256, is_circuit_code

OP_MLOAD = 0x51
OP_MSTORE = 0x52
OP_MSTORE8 = 0x53

G_MEM = 3

NUM_ADDRESS_BYTES_USED = 5


@is_circuit_code
def address_low(
    address: Sequence[U8],
) -> U64:
    return sum(x * (2 ** (8 * i)) for i, x in enumerate(address[:NUM_ADDRESS_BYTES_USED]))


@is_circuit_code
def address_high(
    address: Sequence[U8],
) -> U256:
    return sum(address[NUM_ADDRESS_BYTES_USED:])


@is_circuit_code
def require_address_in_range(
    address: Sequence[U8],
):
    assert address_high(address) == 0


@is_circuit_code
def select(
    selector: U8,
    when_true: U256,
    when_false: U256,
) -> U256:
    return selector * when_true + (1 - selector) * when_false


@is_circuit_code
def div(
    value: U256,
    divisor: U64,
) -> Tuple[U256, U256]:
    quotient = value // divisor
    remainder = value % divisor
    return (quotient, remainder)


@is_circuit_code
def lt(
    lhs: U256,
    rhs: U256,
) -> U256:
    return lhs < rhs


@is_circuit_code
def max(
    lhs: U256,
    rhs: U256,
) -> U256:
    return select(lt(lhs, rhs), rhs, lhs)


@is_circuit_code
def memory_size(
    address: U64,
) -> U64:
    return (address + 31) // 32


@is_circuit_code
def memory_expansion(
    curr_memory_size: U64,
    address: U64,
) -> Tuple[U64, U128]:
    # The memory size required for the used address
    address_memory_size = memory_size(address)

    # Expand the memory if needed
    next_memory_size = max(address_memory_size, curr_memory_size)

    # Calculate the quad memory cost
    (curr_quad_memory_cost, _) = div(curr_memory_size * curr_memory_size, 512)
    (next_quad_memory_cost, _) = div(next_memory_size * next_memory_size, 512)

    # Calculate the gas cost for the memory expansion
    # This gas cost is the difference between the next and current memory costs
    memory_gas_cost = (next_memory_size - curr_memory_size) * G_MEM + (next_quad_memory_cost - curr_quad_memory_cost)

    # Return the new memory size and the memory expansion gas cost
    return (next_memory_size, memory_gas_cost)


@is_circuit_code
def check_memory_ops(
    opcode: U8,
    memory: Memory,
    address8s: Sequence[U8],
    value8s: Sequence[U8],
    curr_memory_size: U64,
    expected_next_memory_size: U64,
    expected_memory_cost: U128,
):
    assert len(address8s) == len(value8s) == 32
    assert memory.memory_size() == curr_memory_size

    # Check if this is an MLOAD, MSTORE or MSTORE8
    is_mload = opcode == OP_MLOAD
    is_mstore8 = opcode == OP_MSTORE8
    is_store = 1 - is_mload
    is_not_mstore8 = 1 - is_mstore8

    # Not all address bytes are used to calculate the gas cost for the memory access,
    # so make sure this success case is disabled if any of those address bytes
    # are actually used.
    require_address_in_range(address8s)
    # Get the capped address value we will use in the memory calculations
    address = address_low(address8s)

    # Calculate the next memory size and the gas cost for this memory access
    (next_memory_size, memory_cost) = memory_expansion(curr_memory_size, address + 1 + is_not_mstore8 * 31)
    assert next_memory_size == expected_next_memory_size
    assert memory_cost == expected_memory_cost

    # Read/Write the value from memory at the specified address
    for i in range(0, 32):
        # For MSTORE8 we write the LSB of value 32x times to the same address
        # For MLOAD and MSTORE we read/write all the bytes of value
        # at an increasing address value.
        byte = value8s[0] if i == 31 else select(is_mstore8, value8s[0], value8s[31 - i])
        offset = 0 if i == 0 else is_not_mstore8 * i
        memory.op(address + offset, byte, is_store)

    # Also verify the expected memory size against the one calculated by Memory
    assert expected_next_memory_size == memory.memory_size()
