import pytest

from zkevm_specs.evm import (
    Bytecode,
    CallContextFieldTag,
    ExecutionState,
    StepState,
    Tables,
    verify_steps,
    RWDictionary,
)
from zkevm_specs.util import rand_fq, RLC

TESTING_DATA = ()


@pytest.mark.parametrize("value", TESTING_DATA)
def test_pop(value):
    randomness = rand_fq()

    bytecode = Bytecode().pop().stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(),
        tx_table=set(tx.table_assignments(randomness)),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            RWDictionary(9)
            .call_context_read(1, CallContextFieldTag.TxId, tx.id)
            .stack_write(1, 1023, RLC(origin, randomness))
            .rws
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ORIGIN,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=0,
                stack_pointer=1024,
                gas_left=2,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=11,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=1,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )
