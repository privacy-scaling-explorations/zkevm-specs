import pytest

from typing import Optional
from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    Opcode,
    verify_steps,
    Tables,
    Block,
    Bytecode,
    RWDictionary,
)
from zkevm_specs.util import rand_fq, rand_word, RLC


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
    randomness = rand_fq()

    b = RLC(a ^ ((1 << 256) - 1), randomness)
    a = RLC(a, randomness)

    bytecode = Bytecode().bitwise_not(a)
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(RWDictionary(9).stack_read(1, 1023, a).stack_write(1, 1023, b).rws),
    )

    verify_steps(
        randomness=randomness,
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
