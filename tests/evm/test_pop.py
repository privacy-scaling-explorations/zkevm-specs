import pytest

from zkevm_specs.evm_circuit import (
    Bytecode,
    ExecutionState,
    StepState,
    Tables,
    verify_steps,
    RWDictionary,
)
from zkevm_specs.util import Word, U256
from common import rand_word

TESTING_DATA = (
    rand_word(),
    rand_word(),
    rand_word(),
)


@pytest.mark.parametrize("y", TESTING_DATA)
def test_pop(y: U256):
    bytecode = Bytecode().pop().stop()
    bytecode_hash = Word(bytecode.hash())

    tables = Tables(
        block_table=set(),
        tx_table=set(),
        withdrawal_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(RWDictionary(1).stack_read(1, 1023, Word(y)).rws),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.POP,
                rw_counter=1,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=0,
                stack_pointer=1023,
                gas_left=2,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=2,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=1,
                stack_pointer=1024,
                gas_left=0,
            ),
        ],
    )
