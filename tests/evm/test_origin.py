import pytest

from zkevm_specs.evm_circuit import (
    Bytecode,
    CallContextFieldTag,
    ExecutionState,
    StepState,
    Tables,
    Transaction,
    verify_steps,
    RWDictionary,
)
from zkevm_specs.util import Word, U256
from common import rand_address

TESTING_DATA = (
    0x00,
    0x10,
    0x302010,
    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
    rand_address(),
)


@pytest.mark.parametrize("origin", TESTING_DATA)
def test_origin(origin: U256):
    tx = Transaction(caller_address=origin)

    bytecode = Bytecode().origin().stop()
    bytecode_hash = Word(bytecode.hash())

    tables = Tables(
        block_table=set(),
        tx_table=set(tx.table_assignments()),
        withdrawal_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(
            RWDictionary(9)
            .call_context_read(1, CallContextFieldTag.TxId, tx.id)
            .stack_write(1, 1023, Word(origin))
            .rws
        ),
    )

    verify_steps(
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
