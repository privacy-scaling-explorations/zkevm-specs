import pytest
from common import generate_sassy_tests
from zkevm_specs.evm import (
    Bytecode,
    CallContextFieldTag,
    ExecutionState,
    Precompile,
    RWDictionary,
    StepState,
    Tables,
    CopyCircuit,
    CopyDataTypeTag,
    verify_steps,
)
from zkevm_specs.util import (
    rand_fq,
    RLC,
    FQ,
)
from zkevm_specs.copy_circuit import verify_copy_table
from common import PrecompileCallContext

CALLER_ID = 1
CALLEE_ID = 2
BN256ADD_PRECOMPILE_ADDRESS = 0x06

TESTING_DATA = generate_sassy_tests()


@pytest.mark.parametrize(
    "caller_ctx, call_data_offset, call_data_length, return_data_offset, return_data_length, input, result",
    TESTING_DATA,
)
def test_bn256Add(
    caller_ctx: PrecompileCallContext,
    call_data_offset: int,
    call_data_length: int,
    return_data_offset: int,
    return_data_length: int,
    input: bytes,
    result: bytes,
):
    randomness = rand_fq()

    input_size = call_data_length
    result_size = return_data_length
    call_id = CALLER_ID
    precompile_id = CALLEE_ID

    gas = Precompile.BN256ADD.base_gas_cost()

    code = (
        Bytecode()
        .call(
            gas,
            Precompile.BN256ADD,
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
        .call_context_read(precompile_id, CallContextFieldTag.CalleeAddress, BN256ADD_PRECOMPILE_ADDRESS)
        .call_context_read(precompile_id, CallContextFieldTag.CallerId, call_id)
        .call_context_read(precompile_id, CallContextFieldTag.CallDataOffset, call_data_offset)
        .call_context_read(precompile_id, CallContextFieldTag.ReturnDataOffset, return_data_offset)
        # fmt: on
    )

    # get points a and b from input
    for i in range(128):
        rw_dictionary.memory_read(precompile_id, call_data_offset + i, input[i])

    # store result point to memory
    for i in range(64):
        rw_dictionary.memory_write(precompile_id, return_data_offset + i, result[i])

    result_src_data = dict(
        [
            (i, input[i] if i < len(input) else 0)
            for i in range(return_data_offset, return_data_offset + result_size)
        ]
    )

    copy_circuit = CopyCircuit().copy(
        randomness,
        rw_dictionary,
        call_id,
        CopyDataTypeTag.Memory,
        precompile_id,
        CopyDataTypeTag.Memory,
        return_data_offset,
        return_data_offset + result_size,
        FQ(0),
        result_size,
        result_src_data,
    )

    rw_dictionary = (
        # fmt: off
        rw_dictionary
        .call_context_read(call_id, CallContextFieldTag.IsRoot, caller_ctx.is_root)
        .call_context_read(call_id, CallContextFieldTag.IsCreate, caller_ctx.is_create)
        .call_context_read(call_id, CallContextFieldTag.CodeHash, code_hash)
        .call_context_read(call_id, CallContextFieldTag.ProgramCounter, caller_ctx.program_counter)
        .call_context_read(call_id, CallContextFieldTag.StackPointer, caller_ctx.stack_pointer)
        .call_context_read(call_id, CallContextFieldTag.GasLeft, caller_ctx.gas_left)
        .call_context_read(call_id, CallContextFieldTag.MemorySize, caller_ctx.memory_size)
        .call_context_read(call_id, CallContextFieldTag.ReversibleWriteCounter, caller_ctx.reversible_write_counter)
        .call_context_write(call_id, CallContextFieldTag.LastCalleeId, precompile_id)
        .call_context_write(call_id, CallContextFieldTag.LastCalleeReturnDataOffset, FQ(0))
        .call_context_write(call_id, CallContextFieldTag.LastCalleeReturnDataLength, result_size)
        # fmt: on
    )

    steps = [
        StepState(
            execution_state=ExecutionState.BN256ADD,
            rw_counter=1,
            call_id=precompile_id,
            is_root=True,
            code_hash=code_hash,
            program_counter=99,
            stack_pointer=1021,
            memory_size=caller_ctx.memory_size,
            gas_left=gas,
        ),
        StepState(
            execution_state=ExecutionState.STOP,
            rw_counter=rw_dictionary.rw_counter,
            call_id=call_id,
            is_root=caller_ctx.is_root,
            code_hash=code_hash,
            program_counter=caller_ctx.program_counter,
            stack_pointer=caller_ctx.stack_pointer,
            memory_size=caller_ctx.memory_size,
            gas_left=0,
        ),
    ]

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
