import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    RWTableTag,
    RW,
    Block,
    Bytecode,
)
from zkevm_specs.util import rand_bytes, rand_fp, RLC


TESTING_DATA = tuple(
    [
        (bytes([1])),
        (bytes([2, 1])),
        (bytes([i for i in range(31, 0, -1)])),
        (bytes([i for i in range(32, 0, -1)])),
    ]
    + [(rand_bytes(i + 1)) for i in range(32)]
)


@pytest.mark.parametrize("value_be_bytes", TESTING_DATA)
def test_push(value_be_bytes: bytes):
    randomness = rand_fp()

    value = RLC(bytes(reversed(value_be_bytes)), randomness)

    bytecode = Bytecode().push(value_be_bytes, n_bytes=len(value_be_bytes))
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            [
                (8, RW.Write, RWTableTag.Stack, 1, 1023, 0, value, 0, 0, 0),
            ]
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.PUSH,
                rw_counter=8,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=0,
                stack_pointer=1024,
                gas_left=3,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=1 + len(value_be_bytes),
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )
