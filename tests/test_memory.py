from zkevm_specs.encoding import u256_to_u8s
from zkevm_specs.opcode import check_memory_ops, Memory, OP_MLOAD, OP_MSTORE, OP_MSTORE8, G_MEM


def test_check_memory_ops():

    memory = Memory()
    # Store a value at address 0
    check_memory_ops(OP_MSTORE, memory, u256_to_u8s(0), range(1, 33), 0, 1, G_MEM)
    # Check if the value is indeed stored in memory
    check_memory_ops(OP_MLOAD, memory, u256_to_u8s(0), range(1, 33), 1, 1, 0)
    # Read the memory at address 1
    check_memory_ops(OP_MLOAD, memory, u256_to_u8s(1), [0] + list(range(1, 32)), 1, 2, G_MEM)
    # Read the memory at address 32
    check_memory_ops(OP_MLOAD, memory, u256_to_u8s(32), [0] * 32, 2, 2, 0)
    # Store a byte at address 32
    check_memory_ops(OP_MSTORE8, memory, u256_to_u8s(32), range(1, 33), 2, 2, 0)
    # Read the memory at address 32
    check_memory_ops(OP_MLOAD, memory, u256_to_u8s(32), [0] * 31 + [1], 2, 2, 0)
    # Reset memory
    memory = Memory()
    # Store a byte at address 31
    check_memory_ops(OP_MSTORE8, memory, u256_to_u8s(31), range(1, 33), 0, 1, G_MEM)
    # Store a byte at address 32
    check_memory_ops(OP_MSTORE8, memory, u256_to_u8s(32), range(1, 33), 1, 2, G_MEM)

    # Test against some values acquired from traces
    memory = Memory()
    # Store a value at address 0x12FFFF
    check_memory_ops(OP_MSTORE, memory, u256_to_u8s(0x12FFFF), range(1, 33), 0, 1_245_216 // 32, 3_074_203)
    # Load a value at address 0x230212
    check_memory_ops(OP_MLOAD, memory, u256_to_u8s(0x230212), [0] * 32, 1_245_216 // 32, 2_294_336 // 32, 7_181_131)
    # Store a value at address 0x131541
    check_memory_ops(OP_MSTORE, memory, u256_to_u8s(0x131541), range(1, 33), 2_294_336 // 32, 2_294_336 // 32, 0)

    # Verify Geth max allowed address
    memory = Memory()
    check_memory_ops(OP_MLOAD, memory, u256_to_u8s(0x1FFFFFFFC0), [0] * 32, 0, 0xFFFFFFFF, 0x800002FEFFFFFD)

    # Verify zkEVM max allowed address
    memory = Memory()
    check_memory_ops(OP_MLOAD, memory, u256_to_u8s(0xFFFFFFFFFF), [0] * 32, 0, 0x800000001, 0x2000001808000003)
