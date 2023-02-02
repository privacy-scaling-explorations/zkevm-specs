import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    Opcode,
    verify_steps,
    Tables,
    Block,
    Bytecode,
    RWDictionary,
    RWTableTag,
)
from zkevm_specs.util import rand_fq, RLC, U64, GAS_COST_COPY, memory_expansion, memory_word_size

TESTING_DATA = (
    (
        Opcode.MLOAD,
        0,
        bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000000"),
    ),
)


@pytest.mark.parametrize("opcode, offset, value", TESTING_DATA)
def test_memory(opcode: Opcode, offset: int, value: bytes):
    randomness = rand_fq()

    offset_rlc = RLC(offset, randomness)
    value_rlc = RLC(value, randomness)
    call_id = 1
    memory_offset = 0
    length = offset

    bytecode = Bytecode().mload(offset_rlc).stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    is_mload = opcode == Opcode.MLOAD
    is_mstore8 = opcode == Opcode.MSTORE8
    is_store = 1 - is_mload
    is_not_mstore8 = 1 - is_mstore8

    rw_dictionary = (
        RWDictionary(1).stack_read(call_id, 1022, offset_rlc).stack_write(call_id, 1022, value_rlc)
    )

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=rw_dictionary.rws,
    )

    next_mem_size, memory_gas_cost = memory_expansion(memory_offset, length + 1)

    gas = Opcode.MLOAD.constant_gas_cost() + memory_gas_cost + length * GAS_COST_COPY

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.MEMORY,
                rw_counter=1,
                call_id=call_id,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=33,
                stack_pointer=1022,
                gas_left=gas,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=35,
                call_id=call_id,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=34,
                stack_pointer=1022,
                memory_size=1,
                gas_left=0,
            ),
        ],
    )
