from zkevm_specs.opcode.memory import Memory
from ..encoding import U64, is_circuit_code


@is_circuit_code
def check_msize(
    memory: Memory,
    curr_memory_size: U64,
):
    assert memory.memory_size() == curr_memory_size
