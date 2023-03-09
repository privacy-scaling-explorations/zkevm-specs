import pytest

from zkevm_specs.evm import (
    Bytecode,
    CallContextFieldTag,
    ExecutionState,
    Opcode,
    RWDictionary,
    StepState,
    Tables,
    verify_steps,
    CopyCircuit,
    CopyDataTypeTag,
)
from zkevm_specs.copy_circuit import verify_copy_table
from zkevm_specs.util import (
    rand_fq,
    GAS_COST_COPY,
    Word,
)
from common import memory_expansion, memory_word_size

CALL_ID = 1
CALLEE_ID = 2
CALLEE_MEMORY = [0x00] * 32 + [0x11] * 32
TESTING_DATA = (
    # simple cases
    (0, 0, 32, 0, 32),
    (100, 0, 32, 0, 32),
    (0, 0, 32, 100, 32),
    (100, 31, 1, 100, 32),
)


@pytest.mark.parametrize(
    "dest_offset, offset, size, return_data_offset, return_data_length", TESTING_DATA
)
def test_returndatacopy(
    dest_offset: int,
    offset: int,
    size: int,
    return_data_offset: int,
    return_data_length: int,
):
    randomness_keccak = rand_fq()

    dest_offset_word = Word(dest_offset)
    memory_offset_word = Word(offset)
    size_word = Word(size)

    code = (
        Bytecode()
        .push32(size_word)
        .push32(memory_offset_word)
        .push32(dest_offset_word)
        .returndatacopy()
        .stop()
    )
    code_hash = Word(code.hash())

    # assume return data is at the current largest memory pos
    curr_mem_size = memory_word_size(return_data_offset + return_data_length)
    next_mem_size, memory_gas_cost = memory_expansion(curr_mem_size, dest_offset + size)
    gas = (
        Opcode.RETURNDATACOPY.constant_gas_cost()
        + memory_gas_cost
        + memory_word_size(size) * GAS_COST_COPY
    )
    rw_dictionary = (
        RWDictionary(1)
        .stack_read(CALL_ID, 1021, dest_offset_word)
        .stack_read(CALL_ID, 1022, memory_offset_word)
        .stack_read(CALL_ID, 1023, size_word)
        .call_context_read(CALL_ID, CallContextFieldTag.LastCalleeId, CALLEE_ID)
        .call_context_read(
            CALL_ID, CallContextFieldTag.LastCalleeReturnDataLength, return_data_length
        )
        .call_context_read(
            CALL_ID, CallContextFieldTag.LastCalleeReturnDataOffset, return_data_offset
        )
    )
    # rw counter before memory writes
    rw_counter_interim = rw_dictionary.rw_counter
    steps = [
        StepState(
            execution_state=ExecutionState.RETURNDATACOPY,
            rw_counter=1,
            call_id=CALL_ID,
            is_root=True,
            code_hash=code_hash,
            program_counter=99,
            stack_pointer=1021,
            memory_word_size=curr_mem_size,
            gas_left=gas,
        ),
    ]

    src_data = dict(
        [
            (i, CALLEE_MEMORY[i] if i < len(CALLEE_MEMORY) else 0)
            for i in range(return_data_offset, return_data_offset + return_data_length)
        ]
    )
    copy_circuit = CopyCircuit().copy(
        randomness_keccak,
        rw_dictionary,
        CALLEE_ID,
        CopyDataTypeTag.Memory,
        CALL_ID,
        CopyDataTypeTag.Memory,
        return_data_offset,
        return_data_offset + size,
        dest_offset,
        size,
        src_data,
    )

    # rw counter post memory writes
    rw_counter_final = rw_dictionary.rw_counter
    assert rw_counter_final - rw_counter_interim == size * 2  # 1 copy == 1 read & 1 write

    steps.append(
        StepState(
            execution_state=ExecutionState.STOP,
            rw_counter=rw_dictionary.rw_counter,
            call_id=CALL_ID,
            is_root=True,
            code_hash=code_hash,
            program_counter=100,
            stack_pointer=1024,
            memory_word_size=next_mem_size,
            gas_left=0,
        )
    )

    tables = Tables(
        block_table=set(),
        tx_table=set(),
        bytecode_table=set(code.table_assignments()),
        rw_table=set(rw_dictionary.rws),
        copy_circuit=copy_circuit.rows,
    )

    verify_copy_table(copy_circuit, tables, randomness_keccak)

    verify_steps(
        tables=tables,
        steps=steps,
    )
