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
)
from zkevm_specs.util import rand_fq, RLC
from common import memory_expansion

TESTING_DATA = (
    (
        Opcode.MLOAD,
        0,
        0xFF,
        bytes.fromhex("00000000000000000000000000000000000000000000000000000000000000FF"),
    ),
    (
        Opcode.MLOAD,
        1,
        0xFF00,
        bytes.fromhex("00000000000000000000000000000000000000000000000000000000000000FF"),
    ),
    (
        Opcode.MSTORE,
        0,
        0xFF,
        bytes.fromhex("00000000000000000000000000000000000000000000000000000000000000FF"),
    ),
    (
        Opcode.MSTORE,
        1,
        0xFF,
        bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000000FF"),
    ),
    (
        Opcode.MSTORE8,
        0,
        bytes.fromhex("FFFF"),
        bytes.fromhex("FF"),
    ),
    (
        Opcode.MSTORE8,
        1,
        bytes.fromhex("FF"),
        bytes.fromhex("FFFF"),
    ),
)


@pytest.mark.parametrize("opcode, offset, value, memory", TESTING_DATA)
def test_memory(opcode: Opcode, offset: int, value: int, memory: bytes):
    randomness = rand_fq()

    offset_rlc = RLC(offset, randomness)
    value_rlc = RLC(value, randomness)
    call_id = 1
    curr_memory_word_size = 0
    length = offset

    is_mload = opcode == Opcode.MLOAD
    is_mstore8 = opcode == Opcode.MSTORE8
    is_store = 1 - is_mload
    is_not_mstore8 = 1 - is_mstore8

    bytecode = (
        Bytecode().mload(offset_rlc).stop()
        if is_mload
        else Bytecode().mstore8(offset_rlc, value_rlc).stop()
        if is_mstore8
        else Bytecode().mstore(offset_rlc, value_rlc).stop()
    )
    rw_dictionary = (
        RWDictionary(1).stack_read(call_id, 1022, offset_rlc).stack_write(call_id, 1022, value_rlc)
        if is_mload
        else RWDictionary(1)
        .stack_read(call_id, 1022, offset_rlc)
        .stack_read(call_id, 1023, value_rlc)
    )

    bytecode_hash = RLC(bytecode.hash(), randomness)
    if is_mstore8:
        rw_dictionary.memory_write(call_id, length, value[0])

    if is_not_mstore8:
        for idx in range(32):
            if is_mload:
                rw_dictionary.memory_read(call_id, offset + idx, memory[idx])
            else:
                rw_dictionary.memory_write(call_id, offset + idx, memory[idx])

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=rw_dictionary.rws,
    )

    address = offset + 1 + (is_not_mstore8 * 31)
    next_mem_size, memory_gas_cost = memory_expansion(curr_memory_word_size, address)
    gas = Opcode.MLOAD.constant_gas_cost() + memory_gas_cost

    rw_counter = 35 - (is_mstore8 * 31)
    program_counter = 66 - (is_mload * 33)
    stack_pointer = 1022 + (is_store * 2)

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
                program_counter=program_counter,
                stack_pointer=1022,
                gas_left=gas,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=rw_counter,
                call_id=call_id,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=program_counter + 1,
                stack_pointer=stack_pointer,
                memory_word_size=next_mem_size,
                gas_left=0,
            ),
        ],
    )
