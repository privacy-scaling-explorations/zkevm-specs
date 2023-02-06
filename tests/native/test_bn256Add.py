import pytest
from collections import namedtuple

from zkevm_specs.util import rand_fq, RLC
from zkevm_specs.evm import (
    Precompile,
    Bytecode,
    RWDictionary,
    StepState,
    ExecutionState,
    CallContextFieldTag,
)
from common import PrecompileCallContext, generate_sassy_tests

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

    size = call_data_length
    call_id = CALLER_ID
    precompile_id = CALLEE_ID
    point = generate_sassy_tests()

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
        .call_context_read(precompile_id, CallContextFieldTag.CallDataLength, call_data_length)
        .call_context_read(precompile_id, CallContextFieldTag.ReturnDataOffset, return_data_offset)
        .call_context_read(precompile_id, CallContextFieldTag.ReturnDataLength, return_data_length)
        # fmt: on
    )

    # rw counter before memory writes
    rw_counter_interim = rw_dictionary.rw_counter
    steps = [
        StepState(
            execution_state=ExecutionState.BN256ADD,
            rw_counter=1,
            call_id=precompile_id,
            is_root=True,
            code_hash=code_hash,
            program_counter=99,
            stack_pointer=1021,
            memory_size=size,
            gas_left=gas,
        ),
    ]
