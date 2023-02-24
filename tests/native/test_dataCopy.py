import pytest

from common import CallContext
from zkevm_specs.evm import (
    Bytecode,
    CallContextFieldTag,
    ExecutionState,
    Precompile,
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
    IdentityPerWordGas,
    RLC,
    FQ,
)

CALLER_ID = 1
CALLEE_ID = 2
CALLEE_MEMORY = [0x00] * 32 + [0x11] * 32
DATACOPY_PRECOMPILE_ADDRESS = 0x04
TESTING_DATA = (
    # simple cases
    (CallContext(), 0, 5, 0, 5),
)


@pytest.mark.parametrize(
    "caller_ctx, call_data_offset, call_data_length, return_data_offset, return_data_length",
    TESTING_DATA,
)
def test_dataCopy(
    caller_ctx: CallContext,
    call_data_offset: int,
    call_data_length: int,
    return_data_offset: int,
    return_data_length: int,
):
    randomness = rand_fq()

    size = call_data_length
    call_id = CALLER_ID
    precompile_id = CALLEE_ID

    data_word_size = (size + 31) // 32
    gas = Precompile.DATACOPY.base_gas_cost() + data_word_size * IdentityPerWordGas

    code = (
        Bytecode()
        .call(
            gas,
            Precompile.DATACOPY,
            0,
            call_data_offset,
            call_data_length,
            return_data_offset,
            return_data_length,
        )
        .stop()
    )
    code_hash = RLC(code.hash(), randomness)

    rw_dictionary = (
        # fmt: off
        RWDictionary(1)
        .call_context_read(precompile_id, CallContextFieldTag.CalleeAddress, DATACOPY_PRECOMPILE_ADDRESS)
        .call_context_read(precompile_id, CallContextFieldTag.CallerId, call_id)
        .call_context_read(precompile_id, CallContextFieldTag.CallDataOffset, call_data_offset)
        .call_context_read(precompile_id, CallContextFieldTag.CallDataLength, call_data_length)
        .call_context_read(precompile_id, CallContextFieldTag.ReturnDataOffset, return_data_offset)
        .call_context_read(precompile_id, CallContextFieldTag.ReturnDataLength, return_data_length)
        # fmt: on
    )

    # rw counter before memory writes
    rw_counter_interim = rw_dictionary.rw_counter
    steps = [
        StepState(
            execution_state=ExecutionState.DATACOPY,
            rw_counter=1,
            call_id=precompile_id,
            is_root=True,
            code_hash=code_hash,
            program_counter=99,
            stack_pointer=1021,
            memory_word_size=size,
            gas_left=gas,
        ),
    ]

    src_data = dict(
        [
            (i, CALLEE_MEMORY[i] if i < len(CALLEE_MEMORY) else 0)
            for i in range(return_data_offset, return_data_offset + return_data_length)
        ]
    )

    copy_circuit = (
        CopyCircuit()
        .copy(
            randomness,
            rw_dictionary,
            call_id,
            CopyDataTypeTag.Memory,
            call_id,
            CopyDataTypeTag.Memory,
            call_data_offset,
            call_data_offset + size,
            return_data_offset,
            size,
            src_data,
        )
        .copy(
            randomness,
            rw_dictionary,
            call_id,
            CopyDataTypeTag.Memory,
            precompile_id,
            CopyDataTypeTag.Memory,
            call_data_offset,
            call_data_offset + size,
            FQ(0),
            size,
            src_data,
        )
    )

    # rw counter after memory writes
    rw_counter_final = rw_dictionary.rw_counter
    assert rw_counter_final - rw_counter_interim == size * 4  # 1 copy == 1 read & 1 write

    rw_dictionary = (
        # fmt: off
        rw_dictionary
        .call_context_read(call_id, CallContextFieldTag.IsRoot, caller_ctx.is_root)
        .call_context_read(call_id, CallContextFieldTag.IsCreate, caller_ctx.is_create)
        .call_context_read(call_id, CallContextFieldTag.CodeHash, code_hash)
        .call_context_read(call_id, CallContextFieldTag.ProgramCounter, caller_ctx.program_counter)
        .call_context_read(call_id, CallContextFieldTag.StackPointer, caller_ctx.stack_pointer)
        .call_context_read(call_id, CallContextFieldTag.GasLeft, caller_ctx.gas_left)
        .call_context_read(call_id, CallContextFieldTag.MemorySize, caller_ctx.memory_word_size)
        .call_context_read(call_id, CallContextFieldTag.ReversibleWriteCounter, caller_ctx.reversible_write_counter)
        .call_context_write(call_id, CallContextFieldTag.LastCalleeId, precompile_id)
        .call_context_write(call_id, CallContextFieldTag.LastCalleeReturnDataOffset, FQ(0))
        .call_context_write(call_id, CallContextFieldTag.LastCalleeReturnDataLength, size)
        # fmt: on
    )

    steps.append(
        StepState(
            execution_state=ExecutionState.STOP,
            rw_counter=rw_dictionary.rw_counter,
            call_id=call_id,
            is_root=caller_ctx.is_root,
            code_hash=code_hash,
            program_counter=caller_ctx.program_counter,
            stack_pointer=caller_ctx.stack_pointer,
            memory_word_size=caller_ctx.memory_word_size,
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
        randomness,
        tables,
        steps,
    )
