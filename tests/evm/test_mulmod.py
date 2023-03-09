import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    Block,
    Bytecode,
    RWDictionary,
)
from zkevm_specs.util import rand_fq, Word

MAXU256 = (2**256) - 1


TESTING_DATA = [
    (1, 1, 2),
    (1, 1, 0),
    (0, 2, 3),
    (MAXU256, MAXU256, MAXU256),
    (MAXU256, MAXU256, 1),
    (MAXU256, 1, MAXU256),
    (MAXU256, 2, 2),
    (0, 0, 0),
]


@pytest.mark.parametrize("a, b, n", TESTING_DATA)
def test_mulmod(a: int, b: int, n: int):
    if n == 0:
        r = Word(0)
    else:
        r = Word((a * b) % n)

    a = Word(a)
    b = Word(b)
    n = Word(n)

    bytecode = Bytecode().mulmod(a, b, n).stop()
    bytecode_hash = Word(bytecode.hash())

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(
            RWDictionary(9)
            .stack_read(1, 1021, a)
            .stack_read(1, 1022, b)
            .stack_read(1, 1023, n)
            .stack_write(1, 1023, r)
            .rws
        ),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.MULMOD,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=99,
                stack_pointer=1021,
                gas_left=8,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=13,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=100,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )
