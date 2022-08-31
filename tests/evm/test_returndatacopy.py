from itertools import chain
import pytest
from typing import Mapping, Sequence, Tuple

from zkevm_specs.evm import (
    AccountFieldTag,
    Bytecode,
    CallContextFieldTag,
    ExecutionState,
    Opcode,
    RW,
    RWDictionary,
    RWTableTag,
    StepState,
    Tables,
    verify_steps,
    CopyCircuit,
    CopyDataTypeTag,
)
from zkevm_specs.copy_circuit import verify_copy_table
from zkevm_specs.util import (
    rand_fq,
    rand_bytes,
    memory_word_size,
    memory_expansion,
    GAS_COST_COPY,
    MAX_N_BYTES_COPY_TO_MEMORY,
    MEMORY_EXPANSION_QUAD_DENOMINATOR,
    MEMORY_EXPANSION_LINEAR_COEFF,
    RLC,
)

CALL_ID = 1
CALLEE_MEMORY = [0x00] * 32 + [0x11] * 32
TESTING_DATA = (
    # simple cases
    (0, 0, 32, 0, 32),
)


@pytest.mark.parametrize(
    "dest_offset, memory_offset, size, return_data_offset, return_data_length", TESTING_DATA
)
def test_returndatacopy(
    dest_offset: int,
    memory_offset: int,
    size: int,
    return_data_offset: int,
    return_data_length: int,
):
    randomness = rand_fq()

    dest_offset_rlc = RLC(dest_offset, randomness)
    memory_offset_rlc = RLC(memory_offset, randomness)
    size_rlc = RLC(size, randomness)

    code = (
        Bytecode()
        .push32(size_rlc)
        .push32(memory_offset_rlc)
        .push32(dest_offset_rlc)
        .returndatacopy()
        .stop()
    )
    code_hash = RLC(code.hash(), randomness)

    next_mem_size, memory_gas_cost = memory_expansion(0, memory_offset + size)
    gas = (
        Opcode.RETURNDATACOPY.constant_gas_cost()
        + memory_gas_cost
        + memory_word_size(size) * GAS_COST_COPY
    )
    rw_dictionary = (
        RWDictionary(1)
        .stack_read(CALL_ID, 1021, dest_offset_rlc)
        .stack_read(CALL_ID, 1022, memory_offset_rlc)
        .stack_read(CALL_ID, 1023, size_rlc)
        .call_context_read(
            CALL_ID, CallContextFieldTag.LastCalleeReturnDataLength, return_data_length
        )
        .call_context_read(
            CALL_ID, CallContextFieldTag.LastCalleeReturnDataOffset, return_data_offset
        )
    )
    # rw counter before memory writes
    rw_counter_interim = rw_dictionary.rw_counter

    bytecode = Bytecode().extcodecopy()
    bytecode_hash = RLC(bytecode.hash(), randomness)
    steps = [
        StepState(
            execution_state=ExecutionState.RETURNDATACOPY,
            rw_counter=1,
            call_id=CALL_ID,
            is_root=True,
            code_hash=code_hash,
            program_counter=99,
            stack_pointer=1021,
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
        randomness,
        rw_dictionary,
        code_hash.rlc_value,
        CopyDataTypeTag.Memory,
        CALL_ID,
        CopyDataTypeTag.Memory,
        return_data_offset,
        len(code.code),
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
            memory_size=next_mem_size,
            gas_left=0,
        )
    )

    print(f"rw_dictionary.rws = {rw_dictionary.rws}")
    tables = Tables(
        block_table=set(),
        tx_table=set(),
        bytecode_table=set(code.table_assignments(randomness)),
        rw_table=set(rw_dictionary.rws),
        copy_circuit=copy_circuit.rows,
    )

    verify_copy_table(copy_circuit, tables, randomness)

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=steps,
    )
