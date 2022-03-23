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


TESTING_DATA = (
    (0x0),
    (0x060504),
)


@pytest.mark.parametrize("value", TESTING_DATA)
def test_iszero(value: int):
    randomness = rand_fq()

    result = 0x1 if value == 0x0 else 0x0

    value = RLC(value, randomness)
    result = RLC(result, randomness)

    bytecode = Bytecode().iszero(value).stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(RWDictionary(9).stack_read(1, 1023, value).stack_write(1, 1023, result).rws),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ISZERO,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=66,
                stack_pointer=1023,
                gas_left=3,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=11,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=67,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )
