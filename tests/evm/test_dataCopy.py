import math
import pytest
from itertools import chain
from typing import Mapping, Sequence, Tuple

from zkevm_specs.evm import (
    AccountFieldTag,
    Bytecode,
    CallContextFieldTag,
    ExecutionState,
    Opcode,
    Precompile,
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
    IdentityPerWordGas,
    GAS_COST_COPY,
    MAX_N_BYTES_COPY_TO_MEMORY,
    MEMORY_EXPANSION_QUAD_DENOMINATOR,
    MEMORY_EXPANSION_LINEAR_COEFF,
    RLC,
)

CALL_ID = 1
CALLEE_ID = 2
CALLEE_MEMORY = [0x00] * 32 + [0x11] * 32
TESTING_DATA = (
    # simple cases
    (0, 32, 0, 32),
)


@pytest.mark.parametrize(
    "call_data_offset, call_data_length, return_data_offset, return_data_length", TESTING_DATA
)
def test_dataCopy(
    call_data_offset: int,
    call_data_length: int,
    return_data_offset: int,
    return_data_length: int,
):
    randomness = rand_fq()

    size = call_data_length
    call_data_offset_rlc = RLC(call_data_offset, randomness)
    call_data_length_rlc = RLC(call_data_length, randomness)
    return_data_offset_rlc = RLC(return_data_offset, randomness)
    return_data_length_rlc = RLC(return_data_length, randomness)

    code = Bytecode(is_include_precompile=True).dataCopy().stop()
    code_hash = RLC(code.hash(), randomness)

    data_word_size = math.ceil((size + 31) / 32)
    gas = Precompile.DATACOPY.base_gas_cost() + data_word_size * IdentityPerWordGas

    rw_dictionary = (
        RWDictionary(1)
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
            execution_state=ExecutionState.DATACOPY,
            rw_counter=1,
            call_id=CALL_ID,
            is_root=True,
            code_hash=code_hash,
            program_counter=99,
            stack_pointer=1021,
            memory_size=size,
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
        CALLEE_ID,
        CopyDataTypeTag.Memory,
        CALL_ID,
        CopyDataTypeTag.Memory,
        return_data_offset,
        return_data_offset + size,
        return_data_offset,
        size,
        src_data,
    )

    # rw counter after memory writes
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
            memory_size=size,
            gas_left=0,
        )
    )

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
