import pytest

from collections import namedtuple
from zkevm_specs.util import rand_fq, MAX_MEMORY_SIZE, RLC
from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    CallContextFieldTag,
    Block,
    Transaction,
    Bytecode,
    RWDictionary,
)

CallContext = namedtuple(
    "CallContext",
    [
        "is_root",
        "is_create",
        "program_counter",
        "stack_pointer",
        "gas_left",
        "memory_size",
        "reversible_write_counter",
    ],
    defaults=[True, False, 232, 1023, 0, 0, 0],
)

TEST_DATA = CallContext(memory_size=MAX_MEMORY_SIZE)


@pytest.mark.parametrize("caller_ctx", TEST_DATA)
def test_error_gas_uint_overflow(caller_ctx: CallContext):
    randomness = rand_fq()

    bytecode = Bytecode().add()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(RWDictionary(24).call_context_read(1, CallContextFieldTag.IsSuccess, 0).rws),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorGasUintOverflow,
                rw_counter=24,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=0,
                stack_pointer=1023,
                gas_left=2,
                reversible_write_counter=0,
            ),
            StepState(
                execution_state=ExecutionState.EndTx,
                rw_counter=25,
                call_id=1,
                gas_left=0,
            ),
        ],
    )
