import pytest

from zkevm_specs.evm_circuit import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    Block,
    Bytecode,
    RWDictionary,
)
from zkevm_specs.util import Word

from common import rand_word

NOT_TESTING_DATA = [
    0,
    0x030201,
    0x090807,
    (1 << 256) - 1,
    (1 << 256) - 0x030201,
    rand_word(),
]


@pytest.mark.parametrize("a", NOT_TESTING_DATA)
def test_not(a: int):
    b = Word(a ^ ((1 << 256) - 1))
    a = Word(a)

    bytecode = Bytecode().not_(a).stop()
    bytecode_hash = Word(bytecode.hash())

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(),
        withdrawal_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(RWDictionary(9).stack_read(1, 1023, a).stack_write(1, 1023, b).rws),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.NOT,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=33,
                stack_pointer=1023,
                gas_left=3,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=11,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=34,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )
